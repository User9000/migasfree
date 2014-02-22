# -*- coding: utf-8 -*-

"""
set up our URLs
"""

import os
import django

try:
    from django.conf.urls import patterns, include, url
except:
    from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from ajax_select import urls as ajax_select_urls

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^admin/lookups/', include(ajax_select_urls)),

    url(r'', include('migasfree.server.urls')),
)

if settings.DEBUG and settings.STATIC_ROOT is not None:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
