from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse

from django.contrib.auth.models import User
from pixare.models.photo import Photo
from pixare.models.comment import Comment
from pixare.models.like import Like
from django.contrib import auth
from pixare.forms import RegistrationForm, LoginForm, ProfileForm, PwdChangeForm
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from pixare.views import error_404
import string, datetime, json
import sys
from django.template.loader import get_template
from django.template.context import Context
from django.views.decorators.csrf import csrf_exempt
from MySite import settings


UPLOAD_PHOTOS_SESSION_KEY = 'upload_photos'  # 用于存放上传的照片片在数据库中的id元组
UPLOAD_STEP1_SESSION_KEY = 'upload_step1'  # 用于判断上传时，是否通过了第一步
UPLOAD_STEP2_SESSION_KEY = 'upload_step2'  # 用于判断上传时，是否通过了第二步

@login_required()
def upload(request):
    if request.method == 'POST':
        photo_id_list = []
        for i in request.FILES:
            photo = Photo()

            photo.save_photo_brief(request.user, request.FILES[i])
            photo_id_list.append(photo.id)

#todo
            # request.user.photo_count += len(photo_id_list)  # 增加用户照片数
            # request.user.save()

        request.session[UPLOAD_PHOTOS_SESSION_KEY] = tuple(photo_id_list)  # 转换成元组
        request.session[UPLOAD_STEP1_SESSION_KEY] = True  # 通过第一步
        return HttpResponseRedirect('complete/')  # 跳转到照片信息编辑页
    else:
        return render(request, 'photos/upload.html', {})


@login_required()
def upload_complete(request):
    if request.method == 'POST':
        photo_id_list = request.session[UPLOAD_PHOTOS_SESSION_KEY]
        for p_id in photo_id_list:
            try:
                photo = Photo.objects.get(id=p_id)
            except:
                pass
            else:
                title = (request.POST.get(str(p_id) + '_title', '')).strip()  # 去掉两端的空格
                caption = (request.POST.get(str(p_id) + '_caption', '')).strip()  # 去掉两端的空格
                tags = (request.POST.get(str(p_id) + '_tags', '')).strip()
                tags = tags.replace(u'，', ',')  # 把中文的逗号'，'替换成英文的','
                tag_list = tags.split(',')
                photo.save_photo_description(request.user, title, caption, tag_list)

        request.session[UPLOAD_STEP1_SESSION_KEY] = False
        request.session[UPLOAD_STEP2_SESSION_KEY] = True  # 通过第二步
        return HttpResponseRedirect('done/')  # 跳转到照片上传完成页
    else:
        photo_id_list = request.session[UPLOAD_PHOTOS_SESSION_KEY]
        photo_list = []
        for p_id in photo_id_list:
            photo = Photo.objects.get(id=p_id)
            photo.input_title_name = str(photo.id) + '_title'
            photo.input_caption_name = str(photo.id) + '_caption'
            photo.input_tags_name = str(photo.id) + '_tags'
            photo_list.append(photo)

        return render(request, 'photos/upload_complete.html', {'photo_list': photo_list})


@login_required()
def upload_done(request):

    if UPLOAD_STEP2_SESSION_KEY in request.session and request.session[UPLOAD_STEP2_SESSION_KEY]:  # 通过第二步
        # request.session[UPLOAD_STEP1_SESSION_KEY] = False
        request.session[UPLOAD_STEP2_SESSION_KEY] = False
        return render(request, 'photos/upload_done.html', {})
    else:
        return error_404(request)


def photo(request, user_id, photo_id):
    try:
        people = User.objects.get(id=user_id)
        photo = Photo.objects.get(owner=people, id=photo_id)

    except(User.DoesNotExist, Photo.DoesNotExist):
        return error_404(request)

    try:
        comment_list = Comment.objects.filter(photo_id=photo.id, photo_owner=people,
                                              deleted_by_photo_owner=False).order_by('date_posted')
    except:
        comment_list = []

    is_myPage = False  # 用来标记该页面是不是登录用户的个人页面
    if request.user.is_authenticated:
        if str(request.user.id) == user_id:  # 注意user_id是unicode字符串，比较时要先转成字符串
            is_myPage = True  # 自己的页面可以删除评论，删除照片
        else:
            is_myPage = False

            try:
                Like.objects.get(photo_id=photo.id, photo_owner=people, user=request.user)
            except Like.DoesNotExist:
                photo.i_like = False
            else:
                photo.i_like = True


    return render(request, 'photos/photo.html', {'people': people, 'photo': photo, 'is_myPage': is_myPage, 'comment_list': comment_list})

