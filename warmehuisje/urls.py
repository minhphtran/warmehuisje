
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('warmehuisje/', include('expenses.urls')),
    path('', RedirectView.as_view(url='warmehuisje/', permanent=True)),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
