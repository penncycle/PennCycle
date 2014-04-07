import datetime
import pytz
import random

from django.core.mail import send_mail
from django_localflavor_us.models import PhoneNumberField
from django.db import models
from django.core.validators import RegexValidator
from django.db.models import Q
from django.utils import timezone
from south.modelsinspector import add_introspection_rules

# Necessary because South hasn't been updated since localflavors was broken up.
add_introspection_rules([], ['django_localflavor_us\.models\.PhoneNumberField'])

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
)

GRAD_YEAR_CHOICES = (
    ("2017", "2017"),
    ('2016', '2016'),
    ('2015', '2015'),
    ('2014', '2014'),
    ('grad', 'grad student'),
    ('faculty', 'faculty'),
    ('staff', 'staff'),
    ('guest', 'guest'),
)

LIVING_LOCATIONS = (
    ('Hill', 'Hill'),
    ('KCECH', 'KCECH'),
    ('Riepe', 'Riepe'),
    ('Fisher', 'Fisher'),
    ('Ware', 'Ware'),
    ('Harrison', 'Harrison'),
    ('Harnwell', 'Harnwell'),
    ('Rodin', 'Rodin'),
    ('Stouffer', 'Stouffer'),
    ('Mayer', 'Mayer'),
    ('Du Bois', 'Du Bois'),
    ('Gregory', 'Gregory'),
    ('Sansom', 'Sansom'),
    ('Off Campus', 'Off Campus'),
)

SCHOOL_CHOICES = (
    ('C', 'College'),
    ('W', 'Wharton'),
    ('E', 'SEAS'),
    ('N', 'Nursing'),
    ('ANN', 'Annenberg'),
    ('DEN', 'Dental'),
    ('DES', 'Design'),
    ('GSE', 'Education'),
    ('LAW', 'Law'),
    ('MED', 'Medicine'),
    ('SPP', 'Social Policy & Practice'),
    ('VET', 'Veterinary'),
    ('O', 'Other or N/A'),
)

PAYMENT_CHOICES = (
    ('cash', 'cash'),
    ('penncash', 'penncash'),
    ('bursar', 'bursar'),
    ('credit', 'credit'),
    ('group', 'group'),
    ('free', 'free'),
    ('other', 'other'),
)


class Plan(models.Model):
    name = models.CharField(max_length=100)
    cost = models.IntegerField()
    description = models.TextField(max_length=150, null=True)

    def __unicode__(self):
        return self.name + ': $' + str(self.cost)

class Payment(models.Model):
    class Meta:
        get_latest_by = 'purchase_date'

    amount = models.DecimalField(decimal_places=2, max_digits=6)
    plan = models.ForeignKey(Plan)
    student = models.ForeignKey('Student', related_name="payments")
    purchase_date = models.DateField(auto_now_add=True)
    payment_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    satisfied = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=100, choices=PAYMENT_CHOICES, blank=True)
    status = models.CharField(max_length=100, default='available')
    renew = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.student) + ' for ' + str(self.plan)

    @property
    def serialize(self):
        return {
            "plan": self.plan.name,
            "end_date": str(self.end_date) or "Activates after your first ride."
        }

class Manufacturer(models.Model):
    name = models.CharField(max_length=30)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=60, blank=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    def __unicode__(self):
        return self.name

def generate_pin():
    return str(random.randint(1000, 10000))

class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = PhoneNumberField(unique=True)
    penncard = models.CharField(max_length=8, validators=[RegexValidator('\d{8}')], unique=True)
    last_two = models.CharField(max_length=2, validators=[RegexValidator('\d{2}')], default="00")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    grad_year = models.CharField(max_length=50, choices=GRAD_YEAR_CHOICES)
    join_date = models.DateField(default=datetime.date.today())
    school = models.CharField(max_length=100, choices=SCHOOL_CHOICES, blank=True)
    major = models.CharField(max_length=50, blank=True)
    living_location = models.CharField(max_length=100, choices=LIVING_LOCATIONS)
    waiver_signed = models.BooleanField(default=False)
    staff = models.NullBooleanField(default=False)
    pin = models.CharField(max_length=4, default=generate_pin)

    @property
    def twilio_phone(self):
        return "+1" + self.phone.replace("-", "")

    @property
    def paid_now(self):
        return bool(self.current_payments)

    @property
    def current_payments(self):
        today = datetime.date.today()
        payments = self.payments.filter(satisfied=True).filter(
            Q(
                end_date__gte=today,
            ) | Q(
                end_date__isnull=True
            )
        )
        return payments

    @property
    def can_ride(self):
        return bool(self.waiver_signed and self.current_payments.filter(status='available'))

    def __unicode__(self):
        return u'%s %s' % (self.name, self.penncard)

    @property
    def current_ride(self):
        rides = Ride.objects.filter(rider=self)
        try:
            ride = rides.get(checkin_time__isnull=True)
            return ride
        except Ride.DoesNotExist:
            return None

    @property
    def ride_history(self):
        return Ride.objects.filter(rider=self, checkin_time__isnull=False)

    @property
    def serialize(self):
        current_ride = self.current_ride
        if current_ride:
            current_ride = current_ride.serialize
        else:
            current_ride = None

        return {
            "name": self.name,
            "can_ride": self.can_ride,
            "ride_history": [r.serialize for r in self.ride_history],
            "current_ride": current_ride,
            "current_payments": [p.serialize for p in self.current_payments]
        }

