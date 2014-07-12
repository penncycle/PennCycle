import json
import logging

logger = logging.getLogger(__name__)

from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.template.loader import render_to_string
from crispy_forms.utils import render_crispy_form

from app.models import Student, Bike, Station

from penncycle.util.util import (
    welcome_email,
    send_pin_to_student,
    feedback_email
)

from penncycle.util.lend import make_ride, checkin_ride

from .forms import SignupForm


def http_json(data):
    return HttpResponse(json.dumps(data), content_type="application/json")

def json_failure(message):
    info = {"error": message}
    body = json.dumps(info)
    return HttpResponseBadRequest(body,
        content_type="application/json")

@csrf_exempt
def check_for_student(request):
    try:
        penncard = request.POST.get("penncard")
        student = Student.objects.get(penncard=penncard)
        reply = {"registered": True, 'student': student.name}
    except Student.DoesNotExist:
        signup_form = SignupForm(initial={"penncard": penncard})
        reply = {
            "registered": False,
            "signup_form": render_crispy_form(signup_form)
        }
    return http_json(reply)


@csrf_exempt
def signup(request):
    form = SignupForm(request.POST)
    if form.is_valid():
        student = form.save()
        reply = {
            'success': True,
            'pin': student.pin,
            'waiver': render_to_string('waiver.html')
        }
        send_pin_to_student(student)
        welcome_email(student)
    else:
        reply = {
            'success': False,
            'signup_form': render_crispy_form(form)
        }
    return http_json(reply)

@csrf_exempt
def verify(request):
    data = request.POST
    penncard = data.get("penncard")
    pin = data.get("pin")
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        return json_failure("Student does not exist.")
    if student.pin == pin:
        return http_json(student.serialize)
    else:
        return json_failure("Invalid PIN.")


@csrf_exempt
def send_pin(request):
    data = request.POST
    try:
        student = Student.objects.get(penncard=data["penncard"])
        send_pin_to_student(student)
        return http_json({"success": True, "phone": student.phone})
    except Student.DoesNotExist:
        return json_failure("No student with that PennCard is registered.")

def bike_data(request):
    data = [
        {
            "name": bike.name,
            "status": bike.status,
            "location": bike.location.name,
            "latitude": bike.location.latitude,
            "longitude": bike.location.longitude,
            "manufacturer": bike.manufacturer.name
        } for bike in Bike.objects.all()
    ]
    return http_json(data)

def station_data(request):
    data = [
        {
            "name": station.name,
            "latitude": station.latitude,
            "longitude": station.longitude
        } for station in Station.objects.all()
    ]
    return http_json(data)

def student_data(request):
    penncard = request.GET.get("penncard")
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        return json_failure("No student with that PennCard has registered.")
    data = {
        "name": student.name,
        "can_ride": student.can_ride,
        "current_ride": student.current_ride.serialize() if student.current_ride else None,
        "ride_history": [
            r.serialize() for r in student.ride_history
        ]
    }
    return http_json(data)


@csrf_exempt
@require_POST
def report(request):
    data = request.POST
    penncard = data.get("penncard")
    feedback = data.get("feedback")
    if penncard and feedback:
        try:
            student = Student.objects.get(penncard=penncard)
            feedback_email(feedback, penncard, student)
        except Student.DoesNotExist:
            feedback_email(feedback, penncard)

        return HttpResponse()

    else:
        return json_failure(
            "invalid POST fields: wanted 'penncard', "
            "'feedback', got {}".format(data)
        )


@csrf_exempt
@require_POST
def checkout(request):
    data = request.POST
    bike = data.get("bike")
    penncard = data.get("penncard")
    pin = data.get("pin")
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        return json_failure("Student does not exist.")
    if student.pin != pin:
        return HttpResponseForbidden()
    if not student.can_ride:
        message = ""
        current_rides = student.ride_set.filter(checkin_time=None)
        if len(current_rides) > 0:
            bike = current_rides[0].bike.name
            message += "You can't check bikes out until you check bike {} in. ".format(bike)
        if not student.waiver_signed:
            message += "You need to fill out a waiver. Click the 'account' button at the bottom and accept the waiver there. "
        if not student.current_payments:
            message = "You don't currently have any PennCycle plans. Log on to penncycle.org to add one."
        return json_failure(message)
    try:
        bike = Bike.objects.get(name=bike)
    except Exception:
        return json_failure(
            "Bike {} is unavailable."
            .format(bike)
        )
    if bike.status == 'available':
        make_ride(student, bike)
    else:
        return json_failure(
            "Bike {} is unavailable with status '{}'."
            .format(bike.name, bike.status)
        )
    return http_json({"combo": bike.combo})


@csrf_exempt
@require_POST
def checkin(request):
    location = request.POST.get("station")
    penncard = request.POST.get("penncard")
    try:
        station = Station.objects.get(name=location)
    except:
        logger.warn('Station missing: {}'.format(location))
        return json_failure("Station not found.")
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        logger.warn('Student missing: {}'.format(penncard))
        return json_failure("No student with that PennCard was found.")
    ride = student.ride_set.latest()
    checkin_ride(ride, station)
    return HttpResponse()
