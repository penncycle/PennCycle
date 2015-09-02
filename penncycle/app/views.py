import json
import datetime
from django.core.mail import send_mail
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, CreateView, UpdateView
from django.utils import timezone

from braces.views import LoginRequiredMixin

from .models import Student, Station, Bike, Payment, Plan, Info
from util.util import email_razzi, welcome_email, payment_email, email_managers, request_bike_email, email_user
from .forms import SignupForm, UpdateForm

#global variables
monthPrice = Plan.objects.get(name='Month Plan').cost
semesterPrice = Plan.objects.get(name='Semester Plan').cost
yearPrice = Plan.objects.get(name='Year Plan').cost

def lookup(request):
    penncard = request.GET.get("penncard")
    if Student.objects.filter(penncard=penncard).exists():
        messages.info(request, "Enter your PIN to add plans.")
        return HttpResponseRedirect('/signin/?penncard={}'.format(penncard))
    else:
        messages.info(request, "Fill out the form below to sign up!")
        return HttpResponseRedirect("/signup/?penncard={}".format(penncard))

def verify_pin(request):
    data = request.POST
    penncard = data.get('penncard')
    pin = data.get('pin')
    context = {}
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        messages.info(
            request,
            "No student with Penncard {} found. Sign up or email"
            "messenger@penncycle.org if you have already signed up.".format(penncard)
        )
        return HttpResponseRedirect('/signup?penncard={}'.format(penncard))
    if student.pin != pin:
        messages.error(
            request,
            "Your pin did not match. <a href='/send_pin/?penncard={}'>Click here</a> "
            "to send it to your email address.".format(penncard)
        )
        return render_to_response("signin.html", RequestContext(request, context))
    else:
        request.session['penncard'] = penncard
        return HttpResponseRedirect('/welcome/')


def welcome(request):
    penncard = request.session.get('penncard')
    try:
        student = Student.objects.get(penncard=penncard)
        # check if he has signed waiver
        if student.waiver_signed is False:
            return HttpResponseRedirect("/waiver/")
    except Student.DoesNotExist:
        return HttpResponseRedirect("/signin/")
    
    context = {
        "student": student,
        "current_payment": student.current_payment,
        "can_ride": student.can_ride,
        "monthPrice": monthPrice,
        "semesterPrice": semesterPrice,
        "yearPrice": yearPrice
    }
    return render_to_response("welcome.html", RequestContext(request, context))

def waiver(request):
    penncard = request.session.get('penncard')
    try:
        student = Student.objects.get(penncard=penncard)
        if student.waiver_signed is True:
            return HttpResponseRedirect('/welcome')
        else:
            return render_to_response('waiver_7-29-14.html', context_instance=RequestContext(request))
    except Student.DoesNotExist:
        return HttpResponseRedirect('/signin')
    



