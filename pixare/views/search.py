from django.shortcuts import render
from pixare.models.photo import Photo
from pixare.models.tag import Tag
from django.contrib.auth.models import User
from pixare.views import error_404

def default(request):
    if 'q' in request.GET:
        q = request.GET['q']
        if not q:
            return error_404(request)
        else:
            # contains是严格区分大小写的，icontains（Case-insensitive contains）是不严格区分大小写的
            inner_qs_tag = Tag.objects.filter(name__icontains=q)
            inner_qs_user = User.objects.filter(profile__name__contains=q)
            photo_by_tag = Photo.objects.filter(tags__in=inner_qs_tag).order_by('id')
            photo_by_user_name = Photo.objects.filter(owner__in=inner_qs_user).order_by('id')
            photos_by_caption = Photo.objects.filter(caption__icontains=q).order_by('id')

            # 将根据用户名，标签，描述，搜索到的图片列表合并成不包含重复的图片列表
            photos = merge_photos(photo_by_tag, photo_by_user_name, photos_by_caption)
            for p in photos:
                p.tag_list = p.tags.all()[0:4]  # 只取前4个标签

            p_len = len(photos)

            p_items = []
            for i in range(0, p_len, 3):
                p_items.extend([photos[i:i + 3]])  # 在末端添加列表元素

            return render(request, 'search.html', {'query': q, 'p_items': p_items})
    else:
        return error_404(request)

# 将根据用户名，标签，描述，搜索到的图片列表合并成不包含重复的图片列表
def merge_photos(photo_by_tag, photo_by_user_name, photos_by_caption):
    photos = list(photo_by_tag)

    for p_list in (photo_by_user_name, photos_by_caption):
        temp = []
        for p in p_list:
            flag = False
            left = 0
            right = len(photos) - 1
            while left <= right:  # 用二分搜索查找是否存在重复photo
                mid = int((left + right) / 2)
                if p.id == photos[mid].id:
                    flag = True  # 存在重复的id
                    break
                elif p.id > photos[mid].id:
                    left = mid + 1
                else:
                    right = mid - 1

            if flag == False:
                temp.append(p)
        photos.extend(temp)

    return photos