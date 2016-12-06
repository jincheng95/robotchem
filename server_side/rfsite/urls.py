from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from controls.views import IndexView, CalorimeterStatusAPI, RunListAPI, DataPointListAPI, DataDownloadView

urlpatterns = [
    url(r'^admin/', admin.site.urls),


    # APIs
    url(r'^api/status/', CalorimeterStatusAPI.as_view()),
    url(r'^api/runs/', RunListAPI.as_view()),
    url(r'^api/data/', DataPointListAPI.as_view()),

    # Download data
    url(r'^download/([0-9]+)/', DataDownloadView),

    # Homepage
    # matches anything, so put this last
    url(r'^', IndexView),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
