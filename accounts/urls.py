from . import views
from django.urls import path

urlpatterns = [
    path('signup', views.sign_up_view, name='sign_up'),
    path('verify-user', views.verify_user_view, name='verify_user'),
    path('login', views.login_view, name='login'),
    path('password-reset', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('u/all', views.get_all_users_view, name='get_all_users'),
    path('u/search', views.search_users_view, name='search_user'),
    path('u/<str:uid>', views.get_specific_user_view, name='get_user'),
]