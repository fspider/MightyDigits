from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.dashboard, name='adminDashboard'),
    path('users/', views.users, name='adminUsers'),
    path('uploadTemplate/', views.uploadTemplate, name='uploadTemplate'),
    path('rollForward', views.rollForward, name='rollForward'),

    path('reportDelete/<int:reportId>/', views.reportDelete, name='reportDelete'),
    path('reportRun/<int:reportId>/<int:runMacro>/', views.reportRun, name='reportRun'),
    path('reportRefresh/<int:reportId>/', views.reportRefresh, name='reportRefresh'),
    path('runRollForward/<int:reportId>/<str:newLastMonth>/', views.runRollForward, name='runRollForward'),

    path('addNewUser/', views.addNewUser, name='addNewUser'),
    path('userDelete/<int:userId>/', views.userDelete, name='userDelete'),
    path('userChangePermission/<int:userId>/<str:permission>', views.userChangePermission, name='userChangePermission'),
    path('userChangeActive/<int:userId>/<str:isActive>', views.userChangeActive, name='userChangeActive'),
    path('userChangePassword/<int:userId>/<str:password>', views.userChangePassword, name='userChangePassword'),
]
