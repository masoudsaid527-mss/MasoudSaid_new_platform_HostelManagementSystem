#Created by management/urls.py

from django.urls import path
from management import views

urlpatterns = [
    path('', views.Login, name='login'),
    path('home/', views.Home, name='home'),
    path('hostels/', views.HostelsList, name='hostels'),
    path('hostel/<int:hostel_id>/', views.HostelDetail, name='hostel_detail'),
    path('register/', views.Register, name='register'),
    path('about/', views.About, name='about'),
    path('contact/', views.Contact, name='contact'),
    path('post-room/', views.PostRoom, name='post_room'),
    path('owner-payments/', views.OwnerPayments, name='owner_payments'),
    path('owner-dashboard/', views.OwnerDashboard, name='owner_dashboard'),
    path('logout/', views.Logout, name='logout'),
]
