import re

from django.contrib import messages
from django.http import HttpResponseRedirect

import twilio.twiml
from django_twilio.decorators import twilio_view

from app.models import Student, Bike, Station
from penncycle.util.util import email_razzi, send_pin_to_student
from penncycle.util.lend import make_ride, checkin_ride


def send_pin(request):
    penncard = request.GET.get("penncard")
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        messages.info(
            request,
            "Student with penncard {} does not exist. "
            "Sign up for PennCycle using the form below.".format(penncard)
        )
        return HttpResponseRedirect("/signup?penncard={}".format(penncard))
    send_pin_to_student(student)
    messages.info(request, "Pin sent to {}.".format(student.phone))
    return HttpResponseRedirect("/signin?penncard={}".format(penncard))

def reply(message):
    reply = twilio.twiml.Response()
    if len(message) > 160:
        message = message[:160]
        email_razzi("Long message. {}".format(message))
    reply.sms(message)
    return reply

def handle_checkout(student, body):
    if not student.can_ride:
        current_rides = student.ride_set.filter(checkin_time=None)
        if not student.waiver_signed:
            message = "You need to accept our waiver. Go to penncycle.org/signin to do so."
        if not student.current_payments:
            message = (
                "You don't currently have any PennCycle plans. "
                "Log on to penncycle.org/signin to add one."
            )
        if len(current_rides) > 0:
            bike = current_rides[0].bike.name
            message = "You can't check bikes out until you check bike {} back in. ".format(bike)
        return message
    try:
        bike_number = re.search("\d+", body).group()
    except:
        return "Command not understood. Text 'help' for a list of commands. Example of checking out a bike would be: Checkout 10"
    try:
        bike = Bike.objects.get(name=bike_number)
    except Bike.DoesNotExist:
        message = "Bike not found. Text 'Checkout (number), where number is 1 or 2 digits."
        return message
    if bike.status == "available":
        make_ride(student, bike)
        message = "You have successfully checked out bike {}. The combination is {}. To return it, reply 'Checkin Hill' or any other station. Text 'Stations' for a list.".format(bike_number, bike.combo)
        return message
    elif bike.status == "out":
        checkout_time = bike.rides.latest().checkout_time
        time_string = checkout_time.strftime("%H-%M on %D")
        message = "Bike {} is still in use. It was checked out at {}.".format(bike.name, time_string)
        return message

def handle_stations(body):
    message = (
        "Stations: Rodin, Ware, Fisher, Huntsman, College Hall, "
        "and Hill. To return a bike text 'Checkin Hill' or another station."
    )
    return message

def handle_checkin(student, body):
    location = None
    stations = [station.name.lower() for station in Station.objects.exclude(name="PSA")]
    for station in stations:
        if station in body:
            location = Station.objects.get(name=station.title())
    if not location:
        email_razzi("Station didn't match for checkin. Message was {}".format(body))
        message = "Station not found. Options: Rodin, Ware, Huntsman, Fisher, College Hall, Hill. To check in, text 'Checkin Hill' or another station."
        return message
    ride = student.ride_set.latest("checkout_time")
    checkin_ride(ride, location)
    message = "You have successfully returned your bike at {}. Make sure it is locked, and we will confirm the bike's checkin location shortly. Thanks!".format(location)
    return message

def handle_help(student, body):
    if student.can_ride:
        message = "Checkout a bike: 'Checkout (number)'. Checkin: 'Checkin (location)'. Text 'stations' to view stations. You're eligible to checkout bikes."
        return message
    else:
        current_rides = student.ride_set.filter(checkin_time=None)
        if len(current_rides) > 0:
            bike = current_rides[0].bike.name
            message = "You still have {} out. Until you check it in, you cannot check out bikes. Text 'locations' for checkin stations.".format(bike)
        elif not student.waiver_signed:
            email_razzi("Waiver not signed by {} on sms.".format(student))
            message = "You need to fill out a waiver. Log on to www.penncycle.org/signin to do so."
        else:
            email_razzi("{} doesn't have any payments, it would seem. Contact him at {}".format(student.name, student.email))
            message = "You are currently unable to check out bikes. Go to penncycle.org/signin and enter your penncard to check your status."
        if not any(command in body for command in ["help", "info", "information", "?"]):
            email_razzi("Body didn't match command. {}".format(locals()))
        return message

def handle_sms(student, body):
    if any(command in body for command in ["rent", "checkout", "check out", "check-out"]):
        return handle_checkout(student, body)
    elif any(command in body for command in ["checkin", "return", "check in", "check-in"]):
        return handle_checkin(student, body)
    elif any(command in body for command in ["station", "stations", "location", "locations"]):
        return handle_stations(body)
    else:
        return handle_help(student, body)

@twilio_view
def sms(request):
    fromNumber = request.POST.get("From")
    number = fromNumber[2:]
    lookup = number[0:3]+"-"+number[3:6]+"-"+number[6:]
    try:
        student = Student.objects.get(phone=lookup)
    except Student.DoesNotExist:
        message = "Welcome to PennCycle! Visit penncycle.org to get started. Sign up for any plan to start checking bikes out bikes using your phone."
        reply(message)
    body = request.POST.get("Body", "").lower()
    response = handle_sms(student, body)
    return reply(response)
