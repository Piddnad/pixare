from django.db import models
from django.contrib.auth.models import User


class Like(models.Model):
    """
    喜欢的数据模型
    """

    photo_id = models.IntegerField()
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE,)
    photo_owner = models.ForeignKey(User, related_name='like_photo_owner', on_delete=models.CASCADE,)
    date_liked = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        ordering = ['id']

    # 计算照片的得分
    def calPhotoScore(self, isMarkLike):
        from pixare.models.photo import Photo
        try:
            photo = Photo.objects.get(id=self.photo_id, owner=self.photo_owner)
            photo.like_count += 1 if isMarkLike else -1
            photo.calculateScore()
            photo.save()
        except Photo.DoesNotExist:
            pass

            # 判断该喜欢记录是否已存在，避免重复喜欢

    def isExist(self):
        try:
            Like.objects.get(photo_id=self.photo_id, user=self.user, photo_owner=self.photo_owner)
        except Like.DoesNotExist:
            return False
        else:
            return True