class Index(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = {
            "bikes": [{
                "name": bike.name,
                "status": bike.status,
                "location": bike.location.name,
                "latitude": bike.location.latitude,
                "longitude": bike.location.longitude
            } for bike in Bike.objects.all()],
            "monthPrice": monthPrice,
            "semesterPrice": semesterPrice,
            "yearPrice": yearPrice
        }
        return context


class Locations(TemplateView):
    template_name = 'locations.html'

    def get_context_data(self, **kwargs):
        return {
            'stations': Station.objects.filter(active="true")
        }


class Signup(CreateView):
    model = Student
    template_name = "signup.html"
    form_class = SignupForm

    def get_initial(self):
        return {
            'penncard': self.request.GET.get('penncard')
        }

    def form_valid(self, form):
        student = form.save()

        location = student.living_location

        if location in ["Ware", "Fisher"]:
            basic_plan = Plan.objects.get(name="Basic Plan")
            free_payment = Payment(
                student=student,
                amount=0,
                plan=basic_plan,
                payment_date=timezone.datetime.now(),
                end_date=timezone.datetime(year=2014, month=5, day=2),
                satisfied=True,
                payment_type="free",
            )
            free_payment.save()
            extra_info = ("Since you are a resident of {}, "
                "you automatically get a free basic plan which lasts "
                "until the end of the school year.").format(location)
            messages.info(self.request, extra_info)

        messages.info(self.request,
            "Your pin is {}. "
            "You will need it to log on in the future.".format(student.pin))
        
        # plan = Plan.objects.get(student)
        body = """
            {} has signed up for a PennCycle plan.
            You can reach him at {}.
        """.format(student.name, student.email)
        email_managers("New Signup", body)

        welcome_email(student)
        self.request.session['penncard'] = student.penncard
        return HttpResponseRedirect('/safety-overview/')

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(Signup, self).dispatch(*args, **kwargs)




@require_POST
@csrf_exempt
def verify_payment(request):
    payment = Payment.objects.get(id=request.POST.get('merchantDefinedData1'))
    # source = request.META.get('HTTP_REFERER')
    # source_needed = 'https://orderpage.ic3.com/hop/orderform.jsp'
    amount = str(request.POST.get('orderAmount', 0))
    cost_with_tax = float(payment.plan.cost)*1.08
    if float(amount) != cost_with_tax:
        email_razzi(
            "student didn't pay the right amount! Payment: {} "
            "Amount: {} Cost+tax: {}".format(payment.id, amount, cost_with_tax)
        )
        return HttpResponse('success')
    else:
        reasonCode = request.POST.get('reasonCode')
        good_reasons = [100, 200]
        if (int(reasonCode) in good_reasons):
            payment.satisfied = True
            payment.payment_type = 'credit'
            payment.payment_date = timezone.datetime.today()
            payment.save()
        return HttpResponse('success')


@csrf_exempt
@require_POST
def verify_waiver(request):
    penncard = request.session.get('penncard')
    try:
        student = Student.objects.get(penncard=penncard)
    except Student.DoesNotExist:
        return HttpResponse(json.dumps({"success": False}), content_type="application/json")
    student.waiver_signed = True
    student.save()
    return HttpResponse(json.dumps({"success": True}), content_type="application/json")

def process_data(data):
    datamap = {}
    datamap['student'] = Student.objects.get(penncard=data.get("penncard"))
    plan = Plan.objects.get(name=data.get("plan"))
    datamap['plan'] = plan
    datamap['renew'] = False
    end_date = None
    if (plan.name == "Month Plan"):
        end_date = timezone.datetime.now() + timezone.timedelta(days=31)
    elif (plan.name == "Semester Plan"):
        end_date = datetime.date(2015, 5, 10)
    elif (plan.name == "Year Plan"):
        end_date = datetime.date(2015, 12, 18)
    datamap['end_date'] = end_date
    datamap['renew'] = False
    return datamap
    
@require_POST
def bursar(request):
    data = request.POST
    datamap = process_data(data)
    student = datamap['student']
    plan = datamap['plan']
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        satisfied=True,
        payment_type="bursar",
        renew=datamap['renew'],
        end_date=datamap['end_date'],
        payment_date=timezone.datetime.now()
    )
    payment.save()
    message = '''
        Name: {}\n
        Penncard and last two digits: {} and {}\n
        Plan: {}\n
        Renew: {}\n
        Living location: {}\n

        Bursar them, and if there is a problem, notify Razzi.

        Thanks!
    '''.format(student.name, student.penncard, student.last_two, plan, datamap['renew'], student.living_location)
    send_mail(
        'Student Registered with Bursar',
        message,
        'messenger@penncycle.org',
        ['messenger@penncycle.org']
    )
    messages.info(request, "You have successfully paid by Bursar!")
    payment_email(student)
    return HttpResponse("success")


@require_POST
def credit(request):
    data = request.POST
    datamap = process_data(data)
    student = datamap['student']
    plan = datamap['plan']
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        satisfied=False,
        payment_type="credit",
        renew=datamap['renew'],
        end_date=datamap['end_date']
    )
    payment.save()
    payment_email(student)
    return HttpResponse(payment.id)


@require_POST
def cash(request):
    data = request.POST
    datamap = process_data(data)
    student = datamap['student']
    plan = datamap['plan']
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        payment_date=timezone.datetime.today(),
        satisfied=True,
        payment_type="cash",
        renew=datamap['renew'],
        end_date=datamap['end_date']
    )
    payment.save()
    messages.info(request, "Your payment has been processed. Please come to Penn"
        "Student Agencies and pay at the front desk.")
    payment_email(student)
    return HttpResponse("success")

