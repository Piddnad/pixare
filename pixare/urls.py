from django.conf.urls import url
from . import views

app_name = 'pixare'
urlpatterns = [
    url(r'^$', views.home.index),

    url(r'^explore/$', views.explore.hots),
    url(r'^explore/hots/$', views.explore.hots),
    url(r'^explore/recents/$', views.explore.recents),

    url(r'^search/$', views.search.default),

    url(r'^accounts/login/$', views.accounts.login, name='login'),
    url(r'^accounts/register/$', views.accounts.register, name='register'),
    url(r'^accounts/logout/$', views.accounts.logout, name='logout'),
    url(r'^accounts/(?P<pk>\d+)/profile/$', views.accounts.profile, name='profile'),
    url(r'^accounts/(?P<pk>\d+)/profile/update/$', views.accounts.profile_update, name='profile_update'),
    url(r'^accounts/(?P<pk>\d+)/pwd_change/$', views.accounts.pwd_change, name='pwd_change'),
    url(r'^accounts/editavatar/$', views.accounts.editavatar, name='editavatar'),

    url(r'^upload/$', views.photos.upload),
    url(r'^upload/complete/$', views.photos.upload_complete),
    url(r'^upload/complete/done/$', views.photos.upload_done),


    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/$', views.photos.photo),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/next/$', views.photos.next_photo),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/prev/$', views.photos.prev_photo),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/edit/$', views.photos.edit),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/delete/$', views.photos.ajax_deletePhoto),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/mark_like/$', views.photos.ajax_markLike),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/cancel_like/$', views.photos.ajax_cancelLike),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/add_comment/$', views.photos.ajax_addComment),
    url(r'^photos/delete_comment/$', views.photos.ajax_deleteComment),
    url(r'^photos/(?P<user_id>\d+)/(?P<photo_id>\d+)/delete_photo/$', views.photos.ajax_deletePhoto),

    url(r'^people/(?P<user_id>\d+)/$', views.people.home),
    url(r'^people/(?P<user_id>\d+)/tags/$', views.people.tags),
    url(r'^people/(?P<user_id>\d+)/comments/$', views.people.comments),
# url(r'^people/(?P<user_id>\d+)/comments/mine/$', views.people.comments_mine),
    url(r'^people/(?P<user_id>\d+)/profile/$', views.people.profile),
    url(r'^people/(?P<user_id>\d+)/likes/$', views.people.likes),
    url(r'^people/(?P<user_id>\d+)/follow/$', views.people.follow),
# url(r'^people/(?P<user_id>\d+)/follow/follow_me/$', views.people.follow_me),
    url(r'^people/(?P<user_id>\d+)/follow/mark_follow/$', views.people.ajax_markFollow),
    url(r'^people/(?P<user_id>\d+)/follow/cancel_follow/$', views.people.ajax_cancelFollow),


]