from django.shortcuts import render, redirect
from django.shortcuts import HttpResponse
from .forms import RegistrationForm, SigninForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.conf import settings
import mimetypes
import os

# Create your views here.

# companyName
# startDate
# endDate
# lastMonth
# departmentsOfPL
# sameDepartmentsOfPL
# departmentsOfHC
# staffLocation

@login_required
def Home(request):
    if request.user.is_staff:
        return redirect('adminDashboard')
    context = {
        'username' : request.user.first_name.capitalize(),
    }
    return render(request, 'successPage.html', context)
    # return HttpResponse("<h1>This is our Home Page </h1>")

# Get Input - Company name
@login_required
def InputCompany(request):
    return render(request, 'inputCompany.html')

@login_required
def DoInputCompany(request):
    print('companyName', request.POST['companyName'])
    request.session['companyName'] = request.POST['companyName']
    return redirect('inputAccountingBasis')

# GET Input - Accounting Basis
@login_required
def InputAccountingBasis(request):
    return render(request, 'accountingBasis.html')
@login_required
def DoInputAccountingBasis(request):
    print('accountingBasis', request.POST['accountingBasis'])
    request.session['accountingBasis'] = request.POST['accountingBasis']
    return redirect('inputStartEndDate')

# Get Input - Start and End Date
@login_required
def InputStartEndDate(request):
    return render(request, 'startEndDate.html')
@login_required
def DoInputStartEndDate(request):
    print('startDate', request.POST['startDate'])
    print('endDate', request.POST['endDate'])
    request.session['startDate'] = request.POST['startDate']
    request.session['endDate'] = request.POST['endDate']
    return redirect('inputLastMonth')

# Get Input - lastMonth
@login_required
def InputLastMonth(request):
    return render(request, 'lastMonth.html')
@login_required
def DoInputLastMonth(request):
    if 'lastMonth' not in request.POST:
        return render(request, 'lastMonth.html')
    print('lastMonth', request.POST['lastMonth'])
    request.session['lastMonth'] = request.POST['lastMonth']
    return redirect('inputDepOfPL')

def remove_empty_string(strings):
    return [x for x in strings if x]
# Get Input - Departments of PL
@login_required
def InputDepOfPL(request):
    return render(request, 'departmentsOfPL.html')
@login_required
def DoInputDepOfPL(request):
    if 'departmentsOfPL ' not in request.POST:
        return render(request, 'departmentsOfPL.html', {'departments':["General & Administrative", "Sales & Marketing", "Tech"]})
    print(remove_empty_string(request.POST.getlist('departmentsOfPL ')))
    request.session['departmentsOfPL'] = remove_empty_string(request.POST.getlist('departmentsOfPL '))
    # return redirect('inputDepOfHC')
    request.session['sameDepartmentsOfPL'] = False
    request.session['departmentsOfHC'] = []
    return redirect('inputStaffLocation')

# Get Input - Departments of HC
@login_required
def InputDepOfHC(request):
    return render(request, 'departmentsOfHC.html')
@login_required
def DoInputDepOfHC(request):
    print(request.POST)
    if 'departmentsOfHeadcount ' not in request.POST:
        return render(request, 'departmentsOfHC.html')
    print('sameDepartmentsOfPL' in request.POST)
    print(remove_empty_string(request.POST.getlist('departmentsOfHeadcount ')))
    request.session['sameDepartmentsOfPL'] = ('sameDepartmentsOfPL' in request.POST)
    request.session['departmentsOfHC'] = remove_empty_string(request.POST.getlist('departmentsOfHeadcount '))
    return redirect('inputStaffLocation')

# Get Input - Staff Location
@login_required
def InputStaffLocation(request):
    return render(request, 'staffLocation.html')
@login_required
def DoInputStaffLocation(request):
    print(request.POST)
    if 'staffLocation' not in request.POST:
        return render(request, 'staffLocation.html')
    print(remove_empty_string(request.POST.getlist('staffLocation')))
    request.session['staffLocation'] = remove_empty_string(request.POST.getlist('staffLocation'))
    return redirect('sampleAppOAuth2')

# Get Input - Connect To QB
@login_required
def ConnectToQB(request):
    return render(request, 'connectToQB.html')
@login_required
def DoConnectToQB(request):
    # return render(request, 'connectToQB.html')
    return redirect('home')

def error(request, exception=None):
    return HttpResponseNotFound('<h1>Page not found</h1>')


@login_required
def download(request, path):
    file_path = os.path.join(settings.PUBLIC_DIR, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            mime_type, _ = mimetypes.guess_type(file_path)
            print('SPIDER----->', mime_type)
            response = HttpResponse(fh, content_type=mime_type)
            response['Content-Disposition'] = 'attachment; filename="' + os.path.basename(file_path) + '"'
            return response

    raise Http404

import json
def webhook(request):
    if request.method=="POST":
        print('Post Data', request.POST)
        data = request.POST
    if request.method=="GET":
        print('Get Data', request.GET)
        data = request.GET

    print (data)
    return HttpResponse(json.dumps(data))

