from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, JsonResponse

from sampleAppOAuth2.models import QBReport, Status, QBToken
from sampleAppOAuth2.views import createReport, createRollForward
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import FileSystemStorage
from .models import AdminSetting

from django.contrib.auth import (
    authenticate,
    get_user_model,
)
User = get_user_model()
from django.conf import settings
from .forms import UserRegisterForm
from .email import sendInviteEmail, sendInfoEmail

@staff_member_required
def dashboard(request):
    # sendInfoEmail('testCompany')
    page = request.GET.get('page', 1)
    companyName = request.GET.get('companyName', '')
    if companyName == '':
        report_list = QBReport.objects.all().order_by('-created_at')
    else:
        report_list = QBReport.objects.filter(companyName__contains=companyName).order_by('-created_at')
    paginator = Paginator(report_list, 10)

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    stPageNo = max(reports.number - 2, 1)
    edPageNo = min(stPageNo + 4, paginator.num_pages)
    return render(request, 'admin_dashboard.html', {'active': 'dashboard', 'reports':reports, 'pagerange': range(stPageNo, edPageNo+1)})

@staff_member_required
def users(request):
    page = request.GET.get('page', 1)
    username = request.GET.get('username', '')
    if username == '':
        report_list = User.objects.all().order_by('-date_joined')
    else:
        report_list = User.objects.filter(first_name__contains=username).order_by('-date_joined')
    paginator = Paginator(report_list, 10)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    stPageNo = max(users.number - 2, 1)
    edPageNo = min(stPageNo + 4, paginator.num_pages)

    # form = UserRegisterForm(request.POST or None)
    # if form.is_valid():
    #     user = form.save(commit=False)
    #     password = settings.DEFAULT_PASSWORD
    #     user.set_password(password)
    #     user.is_staff = form.cleaned_data.get('isAdmin')
    #     user.save()
        # return redirect('/')

    return render(request, 'admin_users.html', {'active': 'users', 'users':users, 'pagerange': range(stPageNo, edPageNo+1)})

@staff_member_required
def reportDelete(request, reportId):
    try:
        QBReport.objects.get(id=reportId).delete()
    except QBReport.DoesNotExist:
        print('[SPIDER] [ADMIN] [REPORT] [DELETE] Not Exists')
        pass
    return redirect('adminDashboard')

@staff_member_required
def reportRun(request, reportId, runMacro):

    reports = QBReport.objects.filter(id=reportId)
    if len(reports) == 0:
        return HttpResponseServerError()
    report = reports[0]

    tokens = QBToken.objects.filter(user=report.user)
    if len(tokens) == 0:
        return HttpResponseServerError()
    token = tokens[0]

    if report.status != Status.QUEUED:
        return HttpResponseBadRequest()

    request.session['reportId'] = reportId
    request.session['reportUserId'] = report.user.id
    request.session['startDate'] = report.startDate
    request.session['endDate'] = report.endDate
    request.session['lastMonth'] = report.lastMonth
    request.session['companyName'] = report.companyName
    request.session['accountingBasis'] = report.accountingBasis.split(' ')[0]
    request.session['departmentsOfPL'] = report.departmentsOfPL
    request.session['sameDepartmentsOfPL'] = report.sameDepartmentsOfPL
    request.session['departmentsOfHC'] = report.departmentsOfHC
    request.session['staffLocation'] = report.staffLocation

    request.session['accessToken'] = token.access_token
    request.session['refreshToken'] = token.refresh_token
    request.session['realmId'] = token.realmId
    createReport(request, runMacro is 1)
    return redirect('adminDashboard')

@staff_member_required
def reportRefresh(request, reportId):
    try:
        QBReport.objects.filter(id=reportId).update(status=Status.QUEUED, fileName="")
    except QBReport.DoesNotExist:
        print('[SPIDER] [ADMIN] [REPORT] [REFRESH] ERROR!')
        pass
    return redirect('adminDashboard')

def create_user(username, email, password, isNewAdmin):
    try:
        user1 = User.objects.create_user(username=username, email=email, password=password)
        if isNewAdmin == 'true':
            user1.is_staff = True
        user1.save()
        # user = authenticate(username=username, password=password)
    except Exception as error:
        print('[SPIDER] [ADMIN] [CREATE USER] Exception : ' + repr(error))


@staff_member_required
def addNewUser(request):
    # print(request.POST)
    # username = request.POST.get('username')
    # email = request.POST.get('email')
    # isNewAdmin = request.POST.get('isNewAdmin')
    print(request.GET)
    username = request.GET.get('username')
    email = request.GET.get('email')
    isNewAdmin = request.GET.get('isNewAdmin')

    # username_qs = User.objects.filter(username=username)
    # if username_qs.exists():
    #     return JsonResponse({"error": "username already exists"}, status=400)

    email_qs = User.objects.filter(email=email)
    if email_qs.exists():
        return JsonResponse({"error": "email already exists"}, status=400)

    # create_user(username, email, password, isNewAdmin)
    isAdmin = (isNewAdmin == 'true')
    sendInviteEmail(email, username, isAdmin)
    # return redirect('adminDashboard')
    return JsonResponse({"result": 123}, status=200)

