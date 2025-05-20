"""
URL configuration for dr_turn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('doctors/', include('doctors.urls')),
    path('reservations/', include('reservations.urls')),
    path('clinics/', include('clinics.urls')),
    path('patients/', include('patients.urls')),
    path('wallet/', include('wallet.urls')),
    path('docpages/', include('docpages.urls')),
    path('', include('doctors.urls', namespace='home')),  # Home page will be handled by doctors app
    path('medimag/', include('medimag.urls')),
    path('', include('about_us.urls')),
    # Authentication URLs
    # path('accounts/', include('accounts.urls')),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/',include('user.urls')),
    path('homecare/', include('homecare.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
