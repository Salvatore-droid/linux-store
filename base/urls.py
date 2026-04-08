from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('browse/', views.browse_apps, name='browse_apps'),
    path('app/<str:app_id>/', views.app_detail, name='app_detail'),
    path('about/', views.about, name='about'),
    
    # Installation
    path('install/', views.install, name='install'),
    path('install/progress/<str:install_id>/', views.installation_progress_api, name='installation_progress'),
    path('installed/', views.installed_apps, name='installed_apps'),
    path('uninstall/<str:app_id>/', views.uninstall_app, name='uninstall_app'),
    path('run/<str:app_id>/', views.run_app, name='run_app'),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
]