class Station(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField(default=39.9529399)
    longitude = models.FloatField(default=-75.1905607)
    address = models.CharField(max_length=300, blank=True)
    notes = models.TextField(max_length=100, blank=True, null=True)
    hours = models.TextField(max_length=100, blank=True, null=True)
    picture = models.ImageField(upload_to='img/stations', blank=True, null=True)
    full_name = models.CharField(max_length=100, default="")

    def __unicode__(self):
        return self.name

    @property
    def is_open(self):
        hour = datetime.datetime.now().hour
        return hour > 10 and hour < 18

    @property
    def bikes(self):
        return Bike.objects.filter(location=self)


class Bike(models.Model):
    name = models.CharField(max_length=100, unique=True)
    manufacturer = models.ForeignKey(Manufacturer)
    purchase_date = models.DateField()
    color = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=100, default='available')
    serial_number = models.CharField(max_length=100, blank=True)
    tag_id = models.CharField(max_length=100, blank=True)
    key_serial_number = models.CharField(max_length=100, blank=True)
    combo = models.CharField(max_length=4, blank=True)
    combo_update = models.DateField()
    location = models.ForeignKey(Station, default=2)

    @property
    def knows_combo(self):
        rides = self.rides.filter(checkout_time__gt=self.combo_update)
        return list(set([ride.rider for ride in rides]))

    def __unicode__(self):
        return '#%s. Location: %s' % (self.name, self.location.name)

    def serialize(self):
        return {
            "name": self.name,
            "status": self.status,
            "location": self.location.name
        }

    def save(self):
        log = Info(message="Bike {} has combo {}".format(self, self.combo))
        log.save()
        return super(Bike, self).save()

class Ride(models.Model):
    class Meta:
        get_latest_by = "checkout_time"

    rider = models.ForeignKey(
        Student, limit_choices_to={
            'payments__status': 'available',
            'waiver_signed': True,
            'payments__satisfied': True,
        },
    )
    bike = models.ForeignKey('Bike', limit_choices_to={'status': 'available'}, related_name='rides')
    checkout_time = models.DateTimeField(auto_now_add=True)
    checkin_time = models.DateTimeField(null=True)
    checkout_station = models.ForeignKey(Station, default=2, related_name='checkouts')
    checkin_station = models.ForeignKey(Station, null=True, related_name='checkins')

    @property
    def ride_duration_days(self):
        if self.checkin_time is None:
            end = datetime.datetime.now(pytz.utc)
        else:
            end = self.checkin_time
        duration = end - self.checkout_time
        return duration.days

    @property
    def status(self):
        if self.checkin_time is None:
            return 'out'
        else:
            return 'in'

    def __unicode__(self):
        return u'%s on %s' % (self.rider, timezone.localtime(self.checkout_time))

    @property
    def serialize(self):
        return {
           "bike": self.bike.serialize(),
           "checkout_time": str(self.checkout_time),
           "checkin_time": str(self.checkin_time),
           "checkout_station": self.checkout_station.name,
           "checkin_station": self.checkin_station.name if self.checkin_station else None
        }

    def rider_phone(self):
        return self.rider.phone


class Comment(models.Model):
    comment = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey(Student, blank=True, null=True)
    ride = models.ForeignKey(Ride, blank=True, null=True)
    is_problem = models.BooleanField(default=False)

    def save(self):
        super(Comment, self).save()
        message = '''
            Comment: {}\n
            Time: {}\n
            Student: {}\n
            Ride: {}\n
            Marked as problem: {}\n
        '''.format(self.comment, self.time, self.student, self.ride, self.is_problem)
        send_mail('PennCycle: Comment Submitted', message, 'messenger@penncycle.org', ['messenger@penncycle.org'])

    def __unicode__(self):
        return self.comment[:30]


class Info(models.Model):
    message = models.TextField()
    date = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return self.message + " on " + self.date.isoformat()

class Helmet(models.Model):
    number = models.CharField(max_length=3, unique=True)
    student = models.ForeignKey(Student, blank=True, null=True)
    checkout_date = models.DateField(blank=True, null=True)
    checkin_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return "Helmet {}".format(self.number)
