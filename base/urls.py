from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('install/', views.install, name='install'),
    path('installed/', views.installed_apps, name='installed'),
    path('installed/<str:app_id>/', views.app_detail, name='app_detail'),
    path('check-flatpak/', views.check_flatpak, name='check_flatpak'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
     path('accounts/signup/', views.signup, name='signup'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
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
    path('install/progress/<str:install_id>/', views.installation_progress_view, name='installation_progress'),
    path('get_installation_progress/<str:install_id>/', views.get_installation_progress, name='get_installation_progress'),
    path('launch_app/<str:app_id>/', views.launch_app, name='launch_app'),
]