from django.db import models
from django.contrib.auth.models import User
from pixare.models.tag import Tag


class UserTag(models.Model):
    """
    用户标签的数据模型
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,)
    used_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        ordering = ['id']