@staff_member_required
def userDelete(request, userId):
    try:
        User.objects.get(id=userId).delete()
    except QBReport.DoesNotExist:
        print('[SPIDER] [ADMIN] [USER] [DELETE] Not Exists')
        pass
    return redirect('adminUsers')

@staff_member_required
def userChangePermission(request, userId, permission):
    print('[permission]', permission)
    isAdmin = (permission == 'true')
    try:
        user = User.objects.get(id=userId)
        user.is_staff = isAdmin
        user.save()
    except Exception as error:
        print('[SPIDER] [AdminAPP] Change Permission Exception : ' + repr(error)) 
        pass
    return redirect('adminUsers')

@staff_member_required
def userChangeActive(request, userId, isActive):
    print('[isActive]', isActive)
    isActive = (isActive == 'true')
    try:
        user = User.objects.get(id=userId)
        user.is_active = isActive
        user.save()
    except Exception as error:
        print('[SPIDER] [AdminAPP] Change Active Status Exception : ' + repr(error)) 
        pass
    return redirect('adminUsers')

@staff_member_required
def userChangePassword(request, userId, password):
    print('[password]', password)
    try:
        user = User.objects.get(id=userId)
        user.set_password(password)
        user.save()
    except Exception as error:
        print('[SPIDER] [AdminAPP] Change Password Exception : ' + repr(error)) 
        pass
    return redirect('adminUsers')

@staff_member_required
def uploadTemplate(request):
    if request.method == 'POST' and 'myfile' in request.FILES:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        strlist = filename.split('/')
        uploaded_file_name = strlist[-1]
        print('----------->', uploaded_file_name)
        try:
            item = AdminSetting.objects.get(key='TemplateFileName')
            item.value = uploaded_file_name
            item.save()
        except AdminSetting.DoesNotExist:
            AdminSetting.objects.create(key='TemplateFileName', value=uploaded_file_name)

    try:
        item = AdminSetting.objects.get(key='TemplateFileName')
        uploaded_time = item.updated_at
    except AdminSetting.DoesNotExist:
        uploaded_time = ""

    uploaded_file_name = AdminSetting.getField('TemplateFileName')
    return render(request, 'admin_uploadTemplate.html', {
        'active': 'uploadTemplate',
        'uploaded_file_url': uploaded_file_name,
        'uploaded_time': uploaded_time,
    })
    # return render(request, 'admin_uploadTemplate.html', {'active': 'uploadTemplate'})


@staff_member_required
def rollForward(request):
    page = request.GET.get('page', 1)
    companyName = request.GET.get('companyName', '')
    if companyName == '':
        report_list = QBReport.objects.all().order_by('-created_at')
    else:
        report_list = QBReport.objects.filter(companyName__contains=companyName).order_by('-created_at')
    paginator = Paginator(report_list, 10)

    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    stPageNo = max(reports.number - 2, 1)
    edPageNo = min(stPageNo + 4, paginator.num_pages)
    return render(request, 'admin_rollForward.html', {'active': 'rollForward', 'reports':reports, 'pagerange': range(stPageNo, edPageNo+1)})

@staff_member_required
def runRollForward(request, reportId, newLastMonth):
    print('reportId={0} newLastMonth={1}', reportId, newLastMonth)

    reports = QBReport.objects.filter(id=reportId)
    if len(reports) == 0:
        return HttpResponseServerError()
    report = reports[0]

    tokens = QBToken.objects.filter(user=report.user)
    if len(tokens) == 0:
        return HttpResponseServerError()
    token = tokens[0]

    request.session['reportId'] = reportId
    request.session['reportUserId'] = report.user.id
    request.session['startDate'] = report.startDate
    request.session['endDate'] = report.endDate
    # request.session['lastMonth'] = report.lastMonth
    request.session['lastMonth'] = newLastMonth
    request.session['companyName'] = report.companyName
    request.session['accountingBasis'] = report.accountingBasis.split(' ')[0]
    request.session['departmentsOfPL'] = report.departmentsOfPL
    request.session['sameDepartmentsOfPL'] = report.sameDepartmentsOfPL
    request.session['departmentsOfHC'] = report.departmentsOfHC
    request.session['staffLocation'] = report.staffLocation

    request.session['accessToken'] = token.access_token
    request.session['refreshToken'] = token.refresh_token
    request.session['realmId'] = token.realmId
    createRollForward(request)

    return redirect('rollForward')