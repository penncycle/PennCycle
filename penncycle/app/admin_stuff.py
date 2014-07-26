from django.contrib import admin
from penncycle.app.models import *
import datetime

# Stuff from django.contrib.admin.options
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode
from django.contrib.admin import helpers
from django.db import models, transaction
from django.utils.safestring import mark_safe
from django.forms.formsets import all_valid
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

csrf_protect_m = method_decorator(csrf_protect)


class StudentAdmin(admin.ModelAdmin):
    list_per_page = 500
    list_display = (
        'name', 'grad_year', 'penncard',
        'gender', 'living_location', 'waiver_signed', 'paid_now',
    )
    search_fields = ('name', 'penncard',)
    list_filter = ('school', 'gender', 'grad_year', 'living_location')
    date_hierarchy = 'join_date'


class PaymentAdmin(admin.ModelAdmin):
    list_per_page = 500
    list_display = (
        'student', 'plan', 'amount', 'payment_type',
        'satisfied', 'status'
    )
    search_fields = ('student__name', 'plan__name',)
    list_filter = ('plan', 'payment_type', 'satisfied')
    date_hierarchy = 'purchase_date'


class BikeAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'location', 'combo_update', 'last_serviced_date')
    list_filter = ('purchase_date', 'manufacturer',)
    date_hierarchy = 'purchase_date'


class RidesAdmin(admin.ModelAdmin):
    list_display = (
        'rider', 'rider_phone', 'bike', 'checkout_time', 'checkin_time',
        'ride_duration_days', 'status', 'checkin_station',
    )
    readonly_fields = ('ride_duration_days',)
    date_hierarchy = 'checkin_time'
    ordering = ('-checkout_time',)
    actions = ['check_in']
    search_fields = ['rider__name', 'rider__penncard', 'bike__name', 'checkin_station__name', 'checkout_station__name']
    save_on_top = True

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        "The 'add' admin view for this model."
        model = self.model
        opts = model._meta
        print 'in custom add_view page'
        print request
        print opts

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES)
            # print form.__getitem__('rider')
            # print form['rider']
            # print help(form['rider'])
            # print form['rider'].data
            # print form.visible_fields()
            # print form.changed_data
            # print form.__dict__
            try:
                print form
                more_than_one = False
            except:
                more_than_one = True
            if more_than_one:
                print 'custom form saving time yay'
                student = Student.objects.get(id=form['rider'].data)
                bike = Bike.objects.get(id=form['bike'].data)
                station = Station.objects.get(id=form['checkout_station'].data)
                print student, bike, station
                new_object = Ride(
                    rider=student,
                    bike=bike,
                    checkout_station=station,
                )
                print new_object
                new_object.save()
                form_validated = True  # LOLZs
                return self.response_add(request, new_object)
            elif form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                form_validated = False
                new_object = self.model()
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(
                    data=request.POST, files=request.FILES,
                    instance=new_object,
                    save_as_new="_saveasnew" in request.POST,
                    prefix=prefix, queryset=inline.queryset(request)
                )
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=False)

                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
        else:
                # Prepare the dict of initial data from the request.
                # We have to special-case M2Ms as a list of comma-separated PKs.
                initial = dict(request.GET.items())
                for k in initial:
                    try:
                        f = opts.get_field(k)
                    except models.FieldDoesNotExist:
                        continue
                    if isinstance(f, models.ManyToManyField):
                        initial[k] = initial[k].split(",")
                form = ModelForm(initial=initial)
                prefixes = {}
                for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                    prefix = FormSet.get_default_prefix()
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                    if prefixes[prefix] != 1:
                        prefix = "%s-%s" % (prefix, prefixes[prefix])
                    formset = FormSet(instance=self.model(), prefix=prefix, queryset=inline.queryset(request))
                    formsets.append(formset)

        adminForm = helpers.AdminForm(
            form, list(self.get_fieldsets(request)),
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self
        )
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request))
            readonly = list(inline.get_readonly_fields(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                    fieldsets, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)

    # make this only work for bikes not already checked in
    def check_in(self, request, queryset):
        try:
            station_name = request.user.groups.exclude(name='Associate')[0].name
        except:
            return HttpResponse("You don't have any groups. Go to app.penncycle.org/admin/auth/user and make sure 'associate' and your station are checked.")
        station = Station.objects.get(name=station_name)
        rides_updated = queryset.update(checkin_time=datetime.datetime.now(), checkin_station=station)
        for item in queryset:
            #item.checkin_time=time
            #item.duration = time - item.checkout_time
            item.bike.status='available'
            item.bike.save()
            item.rider.status='available'
            item.rider.save()
            s = item.rider
            if len(s.ride_set.all()) < 4:
                subject ='How was your ride today?'
                from_email='"The PennCycle Team" <messenger@penncycle.org>'
                to = [s.email,]

                html_content = render_to_string('feedback_email.html', {'student_name':s.name})
                text_content = strip_tags(html_content) # this strips the html, so people will have the text as well.

                # create the email, and attach the HTML version as well.
                # msg = EmailMultiAlternatives(subject, text_content, from_email, to)
                # msg.attach_alternative(html_content, "text/html")
                # msg.send(fail_silently=True)
#         send_mail('How was your ride today?', '''
# Hey %s, \n
# How was your ride today?
# (Where'd you ride today, how was the bike, were there any problems, etc.) \n
# We'd love to hear how your ride was,
# Alex & the PennCycle Team
# <a href="http://api.addthis.com/oexchange/0.8/forward/facebook/offer?pco=tbx32nj-1.0&url=http://app.penncycle.org&pubid=xa-506765865cc9f0e8" target="_blank" ><img src="http://cache.addthiscdn.com/icons/v1/thumbs/32x32/facebook.png" border="0" alt="Facebook" /></a>
#           ''' % (s.name),
#           '"The PennCycle Team" <messenger@penncycle.org>', [s.email], fail_silently=False)
            item.save()
        if rides_updated == 1:
            message_bit = '1 bike was'
        else:
            message_bit = '%s bikes were' % rides_updated
        self.message_user(request, '%s successfully checked in' % message_bit)

    check_in.short_description = "Check in the selected rides"
