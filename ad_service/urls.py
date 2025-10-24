from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='products:catalog'), name='home'),
    path('catalog/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('users/', include('users.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls', namespace='notifications')),  # ← ДОБАВЬТЕ ЗАПЯТУЮ ЗДЕСЬ
    path('', include('pages.urls')),  # Эта строка должна быть ПОСЛЕДНЕЙ
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)