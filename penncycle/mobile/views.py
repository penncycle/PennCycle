import re

from django.contrib import messages
from django.http import HttpResponseRedirect

import twilio.twiml
from django_twilio.decorators import twilio_view

from app.models import Student, Bike, Station
from penncycle.util.util import email_razzi, send_pin_to_student, email_managers
from penncycle.util.lend import make_ride, checkin_ride
from django.utils import timezone

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
        elif not student.current_payments:
            message = (
                "You don't currently have any PennCycle plans. "
                "Log on to penncycle.org/signin to add one."
            )
        elif len(current_rides) > 0:
            bike = current_rides[0].bike.name
            message = "You can't check bikes out until you check bike {} back in. ".format(bike)
        else:
            message = "You are currently unable to ride. Log in to your penncycle account at penncycle.org/signin to fix this."
            email_razzi("Strange cannot ride case. {}".format(locals()))
        return message
    try:
        bike_number = re.search("\d+", body).group()
    except:
        return "Command not understood. Text 'help' for a list of commands. Example of checking out a bike would be: Checkout 10"
    try:
        bike = Bike.objects.get(name=bike_number)
    except Bike.DoesNotExist:
        message = "Bike not found. Text 'Checkout (number)', where number is 1 or 2 digits. Text 'Report (issue)' to report an issue."
        return message
    if bike.status == "available":
        make_ride(student, bike)
        message = "You have successfully checked out bike {}. The combination is {}. To return it, reply 'Checkin Hill' or any other station. Text 'Stations' for a list.".format(bike_number, bike.combo)
    elif bike.status == "out":
        checkout_time = bike.rides.latest().checkout_time
        time_string = timezone.localtime(checkout_time).strftime("%H:%M on %D")
        message = "Bike {} is still in use. It was checked out at {}. Text 'bikes' for a list of available bikes.".format(bike.name, time_string)
    else:
        message = "Bike {} is not in service. Please try another bike, or text 'bikes' for a list of available bikes.".format(bike.name)
    return message

def handle_stations():
    message = (
        "Stations: Rodin, Ware, Fisher, Huntsman, College Hall, "
        "and Hill. To return a bike text 'Checkin Hill' or another station."
    )
    return message

def handle_checkin(student, body):
    # Make sure they actually have a bike out
    if not student.ride_set.filter(checkin_time=None):
        try:
            ride = student.ride_set.latest("checkin_time")
        except:
            return "You have never checked out a bike. Check out a bike using the 'checkout (number)'. Once you have done that, use this command to return it."

        checkin_display_time = timezone.localtime(ride.checkin_time)
        time_of_day = "{}:{}".format(checkin_display_time.hour, checkin_display_time.minute)
        return "You don't have any rides to check in. Your last ride was checked in at {} at {}.".format(time_of_day, ride.checkin_station)

    # Get their location and check the bike in
    location = None
    stations = Station.objects.all()
    for station in stations:
        if station.name.lower() in body or (station.full_name and station.full_name.lower() in body):
            location = station
    if not location:
        email_razzi("Station didn't match for checkin. Message was {}".format(body))
        message = "Station not found. Options: Rodin, Ware, Huntsman, Fisher, College Hall, Hill, PSA. To return text 'Checkin Hill' or another station."
        return message
    ride = student.ride_set.latest("checkout_time")
    checkin_ride(ride, location)
    message = "You have successfully returned your bike at {}. Make sure it is locked, and we will confirm the bike's checkin location shortly. Thanks!".format(location)
    return message

def handle_help(student, body):
    if student.can_ride:
        message = "Checkout: Checkout (number). Checkin: Checkin (location). Text Stations or Bikes for station/bike info. Report (issue) reports an issue. You can check out bikes"
        return message
    else:
        current_rides = student.ride_set.filter(checkin_time=None)
        if len(current_rides) > 0:
            bike = current_rides[0].bike.name
            message = "You have bike {} out. Until you return it, you can't check out bikes. Text 'locations' for checkin stations and 'report' to report an issue.".format(bike)
        elif not student.waiver_signed:
            email_razzi("Waiver not signed by {} on sms.".format(student))
            message = "You need to fill out a waiver. Log on to www.penncycle.org/signin to do so."
        else:
            email_razzi("{} doesn't have any payments, it would seem. Contact him at {}".format(student.name, student.email))
            message = "You are unable to check out bikes. Go to penncycle.org/signin and enter your penncard to check your status. You must purchase a plan before you can ride."
        if not any(command in body for command in ["help", "info", "information", "?"]):
            email_razzi("Body didn't match command. {}".format(locals()))
        return message

def handle_bikes():
    stations = [s for s in Station.objects.all() if s.bikes]
    summary = ""
    for station in stations:
        bikes = station.bikes.order_by('name')
        if len(bikes) > 4:
            bikename_list = [bikes[i].name for i in range(4)]
        else:
            bikename_list = [b.name for b in bikes]

        bikename_list.sort()

        data = {
            "bikes": ", ".join(bikename_list),
            "station": station.name
        }
        summary += "At {station}: {bikes}. ".format(**data)

    if not summary:
        summary = "All of our bikes are currently out. Check penncycle.org/bikes or try again soon."
    else:
        summary = "See penncycle.org/bikes for a full list. " + summary
    return summary

def handle_report(student, body):

    email_body = "{} reported {}. ".format(student, body)
    # check if they have a bike out
    ride = student.current_ride
    if ride:
        bike = ride.bike
    else:
        try:
            bike_number = re.search("\d+", body).group()
            bike = Bike.objects.get(name=bike_number)
        except:
            bike = None
    if bike:
        bike.status = body
        bike.save()
        email_body += "{} had its status changed to {}.".format(bike, body)
    else:
        email_body += "No bikes were changed."
    email_subject = "{} reported issue: {}".format(student, body)
    email_managers(email_body, email_subject)
    return "Thank you. We will take care of the issue as soon as we can. In the meantime, text 'bikes' for available bikes. Email messenger@penncycle.org with questions."

def handle_sms(student, body):
    if any(command in body for command in ["rent", "checkout", "check out", "check-out"]):
        return handle_checkout(student, body)
    elif any(command in body for command in ["checkin", "return", "check in", "check-in"]):
        return handle_checkin(student, body)
    elif any(command in body for command in ["station", "stations", "location", "locations"]):
        return handle_stations()
    elif any(command in body for command in ["bikes", "available"]):
        return handle_bikes()
    elif any(command in body for command in ["report"]):
        return handle_report(student, body)
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
        return reply(message)
    body = request.POST.get("Body", "").lower()
    response = handle_sms(student, body)
    return reply(response)