# 下一张照片
def next_photo(request, user_id, photo_id):
    try:
        people = User.objects.get(id=user_id)
        photo = Photo.objects.get(owner=people, id=photo_id)
        try:
            # id__gt表示id大于
            next_photo = Photo.objects.filter(id__gt=photo_id, owner=photo.owner).order_by('id')[0]
            next_photo_id = next_photo.id
        except:  # 不存在上一张照片，就用当前这张
            next_photo_id = photo_id
    except (User.DoesNotExist, Photo.DoesNotExist):
        return error_404(request)

    # 跳转到该照片的页面
    return HttpResponseRedirect('/photos/' + str(user_id) + '/' + str(next_photo_id) + '/')


# 上一张照片
def prev_photo(request, user_id, photo_id):
    try:
        people = User.objects.get(id=user_id)
        photo = Photo.objects.get(owner=people, id=photo_id)
        try:
            # id__lt表示id小于
            prev_photo = Photo.objects.filter(id__lt=photo_id, owner=photo.owner).order_by('-id')[0]
            prev_photo_id = prev_photo.id
        except:  # 不存在上一张照片，就用当前这张
            prev_photo_id = photo_id
    except (User.DoesNotExist, Photo.DoesNotExist):
        return error_404(request)

    return HttpResponseRedirect('/photos/' + str(user_id) + '/' + str(prev_photo_id) + '/')  # 跳转到该照片的页面

# 编辑照片的信息
def edit(request, user_id, photo_id):
    # 只有登录用户，且是自己的照片，才可以操作，
    if not request.user.is_authenticated or str(request.user.id) != user_id:
        return error_404(request)

    try:
        photo = Photo.objects.get(owner=request.user, id=photo_id)
    except:
        return error_404(request)

    if request.method == 'POST':
        if request.POST.get('update') == u'更新':
            title = (request.POST.get('title', '')).strip()  # 去掉两端的空格
            caption = (request.POST.get('caption', '')).strip()  # 去掉两端的空格
            tags = request.POST.get('tags', '').strip()  # 去掉两端的空格
            tags = tags.replace(u'，', ',')  # 把中文的逗号'，'替换成英文的','
            tag_list = tags.split(',')
            photo.update_photo_info(title, caption, tag_list)
        elif request.POST.get('cancel') == u'撤销':
            pass

        return HttpResponseRedirect('/photos/' + str(user_id) + '/' + str(photo_id) + '/')  # 跳转到该照片的页面

    else:
        tag_list = []
        for tag in photo.tags.all():
            tag_list.append(tag.name)
        photo.tagStr = u'，'.join(tag_list)

        return render(request, 'photos/edit.html', {'photo': photo})


@csrf_exempt
def ajax_deletePhoto(request, user_id, photo_id):
    if not request.is_ajax() or (request.method != 'POST'):
        return HttpResponse(json.dumps({"status": 'error0'}))

    # 只有登录用户，且是自己的照片，才可以操作，
    if not request.user.is_authenticated or str(request.user.id) != user_id:
        return HttpResponse(json.dumps({"status": 'error1'}))

    try:
        photo = Photo.objects.get(id=photo_id)
        photo.clearPhoto()
        photo.delete()
        # photo.deletePhotoFiles()  # 删除照片文件
    except:
        return HttpResponse(json.dumps({"status": str(sys.exc_info()[0]) + str(sys.exc_info()[1])}))

    return HttpResponse(json.dumps({"status": 'success'}))

@csrf_exempt
def ajax_markLike(request, user_id, photo_id):
    if not request.is_ajax() or (request.method != 'POST'):
        return HttpResponse(json.dumps({"status": 'error0'}))

    # 只有登录用户，且不是自己的照片，才可以操作，
    if not request.user.is_authenticated or str(request.user.id) == user_id:
        return HttpResponse(json.dumps({"status": 'error1'}))

    try:
        people = User.objects.get(id=user_id)
        like = Like(photo_id=photo_id, photo_owner=people, user=request.user)
        if like.isExist():  # 判断该喜欢记录是否已存在，避免重复喜欢
            return HttpResponse(json.dumps({"status": 'success'}))
        like.calPhotoScore(True)  # 添加喜欢后重新计算照片得分
        like.save()

    except:
        return HttpResponse(json.dumps({"status": str(sys.exc_info()[0]) + str(sys.exc_info()[1])}))

    return HttpResponse(json.dumps({"status": 'success'}))


