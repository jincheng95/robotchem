from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from controls import views
from rfsite.settings import DEBUG

urlpatterns = [
    url(r'^admin/', admin.site.urls),


    # APIs
    url(r'^api/status/', views.CalorimeterStatusAPI.as_view()),
    url(r'^api/runs/', views.RunListAPI.as_view()),
    url(r'^api/run/(?P<pk>[0-9]+)/$', views.RunDetailsAPI.as_view()),
    url(r'^api/data/', views.DataPointListAPI.as_view()),

    # Download data
    url(r'^download/([0-9]+)/', views.DataDownloadView),

    # Homepage
    # matches anything, so put this last
    url(r'^((history|calibrate)|history/[0-9]+)/?$', views.IndexView),

]

if DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
