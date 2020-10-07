import urllib

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.conf import settings
from .models import QBToken, QBReport, Status
from django.contrib.auth.decorators import login_required

from django.contrib.auth import (
    authenticate,
    get_user_model

)
User = get_user_model()

from sampleAppOAuth2 import getDiscoveryDocument
from sampleAppOAuth2.services import (
    getCompanyInfo,
    getBearerTokenFromRefreshToken,
    getUserProfile,
    getBearerToken,
    getBearerToken2,
    getSecretKey,
    validateJWTToken,
    revokeToken,
    getProfitAndLoss,
    getBalanceSheet,
    getAccountListDetail,
)
from sampleAppOAuth2.xlmanager import ExcelManager
from datetime import datetime, timedelta
import calendar
from adminApp.email import sendInfoEmail

@login_required
def index(request):
    return render(request, 'connectToQB.html')


@login_required
def connectToQuickbooks(request):
    url = getDiscoveryDocument.auth_endpoint
    params = {'scope': settings.ACCOUNTING_SCOPE, 'redirect_uri': settings.REDIRECT_URI,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)

@login_required
def connectToQuickbooks2(request, reportId):
    request.session['connectReportId'] = reportId
    url = getDiscoveryDocument.auth_endpoint
    params = {'scope': settings.ACCOUNTING_SCOPE, 'redirect_uri': settings.REDIRECT_URI2,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)

@login_required
def signInWithIntuit(request):
    url = getDiscoveryDocument.auth_endpoint
    scope = ' '.join(settings.OPENID_SCOPES)  # Scopes are required to be sent delimited by a space
    params = {'scope': scope, 'redirect_uri': settings.REDIRECT_URI,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)

@login_required
def getAppNow(request):
    url = getDiscoveryDocument.auth_endpoint
    scope = ' '.join(settings.GET_APP_SCOPES)  # Scopes are required to be sent delimited by a space
    params = {'scope': scope, 'redirect_uri': settings.REDIRECT_URI,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)


@login_required
def authCodeHandler(request):
    state = request.GET.get('state', None)
    error = request.GET.get('error', None)
    if error == 'access_denied':
        return redirect('')
    if state is None:
        return HttpResponseBadRequest()
    elif state != get_CSRF_token(request):  # validate against CSRF attacks
        return HttpResponse('unauthorized', status=401)

    auth_code = request.GET.get('code', None)
    if auth_code is None:
        return HttpResponseBadRequest()

    bearer = getBearerToken(auth_code)
    realmId = request.GET.get('realmId', None)
    updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)

    # Validate JWT tokens only for OpenID scope
    if bearer.idToken is not None:
        if not validateJWTToken(bearer.idToken):
            return HttpResponse('JWT Validation failed. Please try signing in again.')
        else:
            return redirect('connected')
    else:
        return redirect('connected')

@login_required
def authCodeHandler2(request):
    state = request.GET.get('state', None)
    error = request.GET.get('error', None)
    if error == 'access_denied':
        return redirect('adminDashboard')
    if state is None:
        return HttpResponseBadRequest()
    elif state != get_CSRF_token(request):  # validate against CSRF attacks
        return HttpResponse('unauthorized', status=401)

    auth_code = request.GET.get('code', None)
    if auth_code is None:
        return HttpResponseBadRequest()

    bearer = getBearerToken2(auth_code)

    # Validate JWT tokens only for OpenID scope
    if bearer.idToken is not None:
        if not validateJWTToken(bearer.idToken):
            return HttpResponse('JWT Validation failed. Please try signing in again.')

    realmId = request.GET.get('realmId', None)
    access_token = bearer.accessToken
    refresh_token = bearer.refreshToken
    
    reportId = request.session['connectReportId']
    current_user = QBReport.objects.filter(id=reportId)[0].user

    #  Update Token
    tokens = QBToken.objects.filter(user = current_user)
    if len(tokens) == 0:
        token = QBToken.objects.create(user=current_user, access_token = access_token, refresh_token=refresh_token, realmId=realmId)
    else:
        token = tokens[0]
        token.user=current_user
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.realmId = realmId
        token.save()
    return redirect('adminDashboard')

