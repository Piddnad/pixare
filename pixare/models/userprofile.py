from django.db import models
from django.contrib.auth.models import User

#拓展 Django Auth 自带的 User 模型
class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    name = models.CharField(max_length=14, unique=True) # 昵称
    city = models.CharField(max_length=32, blank=True)  # 所在地
    intro = models.CharField(max_length=512, blank=True) # 个性签名


    photo_count = models.IntegerField(default=0)
    avatar_loc = models.CharField(max_length=128, default='')
    avatar_square_loc = models.CharField(max_length=128, default='')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'User Profile'

    def __str__(self):
        return "{}".format(self.user.__str__())