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
from util.util import email_razzi, welcome_email, payment_email, send_welcome_text
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
            "to resend it to {}.".format(penncard, student.phone)
        )
        return render_to_response("signin.html", RequestContext(request, context))
    else:
        request.session['penncard'] = penncard
        return HttpResponseRedirect('/welcome/')


def welcome(request):
    penncard = request.session.get('penncard')
    try:
        student = Student.objects.get(penncard=penncard)
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


class Index(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = {
            "bikes": [
            {
                "name": bike.name,
                "status": bike.status,
                "location": bike.location.name,
                "latitude": bike.location.latitude,
                "longitude": bike.location.longitude
            } for bike in Bike.objects.all()],
            "monthPrice": monthPrice, 
            "semesterPrice": semesterPrice
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


        welcome_email(student)
        send_welcome_text(student)
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


@require_POST
def bursar(request):
    data = request.POST
    student = Student.objects.get(penncard=data.get("penncard"))
    plan_element_id = data.get("plan")
    plan = plan_element_id.replace("_", " ").title()
    plan = Plan.objects.get(name=plan)
    renew = data.get("renew")
    end_date = None
    if (plan.name == "Semester Plan"):
        end_date = datetime.date(2015, 5, 10)
    elif (plan.name == "Year Plan"):
        end_date = datetime.date(2015, 12, 18)
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        satisfied=True,
        payment_type="bursar",
        renew=renew,
        end_date=end_date,
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
    '''.format(student.name, student.penncard, student.last_two, plan, renew, student.living_location)
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
    student = Student.objects.get(penncard=data.get("penncard"))
    plan_element_id = data.get("plan")
    plan = plan_element_id.replace("_", " ").title()
    plan = Plan.objects.get(name=plan)
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        satisfied=False,
        payment_type="credit",
    )
    payment.save()
    payment_email(student)
    return HttpResponse(payment.id)


@require_POST
def cash(request):
    data = request.POST
    student = Student.objects.get(penncard=data.get("penncard"))
    plan_element_id = data.get("plan")
    plan = plan_element_id.replace("_", " ").title()
    plan = Plan.objects.get(name=plan)
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        purchase_date=timezone.datetime.today(),
        satisfied=False,
        payment_type="cash",
    )
    payment.save()
    messages.info(request, "Your payment has been processed. Please come to Penn"
        "Student Agencies and pay at the front desk.")
    payment_email(student)
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
        bike_set = set();
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
