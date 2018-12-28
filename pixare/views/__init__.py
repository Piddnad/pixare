from django.shortcuts import render

def error_404(request):
    return render(request, '404.html', {})



from . import home
from . import accounts
from . import photos
from . import explore
from . import search
from . import people


from django.conf import settings
def global_settings(request):
    return {"QINIU_IMG_URL": settings.QINIU_IMG_URL,}