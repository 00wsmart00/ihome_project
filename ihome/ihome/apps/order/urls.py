from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^api/v1.0/orders/$', views.OrderView.as_view()),
    url(r'^api/v1.0/orders/comment/$', views.CommentView.as_view()),
]
