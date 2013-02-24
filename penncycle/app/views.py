from django.core.mail import send_mail
from app.models import *
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django import forms
from django.views.decorators.csrf import csrf_exempt
from bootstrap.forms import BootstrapModelForm, Fieldset
import random, json, hashlib, hmac, gviz_api
from django.contrib.auth.decorators import login_required
import datetime
import twilio.twiml
from django_twilio.decorators import twilio_view
import re

class SignupForm(BootstrapModelForm):
  class Meta:
    model = Student
    exclude = ('join_date', 
                'status', 
                'waiver_signed', 
                'paid', 
                'last_two', 
                'payment_type', 
                'at_desk',
                'plan',
                'major',
                )

class InfoSubmitForm(forms.ModelForm):
  class Meta:
    model = Student
    exclude = ('join_date', 
                'status', 
                'waiver_signed', 
                'paid',)

def pages():
  pages = [
    {'name':'Home','url':'/'},
    {'name':'Plans','url':'/plans/'},
    {'name':'Sign Up','url':'/signup/'},
    {'name':'Safety', 'url':'/safety/'},
    {'name':'Team', 'url':'/team/'},
    {'name':'Partners', 'url':'/partners/'},
    # {'name':'Events', 'url':'/events/'},
    {'name':'Locations', 'url':'/locations/'},
    {'name':'FAQ', 'url':'/faq/'},
    ]
  # for page in Page.objects.all():
  #   pages.append({
  #     'name': page.name,
  #     'url': '/about/%s/' % page.slug
  #     })
  return pages

def index(request):
  available = Bike.objects.filter(status='available')
  stoufferCount = sum((1 for bike in available if bike.location.name == "Stouffer"))
  psaCount = sum((1 for bike in available if bike.location.name == "PSA / Houston"))
  rodinCount = sum((1 for bike in available if bike.location.name == "Rodin"))
  wareCount = sum((1 for bike in available if bike.location.name == "Ware"))
  fisherCount = sum((1 for bike in available if bike.location.name == "Fisher"))
  context = {
    'available': available,
    'stoufferCount': stoufferCount,
    'rodinCount':rodinCount,
    'psaCount': psaCount,
    'wareCount': wareCount,
    'fisherCount': fisherCount,
    'pages':pages()
  }
  return render_to_response('index.html', context)

def faq(request):
  context = {
    'pages':pages()
  }
  return render_to_response('faq.html', context)

def safety(request):
  context = {
    'pages':pages()
  }
  return render_to_response('safety.html', context)

def team(request):
  context = {
    'pages':pages()
  }
  return render_to_response('team.html', context)

def partners(request):
  context = {
    'pages':pages()
  }
  return render_to_response('partners.html', context)

# def events(request):
#   context = {
#     'pages':pages()
#   }
#   return render_to_response('events.html', context)

def locations(request):
  context = {
    'pages':pages(),
    'stations':Station.objects.filter(capacity__gt=0)
  }
  return render_to_response('locations.html', context)


def info_submit(request):
  if request.method == 'POST':
    print "its a post!"
    form = SignupForm(request.POST)
    print form
    if form.is_valid():
      print "shit is validd"
      student = form.save()
      living_location = student.living_location
      if living_location in ['Fisher', 'Ware']: 
        payment = Payment(
          amount=0,
          plan=Plan.objects.filter(name="Spring Basic 2013").exclude(name__contains='Unlimited', end_date__lt=datetime.date.today()).order_by('start_date')[0],
          student=student,
          satisfied=True,
          payment_type='pre-paid',
          )
        payment.save()
        message = '''
        student name: %s
        student penncard: %s
        payment: %s
        living_location: %s

        tell alex if you want more info in this email
        ''' % (student.name, student.penncard, payment, living_location)
        send_mail('quaddie signed up', message, 'messenger@penncycle.org', ['messenger@penncycle.org'], fail_silently=True)
        print "this student lives in %s" % living_location
        print str(student) + "; paid = " + str(student.paid)
      print "saved form"
      print "payment plan: " + str(student.plan)
      reply = {'success': True, 'form_valid': True}
    else:
      print "INVALID bullshit"
      reply = {'success': True,
               'form_valid': False,
               'new_form': str(form)}
    print reply
    return HttpResponse(json.dumps(reply), content_type="application/json")
  else:
    return HttpResponse("You have reached this page in error. Please contact messenger@penncycle.org with details on how you got here.")
      
