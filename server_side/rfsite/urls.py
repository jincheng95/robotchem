from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from controls.views import IndexView, CalorimeterStatusAPI

urlpatterns = [
    url(r'^admin/', admin.site.urls),


    # APIs
    url(r'^api/status/$', CalorimeterStatusAPI.as_view()),

    # Homepage
    # matches anything, so put this last
    url(r'^', IndexView),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
