from django.core.management.base import NoArgsCommand
from django.utils import timezone
from django.utils.timesince import timesince
from django_twilio.client import twilio_client
from penncycle.app.models import Ride
from penncycle.util.util import email_razzi
    
def get_late_rides(self):
        nineteen_hours_ago = timezone.now() + timezone.timedelta(hours=-19)
        eighteen_hours_ago = timezone.now() + timezone.timedelta(hours=-18)
        
        late_rides = Ride.objects.filter(
            checkin_time=None,
            checkout_time__gt=nineteen_hours_ago,
            checkout_time__lte=eighteen_hours_ago
        )
        return late_rides
    
def warn_message(ride):
    bike = ride.bike.name
    checkout_display_time = timezone.localtime(ride.checkout_time)
    time_out = timesince(checkout_display_time)
    latest = checkout_display_time + timezone.timedelta(hours=24)
    latest_format = "{}:{}".format(latest.hour, latest.minute)
    message="You've had bike {} out {}. At {} there'll be a $5 late fee. Return the bike or consider an unlimited plan to remove the 24 hour limit.".format(bike, time_out, latest_format)
    return message

def warn(ride):
    phone = ride.rider.twilio_phone
    twilio_client.sms.messages.create(
        to=phone,
        body= warn_message(ride),
        from_="+12156885468"
    )

class Command(NoArgsCommand):
    """To be run every hour."""
    def handle_noargs(self, **options):
        for ride in get_late_rides(self):
            if "Unlimited" not in ride.rider.payments.get(status="out").plan.name:
                warn(ride)