def page(request, slug):
  page = get_object_or_404(Page, slug=slug)
  context = {'page':page}
  context.update({'pages':pages()})
  return render_to_response('page.html', context)

def signup(request):
  if request.method == 'POST':
    form = SignupForm(request.POST)
    if form.is_valid():
      # Process the data in form.cleaned data
      form.save()
      return HttpResponse('ok')
      #return render_to_response('thanks.html', {})
  else:
    form = SignupForm()

  safety_info = Page.objects.get(slug='safety')
  
  context = {
      'safety_info': safety_info,
      'form': form,
      'plans': Plan.objects.filter(end_date__gte = datetime.date.today(), cost__gt = 0)
  }
  context.update({'pages':pages()})
  context_instance = RequestContext(request, context)
  return render_to_response('signup.html', context_instance)

@csrf_exempt
def verify_payment(request):
  if request.method=='POST':
    print "in verify_payment"
    email_razzi(request.POST)
    # gets the student with penncard specified in POST data
    payment = Payment.objects.get(id=request.POST.get('merchantDefinedData1'))
    student = payment.student
    print payment
    print student

    source = request.META.get('HTTP_REFERER')
    print 'referrer is %s ' % unicode(source)
    source_needed = 'https://orderpage.ic3.com/hop/orderform.jsp'
    
    amount = str(request.POST.get('orderAmount', 0))
    print amount
    costwtax = float(payment.plan.cost)*1.08
    print costwtax

    if float(amount) != costwtax:
      errmessage = 'student didn\'t pay the right amount! Payment: %s \n Amount: %d Cost+tax: %d' % (str(payment.id), float(amount),  costwtax)
      print errmessage
      email_razzi(errmessage)
      return HttpResponse('eh okay.')
    else:
      # if source matches CyberSource, payment completed
      #if source == source_needed and (int(request.POST.get('reasonCode')) == (100 or 200)) and amount == .01:
      reasonCode = request.POST.get('reasonCode')
      good_reasons = [100,200]
      print reasonCode
      #if (int(reasonCode) in good_reasons) and (amount == '10.00' or amount == '10'):
      if (int(reasonCode) in good_reasons): 
        print "check passed"
        #student.paid = True
        payment.satisfied=True
        payment.payment_type = 'credit'
        payment.save()
        print "paid"
      return HttpResponse('Verified!')
  else:
    return HttpResponse('Not a POST')

@csrf_exempt
def thankyou(request, payment_id):
  print "in thanks view"
  try:
    payment = Payment.objects.get(id=payment_id)
    student = payment.student
  except:
    student = get_object_or_404(Student, penncard=payment_id)
  #student = Student.objects.get(penncard=request.POST.get('merchantDefinedData1'))
  print student
  type = request.GET.get('type', 'credit')
  if type == 'penncash' or type == 'bursar':
    message = '''Please allow up to 48 hours for your payment to be registered.
    </p><p> You can start checking out bikes immediately in the meantime. Visit our <a href="/locations">locations</a> page
    to view our stations and their hours.'''
  elif type == 'cash':
    message = "Once you've paid and your payment has been registered, you'll be good to go!"
  elif type == "credit":
    if payment.satisfied == True:
      message = 'You\'re ready to ride!'
    else:
      message = 'Something went wrong with your payment. We\'ve been notified and will get on this right away.'
      try:
        dog = payment.id
        email_razzi('payment gone wrong! %s' % str(payment.id))
      except:
        email_razzi('payment gone HORRIBLY wrong! (could not email you what the payment id was!) student is %s' % student)
  else:
    message = 'Something went wrong with your payment. Please email us at messenger@penncycle.org.'
  return render_to_response('thanks.html', {'message':message, 'pages':pages()})

def verify_waiver(request):
  print 'in verify_waiver'
  if request.method=='POST':
    print 'its a post'
    pennid = request.POST.get('pennid')
    print pennid
    student = Student.objects.get(penncard=pennid)
    print student
    student.waiver_signed = True
    student.save()
    print 'waiver signed'
    return HttpResponse(json.dumps({'message': 'success'}), content_type="application/json")
  return HttpResponse('failure')

