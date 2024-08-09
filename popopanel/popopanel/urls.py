"""
This file is part of POPOPANEL.

@package     POPOPANEL is part of WHAT PANEL – Web Hosting Application Terminal Panel.
@copyright   2023-2024 Version Next Technologies and MadPopo. All rights reserved.
@license     BSL; see LICENSE.txt
@link        https://www.version-next.com
"""
from django.contrib import admin
from django.urls import path, include
from popo import views   

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.HomePage, name='home'),  # Define URL pattern for the home page
    # path('<str:domain_name>/home/', views.HomePage, name='home'),
    path('', views.login_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add_customer/', views.add_customer, name='add_customer'),
    path('add_website/', views.add_website, name='add_website'),
    path('list_websites/', views.list_websites, name='list_websites'),
    path('update_hosts_file/', views.update_hosts_file, name='update_hosts_file'),
    path('update_website/<int:website_id>/', views.update_website, name='update_website'),
    path('delete_website/<int:website_id>/', views.delete_website, name='delete_website'),
    path('website/<int:id>/', views.website_info, name='website_info'),
    path('ftp-users/<int:website_id>/', views.ftp_users, name='ftp_users'),
    path('create_ftp_user/', views.create_ftp_user, name='create_ftp_user'),
    ]
