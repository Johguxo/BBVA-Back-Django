from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from django.urls import include,path

from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.index, name='index'),
    path('login-api/', views.AuthenticateUserAPI.as_view()),
    path('register-api/', views.RegisterUserAPI.as_view()),
]