from django.db.models.signals import pre_save, pre_delete
from django.test import TestCase
from django_dynamic_fixture import G
from healers.models import Appointment, HealerTimeslot
from audit.models import AppointmentAudit, HealerTimeslotAudit,\
	audit_callback, audit_delete_callback


class AppointmentAuditTest(TestCase):

	def setUp(self):
		pre_save.disconnect(audit_callback, sender=Appointment)

	def test_create(self):
		pre_save.connect(audit_callback, sender=Appointment)
		G(Appointment, note='note1')

		a = AppointmentAudit.objects.all()[0]
		self.assertTrue('created' in a.before)
		self.assertTrue('note1' in a.after)

	def test_update(self):
		appointment = G(Appointment, note='test1')

		pre_save.connect(audit_callback, sender=Appointment)
		appointment.note = 'test2'
		appointment.save()

		a = AppointmentAudit.objects.get(timeslot=appointment.id)
		self.assertTrue('test1' in a.before)
		self.assertTrue('test2' in a.after)

	def test_delete(self):
		appointment = G(Appointment, note='test1')
		appointment_id = appointment.id

		pre_delete.connect(audit_delete_callback, sender=Appointment)
		appointment.delete()

		a = AppointmentAudit.objects.get(timeslot=appointment_id)
		self.assertTrue('deleted' in a.after)


class HealerTimeslotAuditTest(TestCase):

	def setUp(self):
		pre_save.disconnect(audit_callback, sender=HealerTimeslot)

	def test_create(self):
		pre_save.connect(audit_callback, sender=HealerTimeslot)
		G(HealerTimeslot)

		a = HealerTimeslotAudit.objects.all()[0]
		self.assertTrue('created' in a.before)

	def test_update(self):
		timeslot = G(HealerTimeslot, start_time=0, end_time=1300)

		pre_save.connect(audit_callback, sender=HealerTimeslot)
		timeslot.end_time = 1380
		timeslot.save()

		a = HealerTimeslotAudit.objects.get(timeslot=timeslot.id)
		self.assertTrue('11:00' in a.after)

	def test_delete(self):
		timeslot = G(HealerTimeslot)
		timeslot_id = timeslot.id

		pre_delete.connect(audit_delete_callback, sender=HealerTimeslot)
		timeslot.delete()

		a = HealerTimeslotAudit.objects.get(timeslot=timeslot_id)
		self.assertTrue('deleted' in a.after)