@csrf_exempt
def ajax_cancelLike(request, user_id, photo_id):
    if not request.is_ajax() or (request.method != 'POST'):
        return HttpResponse(json.dumps({"status": 'error0'}))

    # 只有登录用户，且不是自己的照片，才可以操作，
    if not request.user.is_authenticated or str(request.user.id) == user_id:
        return HttpResponse(json.dumps({"status": 'error1'}))

    try:
        people = User.objects.get(id=user_id)  # people是照片拥有者

        like = Like.objects.get(photo_id=photo_id, photo_owner=people, user=request.user)
        like.calPhotoScore(False)  # 取消喜欢后重新计算照片得分
        like.delete()
    except:
        return HttpResponse(json.dumps({"status": str(sys.exc_info()[0]) + str(sys.exc_info()[1])}))

    return HttpResponse(json.dumps({"status": 'success'}))


@csrf_exempt
def ajax_addComment(request, user_id, photo_id):
    if not request.is_ajax() or (request.method != 'POST'):
        return HttpResponse(json.dumps({"status": 'error0'}))

    # 只有登录用户，才可以操作，
    if not request.user.is_authenticated:
        return HttpResponse(json.dumps({"status": 'error1'}))

    try:
        people = User.objects.get(id=user_id)  # people是照片拥有者
        content = (request.POST.get('content')).strip()
        if content != '':
            comment = Comment(photo_id=photo_id, photo_owner=people, author=request.user, content=content)
            comment.add_commment_count()
            comment.save()  # 保存评论


            t = get_template('photos/comment_item.html')
            html = t.render({'comment': comment, 'people':request.user, 'QINIU_IMG_URL':settings.QINIU_IMG_URL})
        else:
            html = ''
        return HttpResponse(json.dumps({'status': 'success', 'html': html}))
    except:
        return HttpResponse(json.dumps({'status': str(sys.exc_info()[0]) + str(sys.exc_info()[1])}))


@csrf_exempt
def ajax_deleteComment(request):
    if not request.is_ajax() or (request.method != 'POST'):
        return HttpResponse(json.dumps({"status": 'error0'}))

    # 只有登录用户，才可以操作，
    if not request.user.is_authenticated:
        return HttpResponse(json.dumps({"status": 'no authority'}))

    user_id = request.POST.get('user_id')
    # photo_id = request.POST.get('photo_id')
    author_id = request.POST.get('author_id')
    comment_id = request.POST.get('comment_id')  # 这里的comment_id是照片所在站点的评论的id
    if author_id != str(request.user.id) and str(request.user.id) != user_id:  # 没有删除权限
        return HttpResponse(json.dumps({"status": 'xx' + user_id + 'no authority to delete this comment'}))

    try:
        # people = User.objects.get(id=user_id)  # people是照片拥有者
        # author = User.objects.get(id=author_id)

        if str(request.user.id) == author_id:  # 如果执行删除操作的是评论者，则删除评论
            c = Comment.objects.get(id=comment_id)
            c.delete()  # 删除评论
        else:  # 如果执行删除操作的是照片所有者，则不删除评论，但标记评论被照片所有者删除，即评论在照片评论列表不可见
            c = Comment.objects.get(id=comment_id)
            # if author.city != people.city:  # 评论用户和照片所有者不在同一个站点，存在评论副本
            #     rc = Comment.objects.get(id=c.master_id)
            #     rc.deleted_by_photo_owner = True
            #     rc.save()
            c.deleted_by_photo_owner = True
            c.save()  # 删除评论
    except Comment.DoesNotExist:  # 评论不存在，或已删除，返回成功
        return HttpResponse(json.dumps({'status': 'success'}))
    except:
        return HttpResponse(json.dumps({'status': str(sys.exc_info()[0]) + str(sys.exc_info()[1])}))

    return HttpResponse(json.dumps({'status': 'success'}))


