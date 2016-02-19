from django.contrib import admin

from healers.models import Healer, HealerTimeslot, Client, Appointment

class HealerTimeslotInline(admin.TabularInline):
	model = HealerTimeslot
	extra = 3

class HealerAdmin(admin.ModelAdmin):
	inlines = [HealerTimeslotInline]

admin.site.register(Healer, HealerAdmin)
admin.site.register(Client)
admin.site.register(Appointment)

