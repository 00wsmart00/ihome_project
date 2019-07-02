from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^api/v1.0/areas/$', views.AreaView.as_view()),
    url(r'^api/v1.0/houses/$', views.HouseView.as_view()),
    url(r'^api/v1.0/user/houses/$', views.HouseView.as_view()),
    url(r'^api/v1.0/houses/(?P<house_id>\d+)/images/$', views.HouseImageView.as_view()),
    url(r'^api/v1.0/houses/(?P<house_id>\d+)/$', views.HouseDetailView.as_view()),
    url(r'^api/v1.0/houses/index/$', views.IndexHouseView.as_view()),
    url(r'^api/v1.0/houses/search/$', views.IndexHouseSearchView.as_view()),

]