@require_POST
def bike_request(request):
    data = request.POST
    student = Student.objects.get(penncard=data.get("penncard"))
    approx_height = data.get("approx_height")
    bike_type = data.get("bike_type")
    available_time = data.get("available_time")

    current_payment = student.current_payment
    plan_info = ""
    if (current_payment):
        plan_info = "{}, expiring on {}".format(current_payment.plan.name, current_payment.end_date.strftime("%m/%d/%y"))
    else:
        plan_info = "You currently don't have a plan. Please purchase a plan when you collect your bike."
    plan_info += """
Dear {},

New PennCycle Bike request with the following info:

Approximate height: {}
Bike type: {}
Available times to collect bike from Quaker Corner: {}
Current Plan: {}
    """.format(student.name, approx_height, bike_type, available_time, plan_info)
    email_managers("New PennCycle Bike request", plan_info)

    request_bike_email(bike_type, approx_height, available_time, student)
    return HttpResponse('success')
    
@require_POST
def group_ride_request(request):
    data = request.POST
    student_name = data.get("student_name")
    organization = data.get("organization")
    position_in_organization = data.get("position_in_organization")
    email = data.get("email")
    destination_of_ride = data.get("destination_of_ride")
    approximate_duration = data.get("approximate_duration")
    total_bikes = data.get("total_bikes")
    require_pc_representative = data.get("require_pc_representative")
    subject = "Group Ride Request"
    
    # message to bike manager
    body = """
    New Group Ride Request with the following information:
    
        Student Name: {}
        Organization: {}
        Position in Organization: {}
        Email: {}
        Destination of Ride: {}
        Approximate Duration: {}
        Total number of Bikes: {}
        Does the group require a PennCycle represntative? {}

        """.format(student_name, organization, position_in_organization, email, destination_of_ride, approximate_duration, total_bikes, require_pc_representative)
    email_managers(subject, body)
    
    # message to user
    body = """
    Your group ride request to {} for {} bikes is under process. PennCycle will get back to you at the earliest.

    Thanks for using PennCycle.

    Have a question, concern, or suggestion? Email us at messenger@penncycle.org.

    Happy Cycling!

    The PennCycle Team.
    """.format(destination_of_ride, total_bikes)
    email_user(subject, body, email)
    return HttpResponse("success")

class Stats(LoginRequiredMixin, TemplateView):
    template_name = "stats.html"


@login_required
def combo(request):
    bikes = Bike.objects.all()
    bikes = reversed(sorted(bikes, key=lambda x: int(x.name)))
    context = {'bikes': bikes}
    if request.method == "POST":
        combo = request.POST.get("combo")
        if not combo:
            messages.info(request, "Enter a combo. Nothing changed.")
            return render_to_response("combo.html", RequestContext(request, context))
        bike = request.POST.get("bike")
        bike = Bike.objects.get(id=bike)
        bike.combo = combo
        log = Info(message="Bike {} had combo {} and is now {}".format(bike, bike.combo, combo))
        log.save()
        bike.combo_update = timezone.datetime.today()
        bike.save()
        messages.info(request, "Changed combo to {}".format(bike.combo))
    return render_to_response("combo.html", RequestContext(request, context))

@require_POST
def modify_payment(request):
    data = request.POST
    payment = Payment.objects.get(id=data.get("id"))
    if data.get("action") == "delete":
        payment.delete()
        return HttpResponse("success")
    elif data.get("action") == "renew":
        payment.renew = True
    else:
        payment.renew = False
    payment.save()
    return HttpResponse("success")

class StudentUpdate(UpdateView):
    model = Student
    form_class = UpdateForm
    template_name = "update_student.html"
    success_url = "/update/"

    def get_object(self, queryset=None):
        return Student.objects.get(penncard=self.request.session.get("penncard"))

    def form_valid(self, form):
        messages.info(self.request, "Successfully updated info.")
        return super(StudentUpdate, self).form_valid(form)

class Bikes(TemplateView):
    template_name = 'bikes.html'

    def get_context_data(self):
        context = super(Bikes, self).get_context_data()
        stations = Station.objects.filter(active=True)
        bike_set = set()
        for s in stations:
            bike_set.update(set(s.bikes.filter(status="available")))
            
        context['bikes'] = bike_set
        return context


@csrf_exempt
def thanks(request):
    return render_to_response(
        'thanks.html',
        RequestContext(request, {})
    )
