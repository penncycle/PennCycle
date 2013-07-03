# import re
# import datetime
import json

from django.core.mail import send_mail
from app.models import Student, Bike, Ride  # , Station
from django.http import HttpResponse

import twilio.twiml
from django.views.generic import TemplateView


def email_razzi(message):
    send_mail('an important email from the PennCycle app', str(message), 'messenger@penncycle.org', ['razzi53@gmail.com'], fail_silently=True)


def check_for_student(request):
    number = request.POST.get("number")
    if not number or len(number) not in (8, 10, 12):
        return HttpResponse("failure")
    if len(number) == 8:
        if not Student.objects.filter(penncard=number):
            return HttpResponse("failure")
        else:
            student = Student.objects.get(penncard=number)
    elif len(number) in (10, 12):
        if len(number) == 10:
            number = number[0:3] + "-" + number[3:6] + "-" + number[6:]
        if not Student.objects.filter(phone=number):
            return HttpResponse("failure")
        else:
            student = Student.objects.get(phone=number)
    email_razzi("Student matched with number {}".format(number))
    data = {
        "student": student.name
    }
    return HttpResponse(json.dumps(data), mimetype="application/json")


class Signup(TemplateView):
    template_name = "index.html"

# def info_submit(request):
#     form = SignupForm(request.POST)
#     if form.is_valid():
#         form.save()
#         reply = {
#             'success': True,
#             'form_valid': True
#         }
#     else:
#         reply = {
#             'success': True,
#             'form_valid': False,
#             'new_form': str(form)
#         }
#     return HttpResponse(json.dumps(reply), content_type="application/json")


def verify(response):
    data = response.POST
    try:
        student = Student.objects.get(phone=data.phone)
    except Student.DoesNotExist:
        return "goto signup"
    if student.pin != data.pin:
        return "bad pin"


def send_pin(phone_number):
    student = Student.objects.get(phone=phone_number)
    pin = student.pin
    return "fix mess"
