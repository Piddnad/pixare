# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect
from pixare.views import people

def index(request):
    if request.user.is_authenticated:
        return people.home(request, str(request.user.id))  # 如果已登录，跳转到我的个人页

    else:
        return render(request, 'index.html', {})

