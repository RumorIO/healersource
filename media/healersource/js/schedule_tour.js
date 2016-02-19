var Tour_Current = 0;
var Tour = [
	{  selector: '.tour_visibility_bar',
		text: "<b>This is the Schedule Visibility Bar.</b><p>You can use it to control who can see your schedule.</p>"
	},

	{  selector: '#schedule_disabled_box .red_button_selected',
		text: "Your Schedule is Currently in <b>Preview</b>. <p>That means nobody can see it except for you. You can play around with it to your heart's content and then make it public when you're happy with it.</p>"
	},

	{  selector: '#schedule_disabled_box .green_button',
		text: "When your schedule is ready, you can click here to make it visible to the public."
	},

	{  selector: '#schedule_disabled_box .my_clients_only',
		text: "Or you can make your schedule visible to Your Clients Only."
	},

	{  selector: '.wc-grid-row-events',
		gravity: 's',
		offset: -70,
		text: "<b>This is the Grid.</b><p>This is where you can add, edit, and view both your Appointments and Availability.</p>"
	},

	{  selector: '#cal_date',
		text: "This shows the dates currently visible in the Grid"
	},

	{  selector: '#cal_prev',
		text: "Click here to go to the Previous Week. <p>You can't go back past the current week</p>"
	},

	{  selector: '#cal_next',
		text: "Click here to go to the Next Week"
	},

	{  selector: '#edit_availability_selector span.selected',
		text: "<b>This is the Schedule Mode Selector.</b><p>Your schedule is currently in <b>{MODE} Mode</b> which means that the Grid will show any {MODE} you have this week. </p><p>To add new {MODE}, just click the Grid.</p>"
	},

	{  selector: '#edit_availability_selector .button_container > span:not(.selected)',
		text: "Click the <b>Edit {NOT_MODE}</b> button to switch to <b>{NOT_MODE} Mode.</b><p>Then you can add {NOT_MODE} by clicking on the Grid.</p>"
	},

	{  selector: '#appointments_view_7_days_button',
		text: "<b>This is the View Selector.</b><p>You can see your Appointments in Week View or as a List.</p>"
	},

//	{  selector: 'appointments_view_list_button',
//		text: ""
//	},

	{  selector: '#set_your_location',
		gravity: 'ne',
		text: "<b>Click here to Set Your Location.</b><p>It's really important to add at least one location so that new clients can find you! </p>"
	},

	{  selector: '#location_bar_edit',
		gravity: 'ne',
		text: "<b>This is the Location Bar.</b><p>If you click on one of your locations, the schedule will show only Appointments or Availability at that location. </p>"
	},

	{  selector: '#sessions_im_receiving',
		gravity: 'se',
		text: "The <b>Sessions I'm Receiving</b> link will show you the sessions where you are the client. <p>Remember to take care of yourself too!</p>"
	},

	{  selector: '#appointment_history',
		gravity: 'se',
		text: "The <b>Appointment History</b> link will show Appointments that have already passed."
	},

	{  selector: '#preview_schedule',
		gravity: 'se',
		text: "The <b>Preview Schedule</b> button is a handy way to preview your schedule without ever leaving this page. <p>You can instantly see exactly what your clients will see when they visit your profile.</p>"
	},

	{  selector: '#schedule_settings_link',
		gravity: 'sw',
		text: "Click here to access your <b>Schedule Settings</b>. <p>We highly recommend that you look through these carefully to make sure everything is set up exactly the way you want.</p>"
	},

	{  selector: '#treatment_types_link',
		gravity: 's',
		text: "The <b>Treatment Types</b> link lets you add and edit the types of services that clients can book through your schedule."
	},

	{  selector: '#locations_link',
		gravity: 's',
		text: "Click here to add and edit your <b>Locations.</b><p>If you travel and have multiple locations, you can put in as many as you like.</p>"
	},

	{  selector: '#time_off_link',
		gravity: 's',
		text: "The <b>Time Off</b> lets you add vacation time. <p>You can add any length of time when your schedule will be marked as unavailable. </p><p>Whether you're taking the afternoon off or an entire week, this makes it easy!</p>"
	}


];

//$(document).ready(function() {
//	help_init();
//});

function tour_get(idx) {
	if(typeof(Tour[idx]) != 'undefined') {
		return $(Tour[idx]['selector']).first();
	} else {
		return $();
	}
}

function tour_get_current() {
	return tour_get(Tour_Current);
}

function tour_next() {
	if( (Tour_Current >= Tour.length) || (Tour_Current < -1) )
		tour_stop();

	tour_get_current().tipsy('hide');
	Tour_Current++;
	tour_get_current().focus();
	if(Tour_Current == Tour.length) {
		Tour_Current = -1;

		hs_dialog('#schedule_tour_end', {
			title: 'The End',
			title_class: 'nav_tour',
			autoOpen: true,
			buttons: {
				"Thanks!" : function() { hs_dialog("close"); }
			}
		});

		Dajaxice.healers.seen_appointments_help(function(){});

	} else {
		if(!tour_get_current().is(':visible')) {
			tour_next();
			return;
		}

		tour_get_current().tipsy('show');
	}
}

function tour_back() {
	if( (Tour_Current >= Tour.length) || (Tour_Current < -1) )
		tour_stop();

	tour_get_current().tipsy('hide');
	Tour_Current--;

	if(Tour_Current > -1) {
		if(!tour_get_current().is(':visible')) {
			tour_back();
			return;
		}

		tour_get_current().tipsy('show');
	}
}

function help_init(is_tour) {
	var visible_idx = 0;
	for(var i=0; i<Tour.length; i++) {
		var $div = tour_get(i);
		var text = '';

		if($div.is(':visible'))
			visible_idx++;

		//This is really ugly but i cant figure out a better way > its so that the correct mode button gets the right text for tour and help mode
		var inner_text = Tour[i]['text'].replace(/{MODE}/g, get_schedule_mode_text(Edit_Availability));
		inner_text = inner_text.replace(/{NOT_MODE}/g, get_schedule_mode_text(!Edit_Availability));

		if(is_tour)
			text =
						"<table><tr><th>" + visible_idx + "</th><td>" +
							inner_text +
						"</td></tr></table>" +
						"<p class='schedule_tour_buttons'>" +
							"<input type='button' value=' &laquo; ' onclick='tour_back(); return false;' />" +
							"<input type='button' style='margin: 0 14px;' value=' || ' onclick='tour_stop(); return false;' />" +
							"<input type='button' value=' &raquo; ' onclick='tour_next(); return false;' />" +
						"</p>";

		else
			text = inner_text;
//			text = "<div>" + Tour[i]['text'] + "</div>";

		$div.attr('original-title', text);

		var gravity_custom = 'n';
		if(typeof(Tour[i]['gravity']) != 'undefined')
			gravity_custom = Tour[i]['gravity'];

		var offset_custom = 0;
		if(typeof(Tour[i]['offset']) != 'undefined')
			offset_custom = Tour[i]['offset'];

		var options = {
			gravity: gravity_custom,
			offset: offset_custom,
			html:true
		};

		if(is_tour)
			options['trigger'] = 'manual';

		$div.tipsy(options);
	}
}

function tour_stop() {
	for(var i=0; i<Tour.length; i++) {
		tour_get(i)
					.tipsy('hide')
					.removeAttr('original-title')
					.removeData('tipsy');
	}
}

//{  selector: '',
//			gravity: '',
//			text: ""
//},

