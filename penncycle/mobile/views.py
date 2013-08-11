import re

from django.contrib import messages
from django.http import HttpResponseRedirect

import twilio.twiml
from django_twilio.decorators import twilio_view

from app.models import Student, Bike, Station
from penncycle.util.util import email_razzi
from penncycle.util.lend import make_ride, checkin_ride
from penncycle.util.mobile_util import send_pin_to_student


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


@twilio_view
def sms(request):
    response = twilio.twiml.Response()
    fromNumber = request.POST.get("From")
    number = fromNumber[2:]
    lookup = number[0:3]+"-"+number[3:6]+"-"+number[6:]
    try:
        student = Student.objects.get(phone=lookup)
    except:
        duplicates = Student.objects.filter(phone=lookup)
        if len(duplicates) > 1:
            message = ("Multiple students have your number. Email messenger@penncycle.org whether you're " + "{} or " * (len(duplicates)-1) + "{}.").format(*duplicates)
            email_razzi("Duplicates! {}".format(duplicates))
        else:
            message = "Welcome to PennCycle! Visit app.penncycle.org to get started. Sign up for any plan to start checking bikes out by texting."
        response.sms(message)
        return response
    body = request.POST.get("Body", "").lower()
    if any(command in body for command in ["rent", "checkout", "check out", "check-out"]):
        if not student.can_ride:
            message = "Hi {}! ".format(student.name)
            currentRides = student.ride_set.filter(checkin_time=None)
            if len(currentRides) > 0:
                bike = currentRides[0].bike.bike_name
                message += "You can't check bikes out until you check bike {} back in. ".format(bike)
            if not student.waiver_signed:
                email_razzi("Waiver not signed by {}".format(student))
                message += "You need to fill out a waiver. Go to penncycle.org/login to do so."
            response.sms(message)
            return response
        try:
            bike_number = re.search("\d+", body).group()
        except:
            response.sms("Command not understood. Text 'info' for a list of commands. Example of checking out a bike would be: Checkout 10")
            email_razzi("Looks like somebody had the wrong bike number. Message: {}".format(body))
            return response
        try:
            bikes = Bike.objects.filter(status="available").filter(bike_name__startswith=bike_number)
            for b in bikes:
                if b.bike_name.startswith(bike_number):
                    bike = b
            make_ride(student, bike)
            message = "You have successfully checked out bike {}. The combination is {}. To return the bike, reply 'checkin PSA' (or any other station). Text 'Stations' for a list.".format(bike_number, bike.combo)
        except:
            message = "The bike you have requested was unavailable or not found. Text 'Checkout (number)', where number is 1 or 2 digits."
            count = 0
            bikes = Bike.objects.filter(status="available").filter(bike_name__startswith=bike_number)
            for b in bikes:
                if b.bike_name.split()[0] == bike_number:
                    count += 1
            email_razzi("Problem with bike {} and student {}. Message was {}. Found {} / {}".format(bike_number, student, body, count, len(bikes)))
    elif any(command in body for command in ["checkin", "return", "check in", "check-in"]):
        location = None
        stations = [station.name.lower() for station in Station.objects.all()]
        for station in stations:
            if station in body:
                if station == "psa":
                    location = Station.objects.get(name="PSA")
                else:
                    location = Station.objects.get(name=station.capitalize())
        if not location:
            email_razzi("Station didn't match for checkin. Message was {}".format(body))
            message = "Station not found. Options: PSA, Rodin, Ware, Fisher, Stouffer, Houston, Hill (PSA=Penn Student Agencies). To return a bike text 'Checkin PSA' or another station."
            response.sms(message)
            return response
        checkin_ride(student, location)
        message = "You have successfully returned your bike at {}. Make sure it is locked, and we will confirm the bike's checkin location shortly. Thanks!".format(location)
        email_razzi("{} successfully returned bike to {}".format(student, location))
    elif any(command in body for command in ["station", "stations", "location", "locations"]):
        message = "Stations: PSA, Rodin, Ware, Fisher, Stouffer, Houston, and Hill (PSA=Penn Student Agencies). To return a bike text 'Checkin PSA' or another station."
    else:
        if student.can_ride:
            message = "Hi, {}! Checkout a bike: 'Checkout (number)'. Checkin: 'Checkin (location)'. Text 'stations' to view stations. You're eligible to checkout bikes.".format(student.name)
        else:
            currentRides = student.ride_set.filter(checkin_time=None)
            if len(currentRides) > 0:
                bike = currentRides[0].bike.bike_name
                message = "Hi {}! You still have {} out. Until you check it in, you cannot check out bikes. Text 'locations' for checkin stations.".format(student.name, bike)
            elif not student.waiver_signed:
                email_razzi("Waiver not signed by {}".format(student))
                message = "You need to fill out a waiver. Go to app.penncycle.org/waiver to do so."
            else:
                email_razzi("{} doesn't have any payments, it would seem. Contact him at {}".format(student.name, student.email))
                message = "You are currently unable to check out bikes. Go to penncycle.org and enter your penncard to check your status."
        if not any(command in body for command in ["help", "info", "information", "?"]):
            email_razzi(body)
    response.sms(message)
    return response
