from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone

from braces.views import LoginRequiredMixin

from app.models import Bike, Student, Payment, Ride, Station

from util.util import email_razzi
from util.lend import make_ride, checkin_ride

class Index(LoginRequiredMixin, TemplateView):
    template_name = "staff/index.html"

    def get_context_data(self):
        context = super(Index, self).get_context_data()
        context['bikes'] = Bike.objects.all()
        context['available_bikes'] = Bike.objects.filter(status="available")
        return context

class Emails(LoginRequiredMixin, TemplateView):
    template_name = "staff/emails.html"

    def get_context_data(self):
        four_months_ago = timezone.localtime(timezone.now()) + timezone.timedelta(days=-120)
        context = super(Emails, self).get_context_data()
        unlimited_plans = Payment.objects.filter(plan__name="Unlimited Plan", end_date__isnull=False, end_date__gte=four_months_ago)
        unlimited_emails = [p.student.email for p in unlimited_plans]
        basic_plans = Payment.objects.filter(plan__name="Basic Plan", end_date__isnull=False, end_date__gte=four_months_ago)
        basic_emails = [p.student.email for p in basic_plans]
        bikes_out = Bike.objects.filter(status="out")
        bikes_out_emails = [b.rides.latest().rider.email for b in bikes_out]
        students = Student.objects.filter(join_date__gte=four_months_ago)
        no_plan_students = [s for s in students if not s.payments.all()]
        no_plan_emails = [s.email for s in no_plan_students]
        context['unlimited_emails'] = unlimited_emails
        context['basic_emails'] = basic_emails
        context['bikes_out_emails'] = bikes_out_emails
        context['no_plan_emails'] = no_plan_emails
        return context

class BikeDashboard(LoginRequiredMixin, TemplateView):
    template_name = "staff/bike_dashboard.html"

    def get_context_data(self):
        context = super(BikeDashboard, self).get_context_data()
        user = self.request.user
        try:
            station = Station.objects.get(name="PSA")
            station_name = station.name
        except IndexError:
            station = None
            station_name = "No Station"

        available_bikes = Bike.objects.filter(status="available")
        if user.is_superuser:
            bikes_for_checkout = available_bikes
        else:
            bikes_for_checkout = available_bikes.filter(location=station)

        for bike in bikes_for_checkout:
            ride = bike.rides.latest("checkout_time")
            bike.rider = ride.rider.name
            bike.return_date = ride.checkin_time

        bikes_for_checkin = [b for b in Bike.objects.all() if b.status == 'out']
        for bike in bikes_for_checkin:
            try:
                ride = bike.rides.latest("checkout_time")
                bike.rider = ride.rider.name
                bike.rider_id = ride.rider.pk
                bike.return_date = ride.checkin_time
            except Ride.DoesNotExist:
                bike.ride = None
                bike.rider_id = None
                bike.return_date = None

        eligible = [s for s in Student.objects.all() if s.can_ride]
        context['eligible'] = eligible
        context['location'] = station_name
        context['bikes_for_checkout'] = bikes_for_checkout
        context['bikes_for_checkin'] = bikes_for_checkin
        return context


def login_required_ajax(function=None, redirect_field_name=None):
    """
    Make sure the user is authenticated to access a certain ajax view

    Otherwise return a HttpResponse 401 - authentication required
    instead of the 302 redirect of the original Django decorator
    """
    def _decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=401)
        return _wrapped_view

    if function is None:
        return _decorator
    else:
        return _decorator(function)


@login_required_ajax
def checkout(request):
    try:
        student = request.POST.get("student")
        student = Student.objects.get(name=student)
        bike = request.POST.get("bike")
        bike = Bike.objects.get(name=bike)
        make_ride(student, bike)
        return HttpResponse("success")
    except Exception as error:
        email_razzi("Admin crashed. Locals: {}. Error: {}".format(locals(), error))
        print("Admin: {}".format(locals()))
        return HttpResponse("failure")


@login_required_ajax
def checkin(request):
    try:
        station = Station.objects.get(name="PSA")
        student_id = request.POST.get("student_id")
        student = Student.objects.get(id=student_id)
        ride = student.ride_set.latest("checkout_time")
        checkin_ride(ride, station)
        return HttpResponse("success")
    except Exception as error:
        email_razzi("Admin crashed. Locals: {}. Error: {}".format(locals(), error))
        print("Admin: {}".format(locals()))
        return HttpResponse("failure")


def end_session(request):
    logout(request)
    return redirect("/")

class Particulars(LoginRequiredMixin, TemplateView):
    template_name = 'staff/particulars.html'

    def get_context_data(self):
        students = Student.objects.all()
        students_able_to_ride = [s for s in students if s.can_ride]

        off_campus_active = [s for s in students_able_to_ride
            if s.living_location == 'Off Campus']

        off_campus_historical = [s for s in students if s.living_location == 'Off Campus']

        today = timezone.localtime(timezone.now())
        one_year_ago = today + timezone.timedelta(days=-365)
        riders_in_the_last_year = [
            s for s in students if s.ride_set.filter(
                checkin_time__gte=one_year_ago
            )
        ]

        return {
            'students_able_to_ride': students_able_to_ride,
            'off_campus_active': off_campus_active,
            'off_campus_historical': off_campus_historical,
            'riders_in_the_last_year': riders_in_the_last_year,
        }
