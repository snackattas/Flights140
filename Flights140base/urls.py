from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()
from . import views

app_name = 'flights140base'

urlpatterns = [
    url(r'^$', views.login, name='login'),
    url(r'^member/$', views.main, name='main'),
    url(r'^member/edit_user/$', views.edit_user, name='edit_user'),
    url(r'^member/delete/$', views.delete_user, name='delete_user'),
    url(r'^member/create_alert/$', views.create_alert, name='create_alert'),
    url(r'^member/delete_alert/$', views.delete_alert, name='delete_alert'),
    url(r'^member/contact_form/$', views.contact_form, name='contact_form'),
    url(r'^member/.*$', views.redirect_to_main, name='redirect_to_main'),
    url(r'^.*$', views.redirect_to_main, name='redirect_to_main')
]
