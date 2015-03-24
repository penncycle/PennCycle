from django.core.mail import send_mail, EmailMultiAlternatives
from django_twilio.client import twilio_client


def send_pin_to_student(student):
    subject = "Welcome to PennCycle"
    from_email = "messenger@penncycle.org"
    to_email = student.email
    text_content = """
Your PennCycle PIN is {}. You can use it to log in at penncycle.org/login. 
    """.format(student.pin)
    html_content = """
<p>Your PennCycle PIN is {}. You can use it to <a href="http://www.penncycle.org/login">log in</a> at penncycle.org.</p>
    """.format(student.pin)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def email_razzi(message):
    send_mail(
        'PennCycle: {}'.format(
            message[:30].replace("\n", " ")
        ),
        message,
        'messenger@penncycle.org', ['razzi53@gmail.com'],
        fail_silently=True
    )

def email_shashank(subject, body):
    send_mail(
        subject,
        body,
        'am.seshank@gmail.com',
        fail_silently=True
    )

def email_managers(subject, body):
    send_mail(
        subject,
        body,
        'messenger@penncycle.org', ['messenger@penncycle.org'],
        fail_silently=True
    )

def welcome_email(student):
    subject = "Welcome to PennCycle"
    from_email = "messenger@penncycle.org"
    to_email = student.email
    text_content = """
Thanks for joining PennCycle.

Your PennCycle PIN is {}. You can use it to log in at penncycle.org/login. 

To ride, you first need to purchase a PennCycle plan, either online or in-person at Quaker Corner. Then visit us at Quaker Corner to check-out a bike. Helmets are required for riding and can also be rented or purchased at Quaker Corner.

Quaker Corner is open Monday - Friday, 10 am - 6 pm.

Have a question, concern, or suggestion? Email us at messenger@penncycle.org.

Happy Cycling!

The PennCycle Team
    """.format(student.pin)
    html_content = """
<p>Thanks for joining PennCycle.</p>

<p>Your PennCycle PIN is {}. You can use it to <a href="http://www.penncycle.org/login">log in</a> at penncycle.org.</p>

<p>To ride, you first need to purchase a PennCycle plan, either online or in-person at <a href='http://www.penncycle.org/about'>Quaker Corner</a>. Then visit us at Quaker Corner to check-out a bike. Helmets are required for riding and can also be rented or purchased at Quaker Corner.</p>

<p>Quaker Corner is open Monday - Friday, 10 am - 6 pm.</p>

<p>Have a question, concern, or suggestion? Email us at messenger@penncycle.org.</p>

<p>Happy Cycling!</p>

<p>The PennCycle Team</p>
    """.format(student.pin)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def renewal_email(student, payment):
    subject = "Your PennCycle plan will expire soon"
    from_email = "messenger@penncycle.org"
    to_email = student.email
    text_content = """
Dear {},

Your monthly PennCycle membership will expire on {}!

To keep riding, purchase a new plan at www.penncycle.org or in-person at Quaker Corner.

We hope you have enjoyed PennCycle. Please let us know if you have any questions or if we can help you out in any way.

Thanks! Keep on pedaling!

Bobby and the PennCycle Team
""".format(student.name, payment.end_date.strftime("%B %d"))
    html_content = """
<p>Dear {},</p>

<p>Your monthly PennCycle membership will expire on {}!</p>

<p>To keep riding, purchase a new plan at <a href='http://www.penncycle.org'>www.penncycle.org</a> or in-person at <a href='http://www.penncycle.org/about'>Quaker Corner</a>.</p>

<p>We hope you have enjoyed PennCycle. Please let us know if you have any questions or if we can help you out in any way. </p>

<p>Thanks! Keep on pedaling!</p>

<p>Bobby and the PennCycle Team</p>
""".format(student.name, payment.end_date.strftime("%B %d"))
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def payment_email(student):
    subject = "Thanks For Purchasing a PennCycle Membership"
    from_email = "messenger@penncycle.org"
    to_email = student.email
    text_content = """
Dear {},

Thank you for signing up for a PennCycle plan! Once your payment is processed, you will be eligible to check out PennCycles from Quaker Corner.

While using PennCycle, keep the following in mind:

1. Before riding do an ABC Check (Air in Tires, Brakes, Chain)

2. If your tires feel flat you can pump them up at the bike racks to the next to Pottruck, by the Chemistry Building, and at Quaker Corner, or email us at messenger@penncycle.org and we'll pump them up for you!

3. Always lock up your bike properly! See the attached picture of a properly locked bike. Ensure the lock goes through the rack, the front wheel and a sturdy part of the frame. If you can't include the front wheel, be sure to include the frame. PennCycle will charge a $5 fee for an improperly locked bike. Never lock your bike to a garbage can, or bench.

We hope that you enjoy your PennCycle experience!

Happy Cycling!

Bobby and the PennCycle Team
""".format(student.name)
    html_content = """
<p>Dear {},</p>

<p>Thank you for signing up for a PennCycle plan! Once your payment is processed, you will be eligible to check out PennCycles from Quaker Corner.</p>

<p>While using PennCycle, keep the following in mind:</p>
<ol>
    <li>Before riding do an ABC Check (Air in Tires, Brakes, Chain)</li>

    <li>If your tires feel flat you can pump them up at the bike racks to the next to Pottruck, by the Chemistry Building, and at Quaker Corner, or email us at messenger@penncycle.org and we'll pump them up for you!</li>

    <li><b>Always lock up your bike properly!</b> See the attached picture of a properly locked bike. Ensure the lock goes through the rack, the front wheel and a sturdy part of the frame. If you can't include the front wheel, be sure to include the frame. PennCycle will charge a $5 fee for an improperly locked bike. Never lock your bike to a garbage can, or bench.</li>
</ol>

<p>We hope that you enjoy your PennCycle experience!</p>

<p>Happy cycling!</p>

<p>The PennCycle Team</p>""".format(student.name)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.attach_file("penncycle/static/img/locked_bike.png")
    msg.send()