@login_required
def connected(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate Sign In With Intuit flow again')

    refresh_token = request.session.get('refreshToken', None)
    realmId = request.session['realmId']
    print('[SPIDER] access_token = ', access_token)
    print('[SPIDER] refresh_token = ', refresh_token)
    print('[SPIDER] realmId = ', realmId)

    if realmId is None:
        user_profile_response, status_code = getUserProfile(access_token)

        if status_code >= 400:
            # if call to User Profile Service doesn't succeed then get a new bearer token from refresh token
            # and try again
            bearer = getBearerTokenFromRefreshToken(refresh_token)
            user_profile_response, status_code = getUserProfile(bearer.accessToken)
            updateSession(request, bearer.accessToken, bearer.refreshToken, request.session.get('realmId', None),
                          name=user_profile_response.get('givenName', None))

            if status_code >= 400:
                return HttpResponseServerError()
        c = {
            'first_name': user_profile_response.get('givenName', ' '),
        }
    else:
        if request.session.get('name') is None:
            name = ''
        else:
            name = request.session.get('name')
        c = {
            'first_name': name,
        }

    updateToken(request)
    insertReport(request)

    current_user = request.user
    companyName = ''
    if 'companyName' in request.session: companyName = request.session['companyName']
    sendInfoEmail(companyName)

    # return render(request, 'connected.html', context=c)
    return render(request, 'submission.html')
    # return redirect('submission')
@login_required
def submission(request):
    startDate = ''
    endDate = ''
    lastMonth = ''
    companyName = ''
    accountingBasis = ''
    departmentsOfPL = []
    sameDepartmentsOfPL = False
    departmentsOfHC = []
    staffLocation = []
    if 'startDate' in request.session: startDate = request.session['startDate']
    if 'endDate' in request.session: endDate = request.session['endDate']
    if 'lastMonth' in request.session: lastMonth = request.session['lastMonth']
    if 'companyName' in request.session: companyName = request.session['companyName']
    if 'accountingBasis' in request.session: accountingBasis = request.session['accountingBasis']
    if 'departmentsOfPL' in request.session: departmentsOfPL = request.session['departmentsOfPL']
    if 'sameDepartmentsOfPL' in request.session: sameDepartmentsOfPL = request.session['sameDepartmentsOfPL']
    if 'departmentsOfHC' in request.session: departmentsOfHC = request.session['departmentsOfHC']
    if 'staffLocation' in request.session: staffLocation = request.session['staffLocation']

    context = {
        'companyName': companyName,
        'accountingBasis': accountingBasis,
        'startDate' : startDate,
        'endDate' : endDate,
        'lastMonth' : lastMonth,
        'departmentsOfPL' : departmentsOfPL,
        'departmentsOfHC' : departmentsOfHC,
        'staffLocation' : staffLocation,
    }

    return render(request, 'infoPage.html', context)

@login_required
def insertReport(request):
    startDate = ''
    endDate = ''
    lastMonth = ''
    companyName = ''
    accountingBasis = ''

    departmentsOfPL = []
    sameDepartmentsOfPL = False
    departmentsOfHC = []
    staffLocation = []

    if 'startDate' in request.session: startDate = request.session['startDate']
    if 'endDate' in request.session: endDate = request.session['endDate']
    if 'lastMonth' in request.session: lastMonth = request.session['lastMonth']
    if 'companyName' in request.session: companyName = request.session['companyName']
    if 'accountingBasis' in request.session: accountingBasis = request.session['accountingBasis']
    if 'departmentsOfPL' in request.session: departmentsOfPL = request.session['departmentsOfPL']
    if 'sameDepartmentsOfPL' in request.session: sameDepartmentsOfPL = request.session['sameDepartmentsOfPL']
    if 'departmentsOfHC' in request.session: departmentsOfHC = request.session['departmentsOfHC']
    if 'staffLocation' in request.session: staffLocation = request.session['staffLocation']

    current_user = request.user
    new_report = QBReport.objects.create(user = current_user, 
                                        companyName=companyName,
                                        accountingBasis=accountingBasis,
                                        status = Status.QUEUED,
                                        startDate = startDate,
                                        endDate = endDate,
                                        lastMonth = lastMonth,
                                        departmentsOfPL = departmentsOfPL,
                                        departmentsOfHC = departmentsOfHC,
                                        staffLocation = staffLocation,
                                        sameDepartmentsOfPL = sameDepartmentsOfPL,
                                        )

# Store token to database
@login_required
def updateToken(request, reportUserId = 0):
    access_token = request.session['accessToken']
    refresh_token = request.session['refreshToken']
    realmId = request.session['realmId']
    # name = request.session['name']

    if not request.user.is_authenticated:
        print('Not Logged In User')
        return False

    # FIND User to update token
    if reportUserId == 0:
        current_user = request.user
    else :
        current_user = User.objects.filter(id=reportUserId)[0]

    tokens = QBToken.objects.filter(user = current_user)
    if len(tokens) == 0:
        token = QBToken.objects.create(user=current_user, access_token = access_token, refresh_token=refresh_token, realmId=realmId)
    else:
        token = tokens[0]
        token.user=current_user
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.realmId = realmId
        token.save()
    return True

@login_required
def loadToken(request):
    if not request.user.is_authenticated:
        print('Not Logged In User')
        return False

    current_user = request.user
    tokens = QBToken.objects.filter(user = current_user)
    if len(tokens) == 0:
        return False
    else:
        token = tokens[0]
        updateSession(request, token.accessToken, token.refreshToken, token.realmId)

    print('Loaded Token')
    return True

@login_required
def disconnect(request):
    access_token = request.session.get('accessToken', None)
    refresh_token = request.session.get('refreshToken', None)

    revoke_response = ''
    if access_token is not None:
        revoke_response = revokeToken(access_token)
    elif refresh_token is not None:
        revoke_response = revokeToken(refresh_token)
    else:
        return HttpResponse('No accessToken or refreshToken found, Please connect again')

    request.session.flush()
    return HttpResponse(revoke_response)


@login_required
def refreshTokenCall(request):
    refresh_token = request.session.get('refreshToken', None)
    if refresh_token is None:
        return HttpResponse('Not authorized')
    bearer = getBearerTokenFromRefreshToken(refresh_token)
    realmId = request.session['realmId']
    updateToken(request)

    if isinstance(bearer, str):
        return HttpResponse(bearer)
    else:
        return HttpResponse('Access Token: ' + bearer.accessToken + ', Refresh Token: ' + bearer.refreshToken)
    
@login_required
def createReport(request, runMacro):
    print('[SPIDER] [sampleAppOAuth2] [CreateReport] Called')

    # Create Manager and Init Template FileName
    excelManager = ExcelManager()
    try:
        startDate = datetime.strptime(request.session['startDate'], '%B %Y')
        endDate = datetime.strptime(request.session['endDate'], '%B %Y')
        lastMonth = datetime.strptime(request.session['lastMonth'], '%B %Y')
        balanceStartDate = replaceStartMonth(replaceStartMonth(startDate) - timedelta(days=1)).strftime('%Y-%m-%d')
        startDate = replaceStartMonth(startDate).strftime('%Y-%m-%d')
        endDate = replaceEndMonth(endDate).strftime('%Y-%m-%d')
        lastMonth = replaceEndMonth(lastMonth).strftime('%Y-%m-%d')
        accountingBasis = request.session['accountingBasis']
    except Exception as error:
        print('[SPIDER] [XLManager] [createReport] Data Parse Exception : ' + repr(error)) 
        return HttpResponseServerError()

   # Save request to QBReport Model
    current_user = request.user
    if 'reportId' in request.session:
        reportId = request.session['reportId']
    else:
        return HttpResponseServerError()

    result = True
    filename = ''
    try:
        # Map Input Form Data
        res = excelManager.create(request.session, startDate, endDate, lastMonth)
        if res == False:
            return HttpResponseServerError()
        print('--->', 1)
        realmId = request.session['realmId']
        refresh_token = request.session['refreshToken']
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        print('--->', 2)

        # Call apiProfitAndLoss and save to Excel
        datas = get_apiProfitAndLoss(request, startDate, lastMonth, accountingBasis)
        print('-got apiProfitAndLoss Data')
        excelManager.writeProfitAndLoss(datas)
        # print('[ProfitAndLost]', datas)
        print('--->', 3)

        # Call apiBalanceSheet and save to Excel
        datas = get_apiBalanceSheet(request, balanceStartDate, lastMonth, accountingBasis)
        excelManager.writeBalanceSheet(datas)
        # print('[BalanceSheet]', datas)
        print('--->', 4)

        # Call apiAccountListDetail and save to Excep
        datas = get_apiAccountListDetail(request)
        ret = excelManager.writeAccountListDetail(datas)
        if ret == False: result = False
        # print('[AccountList]', datas)
        print('--->', 5)

        # Close and Get Saved FileName
        ret, filename = excelManager.close(runMacro=runMacro)
        if ret == False: result = False
        # Return Download Link
        print('[SPIDER][VIEWS] New xlsm created')

    except Exception as error:
        print('[SPIDER] [AUTH] [XLMANAGER] Exception : ' + repr(error))
        result = False
    if result == True:
        QBReport.objects.filter(id=reportId).update(status=Status.COMPLETED, fileName=filename)
    else:
        QBReport.objects.filter(id=reportId).update(status=Status.INCOMPLETED)

    updateToken(request, request.session['reportUserId'])
    print('[SPIDER][SampleAppOAuth2] Run Report Completed')
    return HttpResponse('<a href="/download/' + str(filename) + '"> Download </a>')

@login_required
def createRollForward(request):
    print('[SPIDER] [sampleAppOAuth2] [CreateRollForward] Called')
    # Create Manager and Init Template FileName
    excelManager = ExcelManager()
    try:
        startDate = datetime.strptime(request.session['startDate'], '%B %Y')
        endDate = datetime.strptime(request.session['endDate'], '%B %Y')
        lastMonth = datetime.strptime(request.session['lastMonth'], '%B %Y')
        balanceStartDate = replaceStartMonth(replaceStartMonth(startDate) - timedelta(days=1)).strftime('%Y-%m-%d')
        startDate = replaceStartMonth(startDate).strftime('%Y-%m-%d')
        endDate = replaceEndMonth(endDate).strftime('%Y-%m-%d')
        lastMonth = replaceEndMonth(lastMonth).strftime('%Y-%m-%d')
        accountingBasis = request.session['accountingBasis']
    except Exception as error:
        print('[SPIDER] [XLManager] [createReport] Data Parse Exception : ' + repr(error)) 
        return HttpResponseServerError()

   # Save request to QBReport Model
    current_user = request.user
    if 'reportId' in request.session:
        reportId = request.session['reportId']
    else:
        return HttpResponseServerError()

    QBReport.objects.filter(id=reportId).update(rollFileName="", rollLastMonth=request.session['lastMonth'])

    result = True
    filename = ''
    try:
        # Map Input Form Data
        res = excelManager.create(request.session, startDate, endDate, lastMonth, reportType='RollForward')
        if res == False:
            return HttpResponseServerError()
        print('--->', 1)
        realmId = request.session['realmId']
        refresh_token = request.session['refreshToken']
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        print('--->', 2)

        # Call apiProfitAndLoss and save to Excel
        datas = get_apiProfitAndLoss(request, startDate, lastMonth, accountingBasis)
        excelManager.writeProfitAndLoss(datas)
        print('[ProfitAndLost]', datas)
        print('--->', 3)

        # Call apiBalanceSheet and save to Excel
        datas = get_apiBalanceSheet(request, balanceStartDate, lastMonth, accountingBasis)
        excelManager.writeBalanceSheet(datas)
        # print('[BalanceSheet]', datas)
        print('--->', 4)

        # Call apiAccountListDetail and save to Excep
        datas = get_apiAccountListDetail(request)
        ret = excelManager.writeAccountListDetail(datas)
        if ret == False: result = False
        # print('[AccountList]', datas)
        print('--->', 5)

        # Close and Get Saved FileName
        ret, filename = excelManager.close(runMacro=False)
        if ret == False: result = False
        # Return Download Link
        print('[SPIDER][VIEWS] New ReportRollForward created')

    except Exception as error:
        print('[SPIDER] [AUTH] [XLMANAGER] Exception : ' + repr(error))
        result = False

    if result == True:
        QBReport.objects.filter(id=reportId).update(rollFileName=filename)
    else:
        QBReport.objects.filter(id=reportId).update(rollFileName="")

    updateToken(request, request.session['reportUserId'])
    print('[SPIDER][SampleAppOAuth2] Run RollForward Completed')
    return HttpResponse('<a href="/download/' + str(filename) + '"> Download </a>')

def replaceStartMonth(dt):
    return dt.replace(day=1)

def replaceEndMonth(dt):
    day = calendar.monthrange(dt.year, dt.month)[1]
    return dt.replace(day=day)

# Call apiProfitAndLoss perMonth and return Array
@login_required
def get_apiProfitAndLoss(request, startDate, endDate, accountingBasis):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return [False, HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')]

    realmId = request.session['realmId']
    if realmId is None:
        return [False, HttpResponse('No realm ID. QBO calls only work if the accounting scope was passed!')]

    refresh_token = request.session['refreshToken']
    ProfitAndLoss_info, status_code = getProfitAndLoss(access_token, realmId, startDate, endDate, accountingBasis)
    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        ProfitAndLoss_info, status_code = getProfitAndLoss(bearer.accessToken, realmId, startDate, endDate, accountingBasis)
        if status_code >= 400:
            return [False, HttpResponseServerError()]

    # company_name = company_info_response['CompanyInfo']['CompanyName']
    # address = company_info_response['CompanyInfo']['CompanyAddr']
    return [True, ProfitAndLoss_info]

@login_required
def apiProfitAndLoss(request):
    status, response = get_apiProfitAndLoss(request, '2020-01-01', '2020-06-30', 'Accrual')
    if status == True:
        response = HttpResponse(str(response))
    return response

# Call apiBalanceSheet perMonth and return Array
@login_required
def get_apiBalanceSheet(request, startDate, endDate, accountingBasis):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return [False, HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')]

    realmId = request.session['realmId']
    if realmId is None:
        return [False, HttpResponse('No realm ID. QBO calls only work if the accounting scope was passed!')]

    refresh_token = request.session['refreshToken']
    BalanceSheet_info, status_code = getBalanceSheet(access_token, realmId, startDate, endDate, accountingBasis)
    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        BalanceSheet_info, status_code = getBalanceSheet(bearer.accessToken, realmId, startDate, endDate, accountingBasis)
        if status_code >= 400:
            return [False, HttpResponseServerError()]

    return [True, BalanceSheet_info]

@login_required
def apiBalanceSheet(request):
    status, response = get_apiBalanceSheet(request, '2020-04-01', '2020-06-30', 'Accrual')
    if status == True:
        response = HttpResponse(str(response))
    return response

@login_required
def get_apiAccountListDetail(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return [False, HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')]

    realmId = request.session['realmId']
    if realmId is None:
        return [False, HttpResponse('No realm ID. QBO calls only work if the accounting scope was passed!')]

    refresh_token = request.session['refreshToken']
    AccountListDetail_info, status_code = getAccountListDetail(access_token, realmId)
    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        AccountListDetail_info, status_code = getAccountListDetail(bearer.accessToken, realmId)
        if status_code >= 400:
            return [False, HttpResponseServerError()]

    return [True, AccountListDetail_info]

@login_required
def apiAccountListDetail(request):
    status, response = get_apiAccountListDetail(request)
    if status == True:
        response = HttpResponse(str(response))
    return response


@login_required
def apiCall(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the accounting scope was passed!')

    refresh_token = request.session['refreshToken']
    company_info_response, status_code = getCompanyInfo(access_token, realmId)
    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        company_info_response, status_code = getCompanyInfo(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    company_name = company_info_response['CompanyInfo']['CompanyName']
    address = company_info_response['CompanyInfo']['CompanyAddr']
    return HttpResponse('Company Name: ' + company_name + ', Company Address: ' + address['Line1'] + ', ' + address[
        'City'] + ', ' + ' ' + address['PostalCode'])

@login_required
def get_CSRF_token(request):
    token = request.session.get('csrfToken', None)
    if token is None:
        token = getSecretKey()
        request.session['csrfToken'] = token
    return token

@login_required
def updateSession(request, access_token, refresh_token, realmId, name=None):
    request.session['accessToken'] = access_token
    request.session['refreshToken'] = refresh_token
    request.session['realmId'] = realmId
    request.session['name'] = name
