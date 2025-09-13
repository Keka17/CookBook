
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('app.urls'))
]

# Обработчики ошибок
# 404, 500 - только при DEBUG = False
handler403 = "app.views.tr_handler403"
handler404 = "app.views.tr_handler404"
handler500 = "app.views.tr_handler500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)