def renewed_email(payment, old_end_date):
    context = {
        "name": payment.student.name,
        "plan": payment.plan.name,
        "expire_date": payment.end_date,
        "old_end_date": old_end_date
    }
    content = """
Dear {name},

We hope you have been enjoying PennCycle! Your {plan}, which was set to expire on {old_end_date}, has been renewed by bursar and will end on {expire_date}.

If you have any questions, or if you believe this message was in error, please email messenger@penncycle.org and we will sort it out.

Happy cycling!

The PennCycle Team
""".format(**context)
    send_mail(
        "Your PennCycle Plan has been Renewed",
        content,
        "messenger@penncycle.org", [payment.student.email]
    )


def feedback_email(message, penncard, student=None):
    if not student:
        # In case the student does not exist in the database
        content = (
            'Student with penncard {}'
            'has submitted feedback:'
            '{}'.format(penncard, message)
        )
    else:
        # this should happen 99% of the time
        content = (
            'Student {} with email {}'
            'and penncard {} has submitted feedback:'
            '{}'.format(
                student.name,
                student.email,
                student.penncard,
                message
            )
        )

    email_managers("App feedback: {}".format(message), content)


def request_bike_email(bike_type, approx_height, available_time, student):
    subject = "PennCycle Bike Request"
    from_email = "penncycle.bikemanager@gmail.com"
    to_email = student.email
    current_payment = student.current_payment
    plan_info = ""
    if (current_payment):
        plan_info = "{}, expiring on {}".format(current_payment.plan.name, current_payment.end_date.strftime("%m/%d/%y"))
    else:
        plan_info = "You currently don't have a plan. Please purchase a plan when you collect your bike."   
    text_content = """
Dear {}, 

Thanks for requesting a PennCycle bike with the following information:

Approximate height: {}
Bike type: {}
Available times to collect bike from Quaker Corner: {}
Current Plan: {}  

We're choosing the right bike for you and will email you back within 48 hours. Have a question, concern, or suggestion? Email us at penncycle.bikemanager@gmail.com.

Happy Cycling!

The PennCycle Team
    """.format(student.name, approx_height, bike_type, available_time, plan_info)
    html_content = """
</p>Dear {},</p> 

<p>Thanks for requesting a PennCycle bike with the following information:</p>
<ul>
    <li>Approximate height: {}</li>
    <li>Bike type: {}</li>
    <li>Available times to collect bike from Quaker Corner: {}</li>
    <li>Current Plan: {}</li>
</ul>

<p>We're choosing the right bike for you and will email you back within 48 hours. Have a question, concern, or suggestion? Email us at penncycle.bikemanager@gmail.com.</p>

<p>Happy Cycling!</p>

<p>The PennCycle Team</p>
    """.format(student.name, approx_height, bike_type, available_time, plan_info)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email, "penncycle.bikemanager@gmail.com",])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
