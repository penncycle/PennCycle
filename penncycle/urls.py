from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
admin.autodiscover()

from app.views import (
    Index, Signup, Locations, Bikes, welcome, StudentUpdate,
    verify_payment, verify_waiver, verify_pin, lookup,
    bursar, credit, cash, combo, modify_payment, Stats,
    thanks
)
from app.dump import dump
from mobile.views import sms, send_pin

urlpatterns = patterns(
    '',
    url(r'^manage/', include(admin.site.urls)),
    url(r'^admin/', include('staff.urls')),
    url(r'^admin-login/$', login),
    url(r'^logout/$', logout, {'next_page': '/'}),

    # Normal pages
    (r'^$', Index.as_view()),
    (r'^signup/$', Signup.as_view()),  
    (r'^signin/$', login, {"template_name": "signin.html"}),
    (r'^login/$', login, {"template_name": "signin.html"}),
    (r'^faq/$', TemplateView.as_view(template_name="faq.html")),
    (r'^safety/$', TemplateView.as_view(template_name="safety.html")),
    (r'^about/$', TemplateView.as_view(template_name="about.html")),
    (r'^locations/$', Locations.as_view()),
    (r'^bikes/$', Bikes.as_view()),
    (r'^welcome/$', welcome),
    (r'^update/$', StudentUpdate.as_view()),
    (r'^safety/$', TemplateView.as_view(template_name="safety.html")),
    (r'^safety-overview/$', TemplateView.as_view(template_name="safety_overview.html")),
    (r'^thank.*$', thanks),
    (r'^waiver/$', TemplateView.as_view(template_name="waiver_7-29-14.html")),
    (r'^groupride/$', TemplateView.as_view(template_name="groupride.html")),

    # Backend-related
    (r'^verify_payment/$', verify_payment),
    (r'^verify_waiver/$', verify_waiver),
    (r'^verify_pin/$', verify_pin),
    (r'^lookup/$', lookup),
    (r'^bursar/$', bursar),
    (r'^credit/$', credit),
    (r'^cash/$', cash),
    (r'^dump/$', dump),
    (r'^combo/$', combo),
    (r'^modify_payment/$', modify_payment),
    (r'^bike_request/$', bike_request),


    # Twilio
    (r'^sms/$', sms),

    # Mobile
    url(r'^mobile/', include('mobile.urls')),
    (r'^send_pin/$', send_pin),

    # Stats
    (r'^stats/$', Stats.as_view()),
    url(r'^stats/api/', include('stats.urls')),

    # misc
    url(r'favicon.ico/$', lambda x: HttpResponseRedirect(settings.STATIC_URL + "img/favicon.ico")),

    # only on local
    (r'static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    (r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: ", mimetype="text/plain"))
)