def pay(request, type, penncard, plan):
  if request.method == 'POST':
    type = str(request.POST.get('type')).lower()
    try:
      student = Student.objects.get(penncard=penncard) # verify form is filled out well!
    except:
      context = {
      'message': "No student matching that PennCard was found. Please try again, or sign up.",
      'type': type,
      'pages': pages()
      }
      return render_to_response("pay.html", RequestContext(request, context))
    last_two = request.POST.get('last_two')
    student.last_two = last_two
    student.save()
    plan = get_object_or_404(Plan, id=plan)
    payment = Payment(
      amount=plan.cost,
      plan=plan,
      student=student,
      date=datetime.datetime.today(),
      satisfied=True,
      payment_type=type,
    )
    payment.save()
    message = '''
      Name: %s \n
      PennCard: %s \n
      Last Two Digits: %s \n
      Type: %s \n
      Plan: %s \n
      
      Chris and Razzi deciced that it would be easier for students to have the ability
      to check out bikes immediately, so that students wouldn't have
      to wait for us to bill them and in case we forget, they can still ride. 

      It is still necessary to bill them, and if this has a problem, go to the admin interface and remove their
      payment, then email them with what went wrong.

      Email razzi53@gmail.com if something goes wrong.

      Thanks!
    ''' % (student.name, student.penncard, student.last_two, type, plan)
    send_mail('Student Registered w/ %s' % (type), message, 
      'messenger@penncycle.org', ['messenger@penncycle.org'], fail_silently=False)
    return HttpResponseRedirect('/thankyou/%s/?type=%s' % (penncard, type))
  else: 
    try:
      student = Student.objects.get(penncard=penncard) # verify form is filled out well!
      context = {
        'type': type,
        'penncard': penncard,
        'student': student,
        'pages': pages(),
      }
    except:
      context = {
        'type': type,
        'penncard': penncard,
        'pages': pages(),
        'message': "No student matching that PennCard was found. <a href='/signup'>Sign up</a> here.",
      }
    return render_to_response('pay.html', RequestContext(request, context))

@login_required
def stats(request):
  return render_to_response('stats.html', {'pages':pages()})

def selectpayment(request):
  plans = Plan.objects.filter(end_date__gte = datetime.date.today(), cost__gt = 0)
  print plans
  day_plan = Plan.objects.filter(end_date=datetime.date.today(), name__contains='Day Plan')
  if len(day_plan) < 1:
    print 'about to create a new day plan'
    day_plan = Plan(
      name = 'Day Plan %s' % str(datetime.date.today()),
      cost = 10,
      start_date = datetime.date.today(),
      end_date = datetime.date.today(),
      description = 'A great way to try out PennCycle. Or, use this to check out a bike for a friend or family member! Add more day plans to your account to check out more bikes. Day plans can only be purchased day-of.',
      )
    day_plan.save()
  elif len(day_plan) == 1:
    print 'there already was a day plan! how convenient.'
  print day_plan
  return render_to_response('selectpayment.html', {'plans': plans, 'pages':pages()})

def addpayment(request):
  print "in addpayment view"
  print request.POST
  pennid = unicode(request.POST.get('pennid'))
  print "pennid = " + str(pennid)
  try:
    associated_student = Student.objects.get(penncard=pennid)
  except:
    raise LookupError
  print associated_student
  plan_num = int(request.POST.get('plan'))
  print "plan num = " + str(plan_num)
  associated_plan = Plan.objects.get(pk=plan_num)
  print associated_plan
  new_payment = Payment(amount=associated_plan.cost, plan=associated_plan, student=associated_student)
  print new_payment
  new_payment.save()
  print "payment saved"

  return HttpResponse(json.dumps({'message': 'success', 'payment_id':str(new_payment.id)}), content_type="application/json")

