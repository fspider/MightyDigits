from django.contrib import admin
from django.urls import path, include
from accounts.views import login_view, register_view, logout_view, forgot_view, reset_view, confirm_view
from django.conf.urls import handler404, handler500
from mightyapp.views import error


urlpatterns = [
    path('sampleAppOAuth2/', include('sampleAppOAuth2.urls')),
    path('adminapp/', include('adminApp.urls')),
    path('admin/', admin.site.urls),
    path('accounts/login/', login_view, name='login'),
    path('accounts/register/', register_view, name='register'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/forgot/', forgot_view, name='forgot'),
    path('accounts/reset/', reset_view, name='reset'),
    path('accounts/confirm/', confirm_view, name='confirm'),
    path('', include('mightyapp.urls')),
]

handler404 = error
handler500 = error