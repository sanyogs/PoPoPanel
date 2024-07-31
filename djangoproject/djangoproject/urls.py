from django.contrib import admin
from django.urls import path, include
from dj import views   

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.HomePage, name='home'),  # Define URL pattern for the home page
    # path('<str:domain_name>/home/', views.HomePage, name='home'),
    path('', views.SignupPage, name='index'),
    path('login/', views.LoginPage, name='login'),
    path('add_customer/', views.add_customer, name='add_customer'),
    path('add_website/', views.add_website, name='add_website'),
    path('list_websites/', views.list_websites, name='list_websites'),
    path('update_website/<int:website_id>/', views.update_website, name='update_website'),
    path('read_credentials_from_file/', views.read_credentials_from_file, name='read_credentials_from_file'),
    path('delete_website/<int:website_id>/', views.delete_website, name='delete_website'),
    path('deleteuser/', views.delete_user, name='delete_user'),
    path('deleteuser/process/', views.delete_user_process, name='deleteuserprocess'),
    path('edit_user/', views.EditUser, name='edit_user'),
    path('get_user_details/<int:user_id>/', views.get_user_details, name='get_user_details'),
    path('update_user/', views.update_user, name='update_user'),
    path('rename_user/', views.rename_user, name='rename_user'),
    path('update_apache_config/', views.update_apache_config, name='update_apache_config'),
    path('change_password/', views.change_password, name='change_password'),
    path('update_hosts_file/', views.update_hosts_file, name='update_hosts_file'),
    path('update_php_version/', views.update_php_version, name='update_php_version'),
    # path('list_php_versions/', views.list_php_versions, name='list_php_versions'),
    # path('update_domain/', views.update_domain, name='update_domain'),
    # path('edit/', views.EditPage, name='edit_page'),
    # path('user_detail/', views.user_detail, name='user_detail'),
    # path('edit/<int:user_id>/', views.EditPage, name='edit_page'),
    # path('user_detail/<int:user_id>/', views.user_detail, name='user_detail'),
    # path('store_values/', views.store_values, name='store_values'),
    # path('add_virtual_host/',views.add_virtual_host, name='add_virtual_host'),
]
