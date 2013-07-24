import datetime
import json

from django.core.mail import send_mail
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, CreateView
from django import forms

from braces.views import LoginRequiredMixin

from crispy_forms.layout import Layout, Submit, Div, Field
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineRadios

from models import *
from util.util import email_razzi

class SignupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Field(
                        'penncard',
                        placeholder="8 digits",
                    ),
                    'name',
                    'phone',
                    'email', css_class="span5 offset1"
                ), Div(
                    Field(
                        'last_two',
                        placeholder="Usually 00"
                    ),
                    'grad_year',
                    'living_location',
                    InlineRadios('gender'), css_class="span6"
                ), css_class="row-fluid"
            )
        )
        self.helper.form_action = '/signup/'
        self.helper.add_input(Submit('submit', "Submit"))
        self.helper.form_method = 'post'
        self.fields['last_two'].label = "Last two digits of PennCard"
        self.fields['penncard'].label = "PennCard Number"

    class Meta:
        model = Student
        fields = [
            'penncard',
            'name',
            'phone',
            'email',
            'last_two',
            'grad_year',
            'living_location',
            'gender',
        ]

    gender = forms.TypedChoiceField(
        choices=(("M", "Male"), ("F", "Female")),
    )


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
        email_razzi("Strangely, a student dne on welcome. {}".format(penncard))
        return HttpResponseRedirect("/signin/")
    context = {
        "student": student
    }
    return render_to_response("welcome.html", RequestContext(request, context))


class Index(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        psa = Station.objects.get(name="PSA")
        count = Bike.objects.filter(location=psa).filter(status="available").count()
        context = {
            'psa_count': count
        }
        return context


class Faq(TemplateView):
    template_name = 'faq.html'


class Safety(TemplateView):
    template_name = 'safety.html'


class Team(TemplateView):
    template_name = 'team.html'


class Locations(TemplateView):
    template_name = 'locations.html'

    def get_context_data(self, **kwargs):
        context = {
            'stations': Station.objects.order_by("id")
        }
        return context


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
        messages.info(self.request,
            "Your pin is {}. "
            "You will need it to log on in the future.".format(student.pin)
        )
        self.request.session['penncard'] = student.penncard
        return HttpResponseRedirect('/welcome/')


@require_POST
@csrf_exempt
def verify_payment(request):
    email_razzi(request.POST)
    payment = Payment.objects.get(id=request.POST.get('merchantDefinedData1'))
    # source = request.META.get('HTTP_REFERER')
    # source_needed = 'https://orderpage.ic3.com/hop/orderform.jsp'
    amount = str(request.POST.get('orderAmount', 0))
    cost_with_tax = float(payment.plan.cost)*1.08
    if float(amount) != cost_with_tax:
        errmessage = "student didn't pay the right amount! Payment: {} \n Amount: {} Cost+tax: {}".format(payment.id, amount, costwtax)
        email_razzi(errmessage)
        return HttpResponse('success')
    else:
        reasonCode = request.POST.get('reasonCode')
        good_reasons = [100, 200]
        if (int(reasonCode) in good_reasons):
            payment.satisfied = True
            payment.payment_type = 'credit'
            payment.payment_date = datetime.datetime.today()
            payment.save()
        return HttpResponse('success')


@require_POST
def verify_waiver(request):
    pennid = request.POST.get('pennid')
    student = Student.objects.get(penncard=pennid)
    student.waiver_signed = True
    student.save()
    return HttpResponse(json.dumps({'message': 'success'}), content_type="application/json")


@require_POST
def bursar(request):
    data = request.POST
    student = Student.objects.get(penncard=data.get("penncard"))
    plan_element_id = data.get("plan")
    plan = plan_element_id.replace("_", " ").title()
    plan = Plan.objects.get(name=plan)
    renew = data.get("renew")
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        purchase_date=datetime.datetime.today(),
        satisfied=True,
        payment_type="bursar",
    )
    payment.save()
    message = '''
        Name: {}\n
        Penncard and last two digits: {} and {}\n
        Plan: {}\n
        Renew: {}\n

        Bursar them, and if there is a problem, notify Razzi.

        Thanks!
    '''.format(student.name, student.penncard, student.last_two, plan, renew)
    send_mail(
        'Student Registered with Bursar',
        message,
        'messenger@penncycle.org',
        ['messenger@penncycle.org']
    )
    messages.info(request, "You have successfully paid by Bursar!")
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
        purchase_date=datetime.datetime.today(),
        satisfied=False,
        payment_type="credit",
    )
    payment.save()
    return HttpResponse(payment.id)


@require_POST
def cash(request):
    data = request.POST
    student = Student.objects.get(penncard=data.get(penncard))
    plan_element_id = data.get("plan")
    plan = plan_element_id.replace("_", " ").title()
    plan = Plan.objects.get(name=plan)
    payment = Payment(
        amount=plan.cost,
        plan=plan,
        student=student,
        purchase_date=datetime.datetime.today(),
        satisfied=False,
        payment_type="cash",
    )
    payment.save()
    messages.info("Your payment has been processed. Please come to Penn"
        "Student Agencies and pay at the front desk.")
    return HttpResponse("success")

class Stats(LoginRequiredMixin, TemplateView):
    template_name = "stats.html"


@login_required
def combo(request):
    if request.method == "POST":
        data = request.POST
        bike = data.get("bike")
        bike = Bike.objects.get(id=bike)
        log = Info(message="Bike {} had combo {} and is now {}".format(bike, bike.combo, data.get("combo")))
        log.save()
        bike.combo = data.get("combo")
        bike.combo_update = datetime.datetime.today()
        bike.save()
    context = {
        'bikes': Bike.objects.all()
    }
    context_instance = RequestContext(request, context)
    return render_to_response("combo.html", context_instance)
