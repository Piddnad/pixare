from django.db import models
from django.contrib.auth.models import User


class Follow(models.Model):
    """
    关注的数据模型
    """

    be_followed_user = models.ForeignKey(User, related_name='be_followed_user', on_delete=models.CASCADE,)
    follower = models.ForeignKey(User, related_name='follower', on_delete=models.CASCADE,)
    # date_followed = models.DateTimeField(datetime.datetime.now())
    date_followed = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        ordering = ['id']

    # 判断该关注记录是否已存在，避免重复关注
    def isExist(self):
        try:
            Follow.objects.get(be_followed_user=self.be_followed_user, follower=self.follower)
        except Follow.DoesNotExist:
            return False
        else:
            return True