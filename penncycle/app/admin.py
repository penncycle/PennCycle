from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from penncycle.app.models import *
import datetime

class StudentAdmin(admin.ModelAdmin):
  list_per_page = 500
  list_display = (
      'name', 'grad_year', 'penncard',
      'gender', 'school', 'waiver_signed', 'paid_now',)
  search_fields = ('name', 'penncard',)
  list_filter = ('school', 'gender', 'grad_year')
  date_hierarchy = 'join_date'
    
class BikeAdmin(admin.ModelAdmin):
  list_display = ('bike_name', 'status', 'manufacturer', 'purchase_date')
  list_filter = ('purchase_date','manufacturer',)
  date_hierarchy = 'purchase_date'

class PageAdmin(admin.ModelAdmin):
  readonly_fields = ('slug',)

class RidesAdmin(admin.ModelAdmin):
  list_display = (
      'rider', 'bike', 'checkout_time', 'checkin_time', 'ride_duration_days', 'status', 'checkin_station',
  )
  list_filter = (
      'rider', 'bike', 'checkout_time', 'checkin_time', 'checkin_station',
  ) 
  readonly_fields = ('ride_duration_days', 'num_users')
  date_hierarchy = 'checkin_time'
  ordering = ('-checkout_time',)
  actions = ['check_in']
  search_fields = ['rider__name','rider__penncard','bike__bike_name']
  save_on_top = True

  # make this only work for bikes not already checked in
  def check_in(self, request, queryset):
    station_name = request.user.groups.exclude(name='Associate')[0].name or ''
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
        send_mail('How was your ride today?', '''
Hey %s, \n
How was your ride today? 
(Where'd you ride today, how was the bike, were there any problems, etc.) \n
We'd love to hear how your ride was,
Alex & the PennCycle Team
          ''' % (s.name),
          '"The PennCycle Team" <messenger@penncycle.org>', [s.email], fail_silently=False)
      item.save()
    if rides_updated == 1:
      message_bit = '1 bike was'
    else:
      message_bit = '%s bikes were' % rides_updated
    self.message_user(request, '%s successfully checked in' % message_bit)
  check_in.short_description = "Check in the selected rides"

admin.site.register(Comment)
admin.site.register(Station)
admin.site.register(Manufacturer)
admin.site.register(Student, StudentAdmin)
admin.site.register(Bike, BikeAdmin)
admin.site.register(Ride, RidesAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Plan)
admin.site.register(Payment)
