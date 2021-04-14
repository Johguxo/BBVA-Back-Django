from django.contrib import admin
from accounts.models import UserData, FacebookUser, GoogleUser
# Register your models here.
admin.site.register(UserData)
admin.site.register(FacebookUser)
admin.site.register(GoogleUser)