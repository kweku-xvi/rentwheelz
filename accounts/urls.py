from . import views
from django.urls import path

urlpatterns = [
    path('signup', views.sign_up_view, name='sign_up'),
    path('verify-user', views.verify_user_view, name='verify_user'),
]