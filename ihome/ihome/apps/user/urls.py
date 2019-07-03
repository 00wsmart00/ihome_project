from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    # 图形验证码
    url(r'^api/v1.0/imagecode$', views.ImageCodeView.as_view()),
    # 短信验证码
    url(r'^api/v1.0/smscode/$', views.SmsCodeView.as_view()),
    # 用户注册
    url(r'^api/v1.0/user/register/$', views.RegisterView.as_view()),
    url(r'^api/v1.0/login/$', views.LoginView.as_view()),
    url(r'^api/v1.0/session/$', views.SessionView.as_view()),
    url(r'^api/v1.0/logout/$', views.LogoutView.as_view()),
    url(r'^api/v1.0/user/profile/$', views.UserProfile.as_view()),
    url(r'^api/v1.0/user/avatar/$', views.ImageUpload.as_view()),
    url(r'^api/v1.0/user/auth/$', views.RealNameAuth.as_view()),
]
