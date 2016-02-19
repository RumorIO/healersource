# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0021_auto_20150331_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discountcode',
            name='code',
            field=models.CharField(max_length=30),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='healer',
            name='timezone',
            field=models.CharField(default=b'-05:00', max_length=b'6', verbose_name=b'Timezone', choices=[(b'-05:00', b'-5:00: Eastern Time (US & Canada)'), (b'-06:00', b'-6:00: Central Time (US & Canada)'), (b'-07:00', b'-7:00: Mountain Time (US & Canada)'), (b'-08:00', b'-8:00: Pacific Time (US & Canada)'), (b'-09:00', b'-9:00: Alaska'), (b'-10:00', b'-10:00: Hawaii'), (b'-11:00', b'-11:00: Midway Island, Samoa'), (b'-12:00', b'-12:00: Eniwetok, Kwajalein'), (b'+12:00', b'+12:00: Auckland, Wellington, Fiji'), (b'+11:00', b'+11:00: Magadan, Solomon Isl'), (b'+10:00', b'+10:00: Eastern Australia, Guam'), (b'+09:30', b'+9:30: Adelaide, Darwin'), (b'+09:00', b'+9:00: Tokyo, Seoul, Osaka'), (b'+08:00', b'+8:00: Beijing, Perth, Singapore, HK'), (b'+07:00', b'+7:00: Bangkok, Hanoi, Jakarta'), (b'+06:30', b'+6:30: Rangoon, Cocos'), (b'+06:00', b'+6:00: Almaty, Dhaka, Colombo'), (b'+05:45', b'+5:45: Kathmandu'), (b'+05:30', b'+5:30: Bombay, Calcutta, Delhi'), (b'+05:00', b'+5:00: Ekaterinburg, Karachi'), (b'+04:30', b'+4:30: Kabul'), (b'+04:00', b'+4:00: Abu Dhabi, Muscat, Baku'), (b'+03:30', b'+3:30: Tehran'), (b'+03:00', b'+3:00: Riyadh, Moscow, St Peter'), (b'+02:00', b'+2:00: Kaliningrad, South Africa'), (b'+01:00', b'+1:00: Copenhagen, Madrid, Paris'), (b'+00:00', b'GMT: W. Europe, London, Lisbon'), (b'-01:00', b'-1:00: Azores, Cape Verde Islands'), (b'-02:00', b'-2:00: Mid-Atlantic'), (b'-03:00', b'-3:00: Brazil, Buenos Aires'), (b'-03:30', b'-3:30: Newfoundland'), (b'-04:00', b'-4:00: Atlantic Time (Canada)'), (b'-04:30', b'-4:30: Caracas')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='discountcode',
            unique_together=set([('healer', 'code')]),
        ),
    ]
