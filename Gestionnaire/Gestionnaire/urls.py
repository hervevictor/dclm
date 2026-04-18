"""Gestionnaire URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:    path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
import django.views.i18n

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),

    path('admin/', admin.site.urls),
    path('', include('Eglises.urls')),
    path('adultes/', include('Adultes.urls')),
    path('jeunes/', include('Jeunes_app.urls')),
    path('enfants/', include('Enfants.urls')),
    path('bilans/', include('Bilans.urls')),
    path('annonces/', include('Annonces.urls')),
    path('Lumiere_cite/', include('LumiereCite.urls')),
    path('particularite/', include('Particularite.urls')),
    
    path('membres/', include('django.contrib.auth.urls')),
    path('membres/', include('Membres.urls')),
    path('seances/', include('Seances.urls')),
    path('finances/', include('Finances.urls')),
    path('gck/', include('GCK.urls')),
    path('voeux/', include('Voeux.urls')),
    path('retraites/', include('Retraites.urls')),
    path('quotas/', include('Quotas.urls')),
    path('croissance/', include('Croissance.urls')),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
