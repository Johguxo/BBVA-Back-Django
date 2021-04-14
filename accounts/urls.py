from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings

from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    url('', views.index, name='index'),
    url(r'^login-api/$', views.AuthenticateUserAPI.as_view()),
    url(r'^register-api/$', views.RegisterUserAPI.as_view()),
]