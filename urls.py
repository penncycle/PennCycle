from django.conf.urls.defaults import patterns, include, url 
from django.conf import settings
from app.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'penncycle.views.home', name='home'),
    # url(r'^penncycle/', include('penncycle.foo.urls')),

    (r'media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    (r'^$', index),
    (r'^signup/', signup),
    (r'^thanks/', thanks),
    #url(r'^app/', include(app.urls)),
)