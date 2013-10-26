from django.core.mail import send_mail, EmailMultiAlternatives
from django_twilio.client import twilio_client


def send_pin_to_student(student):
    try:
        pin = student.pin
        twilio_client.sms.messages.create(
            to=student.twilio_phone,
            body="Your PennCycle PIN is {}. "
            "Login at penncycle.org/signin. "
            "Once you buy a plan, check out bikes by texting "
            "this number. Text 'help' for instructions.".format(pin),
            from_="+12156885468"
        )
    except Exception as error:
        email_razzi("Pin send failed: {}, {}".format(student, error))

def email_razzi(message):
    send_mail(
        'an important email from the PennCycle app',
        str(message),
        'messenger@penncycle.org', ['razzi53@gmail.com'],
        fail_silently=True
    )

def email_managers(student, message, bike):
    body =  "{} reported {}. No bikes were changed.".format(student, message) 

    if bike:
        body = "{} had its status changed to {}.".format(bike, message)
    else:
        body = "No bikes were changed"
    
    send_mail(
        "{} reported issue: {}".format(student, message),
        str(body)
        'messenger@penncycle.org', ['messenger@penncycle.org'],
        fail_silently=True
        )

def welcome_email(student):
    subject = "Welcome to PennCycle"
    from_email = "messenger@penncycle.org"
    to_email = student.email
    text_content = """
Thanks for joining PennCycle.

Your PennCycle PIN is {}. You can use it to log in at penncycle.org/login. Once you log in, you can add plans, sign the required waiver, and change your PIN.

Helmets are required for riding and can be rented or purchased at Quaker Corner.

Have a question, concern, or suggestion? Email us at messenger@penncycle.org.

Happy Cycling!

The PennCycle Team
    """.format(student.pin)
    html_content = """
<p>Thanks for joining PennCycle.</p>

<p>Your PennCycle PIN is {}. You can use it to <a href="http://www.penncycle.org/login">log in</a> at penncycle.org. Once you log in, you can add plans, sign the required waiver, and change your PIN.</p>

<p>Helmets are required for riding and can be rented for free or purchased at <a href='http://www.penncycle.org/about#qc'>Quaker Corner</a>.</p>

<p>Have a question, concern, or suggestion? Email us at messenger@penncycle.org.</p>

<p>Happy Cycling!</p>

<p>The PennCycle Team</p>
    """.format(student.pin)
    # Bikes can be checked out using the free phone app. Don't have a smartphone? Text 'Help' to 215-688-5468 for instructions on how to check out bikes through texting.
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

It's easy to renew your subscription to PennCycle. Just log in to your account on the PennCycle website and add a Basic or Unlimited plan,
or click the renew button on a current plan to have it automatically renew by bursar. You can pay for a new plan with bursar or credit online
or by coming to Quaker Corner (Williams Hall Room 117) and paying with cash.

We hope you have enjoyed PennCycle. Please let us know if you have any questions or if we can help you out in any way. 

Thanks! Keep on pedaling!

Bobby and the PennCycle Team
""".format(student.name, payment.end_date.strftime("%B %d"))
    html_content = """
<p>Dear {},</p>

<p>Your monthly PennCycle membership will expire on {}!</p>

<p>It's easy to renew your subscription to PennCycle. Just <a href="http://www.penncycle.org/login">log in</a> to your account on the PennCycle website and add a Basic or Unlimited plan,
or click the renew button on a current plan to have it automatically renew by bursar. You can pay for a new plan with bursar or credit online
or by coming to <a href='http://www.penncycle.org/about#qc'>Quaker Corner</a> (Williams Hall Room 117) and paying with cash.</p>

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

Thank you for signing up for a PennCycle plan! Once your payment is processed, you will be eligible to check out PennCycles from any of our locations on campus.

In order to check out bikes, text 'help' to 215-688-5468 for instructions. The basic commands are 'check out (bike)' and 'check in (location)'.

While using PennCycle, keep the following in mind:

1. Before riding do an ABC Check (Air in Tires, Brakes, Chain)

2. If you experience any problems while riding or finding a bike, email messenger@penncycle.org.

3. Remember to physically locate the bike you want to check out before texting. This is very important and ensures that you will not be liable for damage/loss of a bike whose location you were unaware of.

4. If your tires feel flat you can pump them up at the bike racks to the next to Pottruck, by the Chemistry Building, and at Quaker Corner, or email us at messenger@penncycle.org and we'll pump them up for you!

5. Always lock up your bike properly! See the attached picture of a properly locked bike. Ensure the lock goes through the rack, the front wheel and a sturdy part of the frame. If you can't include the front wheel, be sure to include the frame. PennCycle will charge a $5 fee for an improperly locked bike. Never lock your bike to a garbage can, or bench.

We hope that you enjoy your PennCycle experience! 

Happy Cycling!

Bobby and the PennCycle Team
""".format(student.name)
    html_content = """
<p>Dear {},</p>

<p>Thank you for signing up for a PennCycle plan! Once your payment is processed, you will be eligible to check out PennCycles from any of our locations on campus.</p>

<p>In order to check out bikes, text 'help' to 215-688-5468 for instructions. The basic commands are 'check out (bike)' and 'check in (location)'.</p>

<p>While using PennCycle, keep the following in mind:</p>
<ol>
    <li>Before riding do an ABC Check (Air in Tires, Brakes, Chain)</li>

    <li>If you experience any problems while riding or finding a bike, email messenger@penncycle.org.</li>

    <li><b>Remember to physically locate the bike you want to check out before texting.</b> This is very important and ensures that you will not be liable for damage/loss of a bike whose location you were unaware of.</li>

    <li>If your tires feel flat you can pump them up at the bike racks to the next to Pottruck, by the Chemistry Building, and at Quaker Corner, or email us at messenger@penncycle.org and we'll pump them up for you!</li>

    <li><b>Always lock up your bike properly!</b> See the attached picture of a properly locked bike. Ensure the lock goes through the rack, the front wheel and a sturdy part of the frame. If you can't include the front wheel, be sure to include the frame. PennCycle will charge a $5 fee for an improperly locked bike. Never lock your bike to a garbage can, or bench.</li>
</ol>

<p>We hope that you enjoy your PennCycle experience!</p>

<p>Happy Cycling!</p>

<p>The PennCycle Team</p>""".format(student.name)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.attach_file("penncycle/assets/img/locked_bike.png")
    msg.send()

