from django.db import models
from django.contrib.auth.models import User
from .tag import Tag
from .usertag import UserTag
import datetime
import math
from MySite import settings
from qiniu import Auth, put_file, etag, put_data
import qiniu.config
from PIL import Image
from io import BytesIO

class Photo(models.Model):

    owner = models.ForeignKey(User, on_delete=models.CASCADE,) # 拥有者
    title = models.CharField(max_length=32, blank=True) # 标题
    caption = models.TextField(blank=True) # 说明
    tags = models.ManyToManyField(Tag) #标签

    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    date_posted = models.DateTimeField(auto_now_add=True)
    # shot_date = models.DateTimeField(null=True)
    # camera = models.CharField(max_length=128, blank=True)

    thumb_loc = models.CharField(max_length=128, default="")
    middle_loc = models.CharField(max_length=128, default="")
    original_loc = models.CharField(max_length=128, default="")

    middle_width = models.IntegerField(default=0)
    middle_height = models.IntegerField(default=0)

    original_width = models.IntegerField(default=0)
    original_height = models.IntegerField(default=0)

    score = models.FloatField(default=0)  # 根据用户的喜欢数和时间计算照片的得分

    def __unicode__(self):
        return str(self.id)

    class Meta:
        ordering = ['-date_posted']  # 按上传时间倒序，最近的排在前面



    # 只保存简要信息，等照片保存到数据库后，有了ID，然后以该ID为图片的文件名保存图片文件
    def save_photo_brief(self, user, photo_file):
        self.owner = user
        self.save()  # 保存到数据库，生成id
        self.calculateScore()  # 添加一张照片时，根据当前时间计算得分

        self.save_photo_file(photo_file)  # 生成照片文件的各种尺寸并保存到指定目录中
        self.save()  # 保存到数据库


    def calculateScore(self):
        begin_time = datetime.datetime(2018, 1, 1, 0, 0, 0)
        time_offset1 = datetime.datetime.now() - begin_time
        time_offset2 = datetime.datetime.now() - self.date_posted
        minutes1 = (time_offset1.days * 24 * 60) + time_offset1.seconds / 60
        minutes2 = (time_offset2.days * 24 * 60) + time_offset2.seconds / 60
        self.score = minutes1 / 120.0 + (0.2 * self.comment_count + 0.8 * self.like_count + 1) / (math.atan(minutes2 / 240.0 + 0.5) ** 2.2)


    def save_photo_file(self, photoFile):
        q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
        bucket_name = 'pixare'
        image = Image.open(photoFile)


        # 原始尺寸
        file_name = '%s_%s_%s_o.jpg' % (settings.QINIU_FILE_PREFIX, str(self.owner.id), str(self.id))
        self.original_width, self.original_height = image.size  # size是一个元组
        self.original_loc = file_name  # 图片相对于站点的存放位置
        token = q.upload_token(bucket_name, file_name, 3600)

        output = BytesIO()
        image.save(output, "png", quality=100)  # 原始图
        img_data = output.getvalue()
        output.close()
        ret, info = put_data(token, file_name, img_data)

        # 中尺寸
        image.thumbnail((600, 600), Image.ANTIALIAS)  # 中等尺寸图
        file_name = '%s_%s_%s_m.jpg' % (settings.QINIU_FILE_PREFIX, str(self.owner.id), str(self.id))
        self.middle_width, self.middle_height = image.size  # size是一个元组
        self.middle_loc = file_name  # 图片相对于站点的存放位置
        token = q.upload_token(bucket_name, file_name, 3600)

        output = BytesIO()
        image.save(output, "png", quality=100)
        img_data = output.getvalue()
        output.close()
        ret, info = put_data(token, file_name, img_data)


        # 缩略图
        image.thumbnail((240, 240), Image.ANTIALIAS)  # 缩略图
        file_name = '%s_%s_%s_t.jpg' % (settings.QINIU_FILE_PREFIX, str(self.owner.id), str(self.id))
        self.thumb_loc = file_name
        token = q.upload_token(bucket_name, file_name, 3600)

        output = BytesIO()
        image.save(output, "png", quality=100)
        img_data = output.getvalue()
        output.close()
        ret, info = put_data(token, file_name, img_data)


    # 保存图片的描述信息
    def save_photo_description(self, user, title, caption, tag_list):
        self.title = title
        self.caption = caption

        i = 0
        tag_list = set([t.strip() for t in tag_list if t.strip() != ''])
        for t in tag_list:
            i += 1  # 序号计数

            # 统计标签
            try:
                tt = Tag.objects.get(name=t)
            except Tag.DoesNotExist:
                tt = Tag(name=t)  # 该标签首次出现，创建
            else:
                tt.used_count += 1  # 该标签已存在，增加使用计数

            tt.save()
            self.tags.add(tt)  # 为照片添加标签，tags为多对多关系

            # 为该用户添加使用的标签
            try:
                usertag = UserTag.objects.get(user=self.owner, tag=tt)
            except UserTag.DoesNotExist:
                usertag = UserTag(user=self.owner, tag=tt)  # 该用户从未使用过该标签，创建
            else:
                usertag.used_count += 1  # 该用户已有该标签，增加使用计数
            usertag.save()

        self.save()  # 保存照片信息


    def update_photo_info(self, title, caption, tag_list):
        self.title = title
        self.caption = caption
        tags = self.tags.all()
        # 将该照片的关联标签删除，并更新标签计数，如果为0，就删除标签
        for t in tags:
            self.tags.remove(t)
            self.save()  # 保存照片信息
            t.used_count -= 1

            usertag = UserTag.objects.get(user=self.owner, tag=t)
            usertag.used_count -= 1
            if usertag.used_count <= 0:
                usertag.delete()
            else:
                t.save()

            if t.used_count <= 0:
                t.delete()
            else:
                usertag.save()
        i = 0
        for t in tag_list:
            t = t.strip()  # 去掉两端的空格
            if t == '' or tag_list.index(t) != i:
                continue  # 空字符串不是标签，存在重复，去掉重复的

            i += 1  # 序号计数

            # 统计标签
            try:
                tt = Tag.objects.get(name=t)
            except Tag.DoesNotExist:
                tt = Tag(name=t)  # 该标签首次出现，创建
            else:
                tt.used_count += 1  # 该标签已存在，增加使用计数

            tt.save()
            self.tags.add(tt)  # 为照片添加标签

            # 为该用户添加使用的标签
            try:
                usertag = UserTag.objects.get(user=self.owner, tag=tt)
            except UserTag.DoesNotExist:
                usertag = UserTag(user=self.owner, tag=tt)  # 该用户从未使用过该标签，创建
            else:
                usertag.used_count += 1  # 该用户已有该标签，增加使用计数

            usertag.save()

        self.save()  # 保存照片信息


    # 删除照片前，对照片关联数据的清理
    def clearPhoto(self):
        self.owner.profile.photo_count -= 1
        self.update_photo_info("", "", [])  # 先清空该照片的标签

        self.owner.save()

        # 对评论标注照片已被删除
        from pixare.models.comment import Comment
        comments = Comment.objects.filter(photo_id=self.id, photo_owner=self.owner)
        for c in comments:
            c.photo_deleted = True
            c.save()

