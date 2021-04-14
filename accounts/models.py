from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserData(models.Model):
    user = models.OneToOneField(User,on_delete=models.DO_NOTHING,related_name="userdata")
    about_me = models.TextField(default='', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_fb_user = models.BooleanField(default=False)
    is_google_user = models.BooleanField(default=False)
    last_active_date = models.DateTimeField(blank=True, null=True)
    n_status = models.CharField(max_length=1)

    def __str__(self):
        return self.user.username

class FacebookUser(models.Model):
    """ Model for facebook user """
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    id_facebook = models.CharField(max_length=250)

    def __str__(self):
        return self.user.get_full_name() + ' '+ self.id_facebook


class GoogleUser(models.Model):
    """ Model for google user """
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    id_google = models.CharField(max_length=250)

    def __str__(self):
        return self.user.get_full_name() + ' '+ self.id_google
