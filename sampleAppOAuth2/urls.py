from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='sampleAppOAuth2'),
    path('connectToQuickbooks/', views.connectToQuickbooks, name='connectToQuickbooks'),
    path('connectToQuickbooks2/<int:reportId>/', views.connectToQuickbooks2, name='connectToQuickbooks2'),

    path('signInWithIntuit/', views.signInWithIntuit, name='signInWithIntuit'),
    path('getAppNow/', views.getAppNow, name='getAppNow'),

    re_path('authCodeHandler2/?', views.authCodeHandler2, name='authCodeHandler2'),
    re_path('authCodeHandler/?', views.authCodeHandler, name='authCodeHandler'),

    path('disconnect/', views.disconnect, name='disconnect'),
    path('connected/', views.connected, name='connected'),
    path('refreshTokenCall/', views.refreshTokenCall, name='refreshTokenCall'),
    path('apiCall/', views.apiCall, name='apiCall'),

    path('createReport/', views.createReport, name='createReport'),
    path('apiProfitAndLoss/', views.apiProfitAndLoss, name='apiProfitAndLoss'),
    path('apiBalanceSheet/', views.apiProfitAndLoss, name='apiBalanceSheet'),
    path('apiAccountListDetail/', views.apiAccountListDetail, name='apiAccountListDetail'),
    path('submission/', views.submission, name='submission'),
]
