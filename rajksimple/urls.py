from django.urls import path
from . import views

app_name = 'rajksimple'
urlpatterns = [
    path('', views.home, name='home'),
    path('account/<str:account_id>', views.accountview, name='account'),
    path('backref/<str:orderid>', views.backref, name='backref'),
    path('ipn', views.ipn, name='ipn'),
    path('confirm', views.confirm, name='confirm'),
]