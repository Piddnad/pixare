# -*- encoding: utf-8 -*-
# from PIL import Image


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from pixare.models.userprofile import UserProfile
from django.contrib import auth
from pixare.forms import RegistrationForm, LoginForm, ProfileForm, PwdChangeForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from pixare.views import error_404
import os, time
from MySite import settings
from qiniu import Auth, put_file, etag, put_data
import qiniu.config
from PIL import Image
from io import BytesIO

# 登录
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('pixare:profile', args=[user.id]))

            else:
                # 登陆失败
                return render(request, 'accounts/login.html', {'form': form,
                                                            'message': '你的帐号和密码不符，请重试'})
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})



# 注销
@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')  # 跳转到主页


# 注册
def register(request):
    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password2']

            # 使用内置User自带create_user方法创建用户，不需要使用save()
            user = User.objects.create_user(username=username, password=password, email=email)

            # 如果直接使用objects.create()方法后不需要使用save()
            user_profile = UserProfile(user=user)
            user_profile.avatar_loc = 'avatar_default.png' #设置默认头像
            user_profile.avatar_square_loc = 'avatar_default.png'
            user_profile.save()

            return HttpResponseRedirect("/accounts/login/")

    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


#个人资料
@login_required
def profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'accounts/profile.html', {'user': user})


#修改个人资料
@login_required
def profile_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    user_profile = get_object_or_404(UserProfile, user=user)

    if request.method == "POST":
        form = ProfileForm(request.POST)

        if form.is_valid():
            user_profile.name = form.cleaned_data['name']
            user_profile.city = form.cleaned_data['city']
            user_profile.intro = form.cleaned_data['intro']
            user_profile.save()

            return HttpResponseRedirect(reverse('pixare:profile', args=[user.id]))
    else:
        default_data = {'name': user_profile.name,
                        'city': user_profile.city, 'intro': user_profile.intro, }
        form = ProfileForm(default_data)

    return render(request, 'accounts/profile_update.html', {'form': form, 'user': user})


@login_required
def pwd_change(request, pk):

    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = PwdChangeForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['old_password']
            username = user.username

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                new_password = form.cleaned_data['password2']
                user.set_password(new_password)
                user.save()
                return HttpResponseRedirect("/accounts/login/")

            else:
                return render(request, 'accounts/pwd_change.html', {'form': form,
                                                                 'user': user, 'message': 'Old password is wrong. Try again'})
    else:
        form = PwdChangeForm()

    return render(request, 'accounts/pwd_change.html', {'form': form, 'user': user})

@login_required
def editavatar(request):
    if not request.user.is_authenticated:
        return error_404(request)

    if request.method == 'POST':
        q = Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
        bucket_name = 'pixare'


        user = request.user
        file_name = 'a_' + str(user.id) + '_temp.jpg'  # 临时头像文件
        temp_avatar_loc = '/static/avatars/' + file_name  # 头像图片相对于站点的存放位置
        temp_abs_path = (os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../static'), 'avatars/')) + file_name
        token = q.upload_token(bucket_name, file_name, 3600)

        # 多个submit的判断，第一个name，第二个是value
        if request.POST.get('pic_submit') == u'上传图片':  # 中文使用unicode，要加u
            img_file = request.FILES.get('pic_avatar')
            if img_file == None:  # 没有选择图片
                if os.path.isfile(temp_abs_path):  # 如果已存在上次上传的临时头像图片，则显示上传上传的图片
                    avatar_loc = temp_avatar_loc
                else:
                    avatar_loc = user.profile.avatar_loc
                return render(request, "accounts/editavatar.html", {'avatar_loc': avatar_loc})
            else:
                image = Image.open(img_file)
                image = makeSquareImg(image, 160)
                if os.path.isfile(temp_abs_path):  # 如果已存在上次上传的临时头像图片，先删除
                    os.remove(temp_abs_path)
                image.save(temp_abs_path, "png", quality=90)  # 将该头像图片临时保存起来，不设置quality，默认是75

                output = BytesIO()
                image.save(output, "png", quality=90)  # 不设置quality，默认是75
                img_data = output.getvalue()
                output.close()
                ret, info = put_data(token, file_name, img_data)

                return render(request, "accounts/editavatar.html",{'avatar_loc': file_name})
        elif request.POST.get('save') == u'保存':
            if os.path.isfile(temp_abs_path):  # 如果存在上传的临时头像图片，更新头像
                nowTime = time.localtime()
                # 头像地址加上时间，和之前的头像予以区分，可以避免使用相同路径，导致浏览器缓存图片而使得在返回个人资料页时，头像还是之前的
                user.profile.avatar_loc = '%s_a_%s_%s_l.jpg' % (settings.QINIU_FILE_PREFIX, str(user.id),
                                                        time.strftime('%Y%m%d%H%M%S', nowTime))
                user.profile.avatar_square_loc = '%s_a_%s_%s_s.jpg' % (settings.QINIU_FILE_PREFIX, str(user.id),
                                                               time.strftime('%Y%m%d%H%M%S', nowTime))
                user.profile.save()  # 保存数据到数据库


                image = Image.open(temp_abs_path)
                output = BytesIO()
                image.save(output, "png", quality=90)  # 不设置quality，默认是75
                img_data = output.getvalue()
                output.close()
                token = q.upload_token(bucket_name, user.profile.avatar_loc, 3600)
                ret, info = put_data(token, user.profile.avatar_loc, img_data)

                image = makeSquareImg(image, 48)
                output = BytesIO()
                image.save(output, "png", quality=90)  # 不设置quality，默认是75
                img_data = output.getvalue()
                output.close()
                token = q.upload_token(bucket_name, user.profile.avatar_square_loc, 3600)
                ret, info = put_data(token, user.profile.avatar_square_loc, img_data)


            return HttpResponseRedirect(reverse('pixare:profile', args=[user.id]))
        elif request.POST.get('cancel') == u'撤销':
            if os.path.isfile(temp_abs_path):  # 如果存在上传的临时头像图片，删除该图片
                os.remove(temp_abs_path)
            return HttpResponseRedirect(reverse('pixare:profile', args=[user.id]))
    else:
        user = request.user
        return render(request, "accounts/editavatar.html",{'avatar_loc': user.profile.avatar_loc})

# 生成方形缩略图
def makeSquareImg(im, size=48):
    mode = im.mode
    if mode not in ('L', 'RGB'):
        if mode == 'RGBA':
            # 透明图片需要加白色底
            alpha = im.split()[3]
            bgmask = alpha.point(lambda x: 255 - x)
            im = im.convert('RGB')
            im.paste((255, 255, 255), None, bgmask)
        else:
            im = im.convert('RGB')

    width, height = im.size
    if width == height:
        region = im
    else:
        if width > height:
            delta = (width - height) / 2
            box = (delta, 0, delta + height, height)
        else:
            delta = (height - width) / 2
            box = (0, delta, width, delta + width)
        region = im.crop(box)

    thumb = region.resize((size, size), Image.ANTIALIAS)
    return thumb