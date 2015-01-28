from django.conf.urls import patterns, url

from views import (
    Index, BikeDashboard, checkout, checkin, Emails, Payments, Particulars
)

urlpatterns = patterns(
    '',
    (r'^$', Index.as_view()),
    url(r'^checkouts/$', BikeDashboard.as_view(), name="bike dashboard"),
    url(r'^payments/$', Payments.as_view(), name="payments"),
    url(r'^emails/$', Emails.as_view(), name="emails"),
    (r'checkout/$', checkout),
    (r'checkin/$', checkin),
    (r'particulars/$', Particulars.as_view()),
)