def plans(request):
  print "hit plans view"
  # list of dicts
  plans = [] 
  for p in Plan.objects.filter(end_date__gte=datetime.date.today(), cost__gt=0).order_by('start_date', 'cost'):
    plans.append({'name': str(p), 'description': p.description, 'start_date': p.start_date, 'end_date': p.end_date,})
  context = {
      'plans': plans,
      'pages': pages(),
  }
  print plans
  return render_to_response('plans.html', context)

def email_razzi(message):
  send_mail('an important email from the PennCycle App', str(message), 'messenger@penncycle.org', ['razzi53@gmail.com'], fail_silently=True)

@twilio_view
def sms(request):
  if request.method=="POST":
    response = twilio.twiml.Response()
    fromNumber = request.POST.get("From", "None")
    number = fromNumber[2:]
    lookup = number[0:3]+"-"+number[3:6]+"-"+number[6:]
    try:
      student = Student.objects.get(phone=lookup)
      if not student.can_ride:
        message = "Hi {}! You are currently unable to checkout bikes. Visit app.penncycle.org and go to returning members to fix this.".format(student.name)
        response.sms(message)
        return response
    except:
      message = "Welcome to PennCycle! Visit app.penncycle.org to get started. Signup for the unlimited plan to check out bikes by texting."
      response.sms(message)
      return response
    body = request.POST.get("Body", "").lower()
    email_razzi(body)
    if any(command in body for command in ["return", "checkout"]):
      try:
        bikeNumber = re.search("\d+", body).group()
      except:
        response.sms("Command not understood. Example of checking out a bike would be: Checkout 10")
      try:
        bike = Bike.objects.get(id=int(bikeNumber))
        ride = Ride(rider=student, bike=bike, checkout_station=bike.location)
        ride.save()
        message = "You have successfully checked out bike {}. The combination is 1005. To return the bike, reply 'checkin PSA' (or any other station). Text 'Stations' for a list.".format(bikeNumber)
        response.sms(message)
      except:
        message = "The bike you have requested was not found. Text 'Checkout (number)', where number is 1 or 2 digits."
        response.sms(message)
    elif "checkin" in body:
      location = None
      stations = [station.name for station in Station.objects.all()]
      for station in stations:
        if station in body:
          location = Station.objects.get(name=station)
      if not location:
        email_razzi("Station didn't match for checkin. Message was {}".format(body))
        message = "Station not found. Options: PSA, Rodin, Ware, Fisher, Stouffer, Houston, Hill (PSA=Penn Student Agencies). To return a bike text 'Checkin PSA' or another station."
      ride = student.ride_set.all()[len(student.ride_set.all())-1]
      ride.checkin_time = datetime.datetime.now()
      ride.checkin_station = location
      ride.save()
      message = "You have successfully returned your bike at {}. Make sure it is locked, and we will confirm the bike's checkin location shorty. Thanks!"
      response.sms(message)
      email_razzi("Bike {} successfully returned! Ride was {}".format(ride, ride.bike))
    elif any(command in body for command in ["station", "stations", "location", "locations"]):
      message = "Stations: PSA, Rodin, Ware, Fisher, Stouffer, Houston, and Hill (PSA=Penn Student Agencies). To return a bike text 'Checkin PSA' or another station."
      response.sms(message)
    else:
      message = "Hi, {}! Checkout a bike: 'Checkout (number)'. Checkin: 'Checkin (location)'. Text 'stations' to view stations. You're eligible to checkout bikes.".format(student.name)
      response.sms(message)
      if not "help" in body:
        email_razzi(body)
    return response

@twilio_view
def debug(request):
  try:
    email_razzi(request.GET)
  except:
    email_razzi("Problem with debug.")
  return HttpResponse("Ok")

@login_required  
def combo(request):
  context = {
    'pages': pages(),
    'bikes': Bike.objects.all()
  }
  context_instance = RequestContext(request, context)
  return render_to_response("combo.html", context_instance)

def updateCombo(request):
  print("updating combo")
  data = request.POST
  bike = data.get("bike")
  bike = Bike.objects.get(id=bike)
  bike.combo = data.get("combo")
  print(data.get("combo"))
  bike.combo_update = datetime.datetime.today()
  bike.save()
  context = {
    'pages': pages(),
    'bikes': Bike.objects.all()
  }
  context_instance = RequestContext(request, context)
  return render_to_response("combo.html", context_instance)
