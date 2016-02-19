# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import healers.fields
import django.contrib.gis.db.models.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('friends', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address_line1', models.CharField(max_length=42, verbose_name=b'Address Line 1', blank=True)),
                ('address_line2', models.CharField(max_length=42, verbose_name=b'Address Line 2', blank=True)),
                ('postal_code', models.CharField(db_index=True, max_length=10, verbose_name=b'Zip Code', blank=True)),
                ('city', models.CharField(max_length=42, blank=True)),
                ('state_province', models.CharField(max_length=42, verbose_name=b'State', blank=True)),
                ('country', models.CharField(max_length=42, verbose_name=b'Country', blank=True)),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Addresses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('start_time', models.PositiveSmallIntegerField()),
                ('end_time', models.PositiveSmallIntegerField()),
                ('repeat_period', models.PositiveSmallIntegerField(default=None, null=True, choices=[(3, b'day'), (2, b'week')])),
                ('repeat_every', models.PositiveIntegerField(default=1, null=True)),
                ('exceptions', healers.fields.SeparatedValuesField(null=True)),
                ('note', models.TextField(default=b'', null=True, blank=True)),
                ('canceled', models.BooleanField(default=False)),
                ('confirmed', models.BooleanField(default=True)),
                ('repeat_count', models.PositiveIntegerField(default=0, null=True)),
                ('google_event_link', models.CharField(max_length=1024, blank=True)),
                ('created_date', models.DateTimeField()),
                ('last_modified_date', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClientInvitation',
            fields=[
                ('friendshipinvitation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='friends.FriendshipInvitation')),
            ],
            options={
            },
            bases=('friends.friendshipinvitation',),
        ),
        migrations.CreateModel(
            name='Clients',
            fields=[
                ('friendship_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='friends.Friendship')),
            ],
            options={
            },
            bases=('friends.friendship',),
        ),
        migrations.CreateModel(
            name='DiscountCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('amount', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1000)])),
                ('type', models.CharField(default=b'$', max_length=1, choices=[(b'$', b'$'), (b'%', b'%')])),
            ],
            options={
                'ordering': ['code'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Healer',
            fields=[
                ('client_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='clients.Client')),
                ('defaultTimeslotLength', models.FloatField(default=3.0, choices=[(1.0, b'0:30'), (2.0, b'1:00'), (3.0, b'1:30'), (3.5, b'2:00'), (4.0, b'2:30'), (4.5, b'3:00'), (5.0, b'3:30'), (5.5, b'4:00'), (6.0, b'4:30'), (6.5, b'5:00')])),
                ('bookAheadDays', models.IntegerField(default=90)),
                ('leadTime', models.PositiveIntegerField(default=24)),
                ('manualAppointmentConfirmation', models.PositiveSmallIntegerField(default=1, choices=[(1, b'Manually confirm all appointments'), (2, b'Manually confirm appointments for new clients only'), (3, b'Automatically confirm all appointments')])),
                ('scheduleVisibility', models.PositiveSmallIntegerField(default=3, choices=[(0, b'Visible to Everyone'), (2, b'Visible to My Clients Only'), (3, b'Only Me (Preview)')])),
                ('profileVisibility', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Visible to Everyone'), (2, b'Visible to My Clients Only')])),
                ('phonesVisibility', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Visible to Everyone'), (2, b'Visible to My Clients Only')])),
                ('client_screening', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Manually Screen All New Clients'), (1, b'Auto Approve New Clients who Ive Imported from Facebook/Google'), (2, b'Automatically Approve All New Clients')])),
                ('setup_time', models.PositiveSmallIntegerField(default=30, verbose_name=b'Setup time between clients')),
                ('smart_scheduler_avoid_gaps_num', models.PositiveSmallIntegerField(default=0, verbose_name=b'Number of slots available if first one of the day is booked')),
                ('profile_completeness_reminder_interval', models.PositiveSmallIntegerField(default=1, choices=[(1, b'1 week'), (2, b'2 weeks'), (4, b'1 month'), (8, b'2 months')])),
                ('profile_completeness_reminder_lastdate', models.DateField(null=True, blank=True)),
                ('timezone', models.CharField(default=b'', max_length=b'6', verbose_name=b'Timezone', blank=True, choices=[(b'-05:00', b'-5:00: Eastern Time (US & Canada)'), (b'-06:00', b'-6:00: Central Time (US & Canada)'), (b'-07:00', b'-7:00: Mountain Time (US & Canada)'), (b'-08:00', b'-8:00: Pacific Time (US & Canada)'), (b'-09:00', b'-9:00: Alaska'), (b'-10:00', b'-10:00: Hawaii'), (b'-11:00', b'-11:00: Midway Island, Samoa'), (b'-12:00', b'-12:00: Eniwetok, Kwajalein'), (b'+12:00', b'+12:00: Auckland, Wellington, Fiji'), (b'+11:00', b'+11:00: Magadan, Solomon Isl'), (b'+10:00', b'+10:00: Eastern Australia, Guam'), (b'+09:30', b'+9:30: Adelaide, Darwin'), (b'+09:00', b'+9:00: Tokyo, Seoul, Osaka'), (b'+08:00', b'+8:00: Beijing, Perth, Singapore, HK'), (b'+07:00', b'+7:00: Bangkok, Hanoi, Jakarta'), (b'+06:30', b'+6:30: Rangoon, Cocos'), (b'+06:00', b'+6:00: Almaty, Dhaka, Colombo'), (b'+05:45', b'+5:45: Kathmandu'), (b'+05:30', b'+5:30: Bombay, Calcutta, Delhi'), (b'+05:00', b'+5:00: Ekaterinburg, Karachi'), (b'+04:30', b'+4:30: Kabul'), (b'+04:00', b'+4:00: Abu Dhabi, Muscat, Baku'), (b'+03:30', b'+3:30: Tehran'), (b'+03:00', b'+3:00: Riyadh, Moscow, St Peter'), (b'+02:00', b'+2:00: Kaliningrad, South Africa'), (b'+01:00', b'+1:00: Copenhagen, Madrid, Paris'), (b'+00:00', b'GMT: W. Europe, London, Lisbon'), (b'-01:00', b'-1:00: Azores, Cape Verde Islands'), (b'-02:00', b'-2:00: Mid-Atlantic'), (b'-03:00', b'-3:00: Brazil, Buenos Aires'), (b'-03:30', b'-3:30: Newfoundland'), (b'-04:00', b'-4:00: Atlantic Time (Canada)'), (b'-04:30', b'-4:30: Caracas')])),
                ('scheduleUpdatedThrough', models.DateField(default=b'1969-08-17')),
                ('google_calendar_feed_link', models.CharField(max_length=1024, blank=True)),
                ('google_calendar_edit_link', models.CharField(max_length=1024, blank=True)),
                ('google_email', models.EmailField(max_length=75, blank=True)),
                ('seen_availability_help', models.BooleanField(default=False)),
                ('seen_appointments_help', models.BooleanField(default=False)),
                ('office_hours_start', models.TimeField(default=b'10:00:00')),
                ('office_hours_end', models.TimeField(default=b'20:00:00')),
                ('years_in_practice', models.CharField(default=b'', max_length=4, blank=True)),
                ('send_notification', models.BooleanField(default=True)),
                ('cancellation_policy', models.TextField(default=b'', verbose_name='cancellation_policy', blank=True)),
                ('additional_text_for_email', models.TextField(default=b'', verbose_name='additional info', blank=True)),
                ('location_bar_title', models.CharField(default=b'Locations: ', max_length=36, blank=True)),
                ('setup_step', models.PositiveSmallIntegerField(default=0)),
                ('ratings_1_star', models.PositiveIntegerField(default=0)),
                ('ratings_2_star', models.PositiveIntegerField(default=0)),
                ('ratings_3_star', models.PositiveIntegerField(default=0)),
                ('ratings_4_star', models.PositiveIntegerField(default=0)),
                ('ratings_5_star', models.PositiveIntegerField(default=0)),
                ('ratings_average', models.FloatField(default=0)),
                ('review_permission', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Everyone'), (2, b'My Clients Only'), (3, b'Nobody (Hide All Current Reviews)')])),
                ('send_sms_appt_request', models.BooleanField(default=True)),
                ('schedule_full_width', models.BooleanField(default=False)),
                ('schedule_start_from_sunday_setting', models.BooleanField(default=False)),
                ('notes_notice_shown', models.BooleanField(default=False)),
                ('default_modality', models.CharField(default=b'Healer', max_length=64)),
                ('default_location', models.CharField(default=b'USA', max_length=64)),
                ('deposit_percentage', models.PositiveIntegerField(default=100)),
            ],
            options={
                'verbose_name': 'healers',
                'verbose_name_plural': 'healers',
                'permissions': (('can_use_wcenter_schedule', 'Can use wellness center schedule'), ('can_use_notes', 'Can use notes')),
            },
            bases=('clients.client',),
        ),
        migrations.CreateModel(
            name='Concierge',
            fields=[
                ('healer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='healers.Healer')),
            ],
            options={
            },
            bases=('healers.healer',),
        ),
        migrations.CreateModel(
            name='HealerTimeslot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('start_time', models.PositiveSmallIntegerField()),
                ('end_time', models.PositiveSmallIntegerField()),
                ('repeat_period', models.PositiveSmallIntegerField(default=None, null=True, choices=[(3, b'day'), (2, b'week')])),
                ('repeat_every', models.PositiveIntegerField(default=1, null=True)),
                ('exceptions', healers.fields.SeparatedValuesField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('address_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='healers.Address')),
                ('title', models.CharField(max_length=42, verbose_name=b'Location Name')),
                ('timezone', models.CharField(default=b'', max_length=b'6', verbose_name=b'Timezone', blank=True, choices=[(b'-05:00', b'-5:00: Eastern Time (US & Canada)'), (b'-06:00', b'-6:00: Central Time (US & Canada)'), (b'-07:00', b'-7:00: Mountain Time (US & Canada)'), (b'-08:00', b'-8:00: Pacific Time (US & Canada)'), (b'-09:00', b'-9:00: Alaska'), (b'-10:00', b'-10:00: Hawaii'), (b'-11:00', b'-11:00: Midway Island, Samoa'), (b'-12:00', b'-12:00: Eniwetok, Kwajalein'), (b'+12:00', b'+12:00: Auckland, Wellington, Fiji'), (b'+11:00', b'+11:00: Magadan, Solomon Isl'), (b'+10:00', b'+10:00: Eastern Australia, Guam'), (b'+09:30', b'+9:30: Adelaide, Darwin'), (b'+09:00', b'+9:00: Tokyo, Seoul, Osaka'), (b'+08:00', b'+8:00: Beijing, Perth, Singapore, HK'), (b'+07:00', b'+7:00: Bangkok, Hanoi, Jakarta'), (b'+06:30', b'+6:30: Rangoon, Cocos'), (b'+06:00', b'+6:00: Almaty, Dhaka, Colombo'), (b'+05:45', b'+5:45: Kathmandu'), (b'+05:30', b'+5:30: Bombay, Calcutta, Delhi'), (b'+05:00', b'+5:00: Ekaterinburg, Karachi'), (b'+04:30', b'+4:30: Kabul'), (b'+04:00', b'+4:00: Abu Dhabi, Muscat, Baku'), (b'+03:30', b'+3:30: Tehran'), (b'+03:00', b'+3:00: Riyadh, Moscow, St Peter'), (b'+02:00', b'+2:00: Kaliningrad, South Africa'), (b'+01:00', b'+1:00: Copenhagen, Madrid, Paris'), (b'+00:00', b'GMT: W. Europe, London, Lisbon'), (b'-01:00', b'-1:00: Azores, Cape Verde Islands'), (b'-02:00', b'-2:00: Mid-Atlantic'), (b'-03:00', b'-3:00: Brazil, Buenos Aires'), (b'-03:30', b'-3:30: Newfoundland'), (b'-04:00', b'-4:00: Atlantic Time (Canada)'), (b'-04:30', b'-4:30: Caracas')])),
                ('addressVisibility', models.PositiveSmallIntegerField(default=0, verbose_name=b'Full Address Visibility', choices=[(0, b'Visible to Everyone'), (2, b'Visible to My Clients Only'), (3, b'Dont Show Address (Only Location Name)')])),
                ('book_online', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('color', models.CharField(default=b'', max_length=7, verbose_name=b'Color', choices=[(b'#68A1E5', b'#68A1E5'), (b'#5FBF87', b'#5FBF87'), (b'#928ECF', b'#928ECF'), (b'#F2A640', b'#F2A640'), (b'#A7A77D', b'#A7A77D'), (b'#BE9494', b'#BE9494'), (b'#E0C240', b'#E0C240'), (b'#D96666', b'#D96666'), (b'#59BFB3', b'#59BFB3'), (b'#C09B64', b'#C09B64'), (b'#BFBF4D', b'#BFBF4D'), (b'#DF80F7', b'#DF80F7'), (b'#8BE2B8', b'#8BE2B8'), (b'#E69229', b'#E69229'), (b'#9EDF4B', b'#9EDF4B'), (b'#5C7BBE', b'#5C7BBE'), (b'#7EECEC', b'#7EECEC'), (b'#52E08B', b'#52E08B'), (b'#8BB83B', b'#8BB83B'), (b'#ECE766', b'#ECE766')])),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=('healers.address',),
        ),
        migrations.CreateModel(
            name='ReferralInvitation',
            fields=[
                ('friendshipinvitation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='friends.FriendshipInvitation')),
            ],
            options={
            },
            bases=('friends.friendshipinvitation',),
        ),
        migrations.CreateModel(
            name='Referrals',
            fields=[
                ('friendship_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='friends.Friendship')),
            ],
            options={
            },
            bases=('friends.friendship',),
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name=b'name')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TreatmentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=42)),
                ('description', models.TextField(default=b'', blank=True)),
                ('is_default', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TreatmentTypeLength',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('length', models.PositiveIntegerField()),
                ('cost', models.CharField(max_length=10)),
                ('is_default', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['length', 'cost'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnavailableSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('start_time', models.PositiveSmallIntegerField()),
                ('end_time', models.PositiveSmallIntegerField()),
                ('repeat_period', models.PositiveSmallIntegerField(default=None, null=True, choices=[(3, b'day'), (2, b'week')])),
                ('repeat_every', models.PositiveIntegerField(default=1, null=True)),
                ('exceptions', healers.fields.SeparatedValuesField(null=True)),
                ('api', models.PositiveSmallIntegerField(choices=[(0, b'Google')])),
                ('title', models.CharField(max_length=1024, blank=True)),
                ('event_id', models.CharField(max_length=1024, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vacation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('start_time', models.PositiveSmallIntegerField()),
                ('end_time', models.PositiveSmallIntegerField()),
                ('repeat_period', models.PositiveSmallIntegerField(default=None, null=True, choices=[(3, b'day'), (2, b'week')])),
                ('repeat_every', models.PositiveIntegerField(default=1, null=True)),
                ('exceptions', healers.fields.SeparatedValuesField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WellnessCenter',
            fields=[
                ('healer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='healers.Healer')),
                ('payment_schedule_setting', models.PositiveSmallIntegerField(default=1, choices=[(1, b'Disable schedule'), (2, b'Each Provider pays individually for their schedule'), (3, b'Center pays for everyone')])),
                ('clients_visible_to_providers', models.BooleanField(default=False)),
                ('schedule_side_by_side_setting', models.BooleanField(default=False)),
                ('schedule_trial_started_date', models.DateField(null=True, blank=True)),
                ('schedule_dropdown_provider_list', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=('healers.healer',),
        ),
        migrations.CreateModel(
            name='WellnessCenterGoogleEventLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('google_event_link', models.CharField(max_length=1024, blank=True)),
                ('appointment', models.ForeignKey(related_name=b'wellness_center_google_event_links', to='healers.Appointment')),
                ('wellness_center', models.ForeignKey(to='healers.WellnessCenter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WellnessCenterTreatmentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('healer', models.ForeignKey(related_name=b'wellness_center_treatment_types', to='healers.Healer')),
                ('treatment_types', models.ManyToManyField(to='healers.TreatmentType', null=True, blank=True)),
                ('wellness_center', models.ForeignKey(to='healers.WellnessCenter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WellnessCenterTreatmentTypeLength',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('healer', models.ForeignKey(related_name=b'wellness_center_treatment_type_lengths', to='healers.Healer')),
                ('treatment_type_lengths', models.ManyToManyField(to='healers.TreatmentTypeLength', null=True, blank=True)),
                ('wellness_center', models.ForeignKey(to='healers.WellnessCenter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Zipcode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=5, db_index=True)),
                ('city', models.CharField(max_length=50, blank=True)),
                ('state', models.CharField(max_length=2, blank=True)),
                ('population', models.PositiveIntegerField(default=0, blank=True)),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=4326)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='vacation',
            name='healer',
            field=models.ForeignKey(to='healers.Healer'),
            preserve_default=True,
        ),
    ]
