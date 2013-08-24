from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django_twilio.client import twilio_client


def send_pin_to_student(student):
    try:
        pin = student.pin
        twilio_client.sms.messages.create(
            to=student.twilio_phone,
            body="Your PIN for PennCycle is {}."
            " Log in the website at penncycle.org/signin.".format(pin),
            from_="+12156885468"
        )
    except Exception as error:
        email_razzi("Pin send failed: {}".format(error))

def email_razzi(message):
    send_mail(
        'an important email from the PennCycle app',
        str(message),
        'messenger@penncycle.org', ['razzi53@gmail.com'],
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
