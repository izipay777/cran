from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path

from main import settings

urlpatterns = [
    path("ePmnGJ9Rah4tieg2hu1s2/", admin.site.urls),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
