from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from pixare.models.userprofile import UserProfile
from pixare.models.photo import Photo
from pixare.models.tag import Tag
from pixare.models.usertag import UserTag
from pixare.models.follow import Follow
from pixare.models.like import Like
from pixare.models.comment import Comment

admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline, ]


admin.site.register(User, UserProfileAdmin)
admin.site.register(Photo)
admin.site.register(Tag)
admin.site.register(UserTag)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Comment)

