from django.urls import path
# from .views import viewNew, Home, Contact, Signup, AddUser, Signin, DoSignin, InputCompany, DoInputCompany
from .views import *

urlpatterns = [
    path('', Home, name = "home"),
    path('inputCompany', InputCompany, name = "inputCompany"),
    path('doInputCompany', DoInputCompany, name="doInputCompany"),
    path('inputAccountingBasis', InputAccountingBasis, name = "inputAccountingBasis"),
    path('doInputAccountingBasis', DoInputAccountingBasis, name="doInputAccountingBasis"),
    path('inputStartEndDate', InputStartEndDate, name = "inputStartEndDate"),
    path('doInputStartEndDate', DoInputStartEndDate, name = "doInputStartEndDate"),
    path('inputLastMonth', InputLastMonth, name = "inputLastMonth"),
    path('doInputLastMonth', DoInputLastMonth, name = "doInputLastMonth"),
    path('inputDepOfPL', InputDepOfPL, name = "inputDepOfPL"),
    path('doInputDepOfPL', DoInputDepOfPL, name = "doInputDepOfPL"),
    path('inputDepOfHC', InputDepOfHC, name = "inputDepOfHC"),
    path('doInputDepOfHC', DoInputDepOfHC, name = "doInputDepOfHC"),
    path('inputStaffLocation', InputStaffLocation, name = "inputStaffLocation"),
    path('doInputStaffLocation', DoInputStaffLocation, name = "doInputStaffLocation"),
    path('connectToQB', ConnectToQB, name = "connectToQB"),
    path('doConnectToQB', DoConnectToQB, name = "doConnectToQB"),

    path('download/<str:path>/', download, name = "download"),
    path('webhook', webhook, name="webhook"),
]
