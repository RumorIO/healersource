var $calendar;
var $timestampsOfOptions = {start:[], end:[]};
var AjaxCallback = null;
var RefreshCalendar = false;
var calEvent = null;
var dialog_is_active = false;
var current_mode = 'new';
var mode_data = {new: {id: '', container: '#new_appointment_container'},
	edit: {id: '_edit', container: '#edit_appointment_container'}};
var center_main_mode = false;
var schedule_available = true;
var is_wellness_center = false;
var initial_schedule_content_frame_css;
var schedule_full_width;
var overlapEventsSeparate;
var start_from_sunday;
var location_id = false;
var center_common_availability = false;

function fetchCalendar() {
	Dajaxice.healers.getTimeslotsEdit(populateCalendar, {'username': schedule_username});
}

function updatedList(result) {
	if (dajaxProcess(result)) return;
	if (result.message == '') {
		location.reload();
	} else {
		showResult(result.message, result.title);
	}
}

function get_treatment_name_and_cost(slot){
	var t_length = slot.treatment_length;
	if (t_length === 0)	{
		return 'Custom Treatment';
	}
	return Treatments[slot.treatment_length].name + ' - $' + slot.cost;
}

function updateAppointmentsList() {
	var unconfirmed_slots = UnconfirmedSlots;
	Timeslots.sort(function (a, b) {
		return a.start.compareTo(b.start);
	});
	unconfirmed_slots.sort(function (a, b) {
		return a.slot_id - b.slot_id;
	});

	updateConfirmedSlots();

	function updateConfirmedSlots() {
		$('#confirmed_appts').fadeOut(200);
		$('#no_confirmed_appts').fadeOut(200);
		$('#confirmed_appts_list').html("");
		var slots_count = 0;
		var confirmed_more = false;
		var new_week = false;
		var new_day = false;
		var sunday = Date.today().moveToDayOfWeek(0, -1);
		for (var i in Timeslots) {
			var slot = Timeslots[i];
			if (slot.unavailable != 1 || slot.timeoff == 1) continue;
			//slot = prepareDates(slot);

			if (slot.start < sunday) continue;
			if (slot.start >= confirmedListEndDate) {
				confirmed_more = true;
				continue;
			}

			new_week = addWeekDelimiter(new_week, slot);

			var row = $('<tr class="appointment_row"></tr>');
			new_day = addNewDayCell(new_day, slot, row);
			$('<td class="appt_cell_min" style="white-space:nowrap;"></td>')
					  .append('<span class="ui-icon ui-icon-refresh" style="display:inline; ' + (slot.repeat_period ? 'padding' : 'margin') + '-left:16px;" />')
					  .append(formatDateRange(slot.start, slot.end))
					  .appendTo(row);
			$('<td class="appt_cell_min" style="white-space:nowrap;"></td>')
					  .append(get_treatment_name_and_cost(slot))
					  .appendTo(row);
			$('<td class="appt_cell_min appt_cell_pointer"></td>')
					  .bind('click', {slot_ind:i}, function (event) {
						  dlg_appt_edit(Timeslots[event.data.slot_ind]);
						  RefreshCalendar = true;
					  })
					  .append("<img src='" + STATIC_URL + "healersource/img/edit.png' title='Edit' class='edit_appointment_button' />")
					  .appendTo(row);

			addClientCell(slot, row);

			if (_.keys(location_colors).length > 1) {
				$('<td class="appt_cell_max"></td>')
						  .append(slot.location_title.substr(0, 99))
						  .appendTo(row);
			}

			$('<td class="appt_cell_min appt_cell_pointer"></td>')
					  .bind('click', {slot_ind:i}, function (event) {
						  dlg_appt_delete(Timeslots[event.data.slot_ind]);
						  RefreshCalendar = true;
					  })
					  .append("<img src='" + STATIC_URL + "healersource/img/delete.png' title='Cancel' class='cancel_appointment_button' />")
					  .appendTo(row);
			row.appendTo($('#confirmed_appts_list'));
			slots_count++;
		}

		$('#confirmed_appts_more').toggle(confirmed_more);
		if (slots_count || confirmed_more) {
			$('#confirmed_appts').fadeIn(200);
		} else {
			$('#no_confirmed_appts').fadeIn(200);
		}
	}

	function addWeekDelimiter(new_week, slot) {
		return;
		if (new_week && new_week != slot.start.getWeekOfYear()) {
			$('<tr><td colspan="5"><hr/></td></tr>').appendTo($('#confirmed_appts_list'));
		}
		return slot.start.getWeekOfYear();
	}

	function addNewDayCell(new_day, slot, row) {
		if (new_day != slot.start.getDate()) {
			if (new_day)
				$('<tr><td colspan="99"><hr/></td></tr>').appendTo($('#confirmed_appts_list'));

			$('<td class="appt_cell_min" style="white-space:nowrap;"></td>').append(formatDay(slot.start)).appendTo(row);
		} else {
			$('<td></td>').appendTo(row);
		}
		return slot.start.getDate();
	}

	function addClientCell(slot, row) {
		var td = $('<td class="appt_cell_max"></td>');
		var a = $('<a href="/client/client_detail/' + slot.client + '/" class="client_detail floatbox" data-fb-options="type:ajax"' +
				  'onclick="fb.start(this); return false;">' + slot.client_name.substr(0, 99) + "</a>");
		td = td.append(a);
		td.appendTo(row);
	}

	function addLinks(link1, link2, row) {
		$('<td class="appt_cell_min" style="text-align: right;"></td>').append(link1).append(" | ").append(link2).appendTo(row);
	}

	function formatDay(date) {
		return date.toString('dddd, MMMM d');
	}

	function formatDateRange(start, end) {
		var second_part = "";
		if (end.getHours() === 0 && end.getMinutes() === 0)
			second_part = " - 24:00 pm";
		else
			second_part = end.toString(' - h:mm') + end.toString(' tt ').toLowerCase();
		return   start.toString('h:mm') + second_part;
	}

}

function disableInput(name) {
	var el = $('input[name=' + name + ']');
	el.attr('disabled', 'disabled');
	el.addClass('disabled');
}

function enableInput(name) {
	var el = $('input[name=' + name + ']');
	el.removeAttr('disabled');
	el.removeClass('disabled');
}

function resetForm($dialogContent) {
	$dialogContent.find("input").val("");
	$dialogContent.find("textarea").val("");
	$dialogContent.find("select").not('select[id="appointment_provider"],select[id="timeslot_provider"]').val("");
}

function getTimeFieldVal(field) {
	if (typeof field.timeEntry !== 'undefined')
		return field.timeEntry('getTime');
	else {
		var d = Date.parse(field.val());
		return d ? d : new Date(0);
	}
}

function setTimeFieldVal(field, val) {
	if (typeof field.timeEntry !== 'undefined')
		field.timeEntry('setTime', val);
	else {
		field.attr('readonly', true);
		var events = field.data('events');
		if (events && typeof events.click !== 'undefined')
			field.unbind('click');
		field.click(function(){
			dlg_time_picker_mobile(field);
			return false;
		});
		field.val(Date.parse(val).toString('h:mmtt'));
	}
	return field;
}

function initTimesOnChange(dialog) {
	var startField = dialog.find("input[name='start']");
	var endField = dialog.find("input[name='end']");
	var treatmentField = dialog.find("select[name='treatment_length']");

	startField.change(function () {
		if (treatmentField.val() === '0' || treatmentField.val() == null) {
			return;
		}
		var start = getTimeFieldVal(startField);
		var end = getTimeFieldVal(endField);
		var length = Treatments[treatmentField.val()].length;
		if (!start || !end) return;

		if (start > end || start.equals(end)) {
			var newEnd = start.clone().addMinutes(length);
			if (newEnd.getDay() == start.getDay())
				setTimeFieldVal(endField, newEnd);
		}
	});
	endField.change(function () {
		if (treatmentField.val() === '0' || treatmentField.val() == null) {
			return;
		}
		var start = getTimeFieldVal(startField);
		var end = getTimeFieldVal(endField);
		var length = Treatments[treatmentField.val()].length;
		if (!start || !end) return;

		if (start > end || start.equals(end)) {
			var newStart = end.clone().addMinutes(-length);
			if (newStart.getDay() == start.getDay())
				setTimeFieldVal(startField, newStart);
		}
	});
	treatmentField.change(function () {
		if (treatmentField.val() === '0') {
			dialog.find(".end_time_row").show();
		} else {
			dialog.find(".end_time_row").hide();

			var start = getTimeFieldVal(startField);
			var end = getTimeFieldVal(endField);
			var length = Treatments[treatmentField.val()].length;
			if (!start || !end) return;

			var newEnd = start.clone().addMinutes(length);
			if (newEnd.getDay() == start.getDay())
				setTimeFieldVal(endField, newEnd);
		}

		if (dialog_is_active) {
			hs_dialog("resize");
		}
	});
}

function initDatePicker() {
	$(".datepicker").datepicker();
	$(".datepicker").datepicker("disable");
}

function getAppointmentStartEnd(dialog) {
	var slot = {};
	var treatment_length = dialog.find("select[name='treatment_length']").val();
	var date = new Date(dialog.find("input[name='date']").val());
	var start_time = getTimeFieldVal(dialog.find("input[name='start']"));
	var start = date.clone();
	var end;
	start.setHours(start_time.getHours(), start_time.getMinutes());
	if (treatment_length === '0') {
		var end_time = getTimeFieldVal(dialog.find("input[name='end']"));
		end = date.clone();
		end.setHours(end_time.getHours(), end_time.getMinutes());
	} else {
		end = start.clone().addMinutes(Treatments[treatment_length].length);
	}

	slot.start = date.clone();
	slot.start.setHours(start.getHours(), start.getMinutes());

	slot.end = date.clone();
	slot.end.setHours(end.getHours(), end.getMinutes());
	if (end.getHours() === 0 && end.getMinutes() === 0) {
		slot.end.addDays(1);
	}
	return slot;
}


/**
 * @param   jQuery object  dialog     dialog window
 * @param   Number         room_id    room_id to select
 */
function updateRoomField(dialog, room_id) {
	// Get available rooms for chosen treatment type
	function get_available_rooms(){
		var treatment_length_id = dialog.find('select[name="treatment_length"]').val();
		var treatment_id = treatment_length_id != '0' ? Treatments[treatment_length_id].type : null;
		var rooms = treatment_id ? Treatments_Rooms[selected_username][treatment_id] : null;
		if(!rooms || rooms.length === 0) {
			rooms = All_Rooms;
		}
		return rooms;
	}

	// Filter rooms by selected location
	function filter_rooms_by_location() {
		var location_id = dialog.find('select[name="location"]').val();
		return rooms.filter(function(room) {return room.location == location_id;});
	}

	function exclude_busy_rooms(){
		var appointment = getAppointmentStartEnd(dialog);
		return rooms.filter(function(room) {
			return is_no_room_conflict(appointment, Timeslots, room.id);
		});
	}

	function create_room_select() {
		select.empty();
		for(var key in rooms) {
			var room = rooms[key];
			var selected = room.id == room_id;
			select.append(new Option(room.name, room.id, false, selected));
		}
	}

	function replace_select_with_text_if_room_are_not_available(){
		if (rooms.length === 0) {
			select.parent().children('span').html('No Rooms Available');
			select.hide();
		} else {
			select.parent().children('span').html('');
			select.show();
		}
	}

	function get_setup_time(){
		if (is_wellness_center) {
			user = $('#appointment_provider').val();
		} else {
			user = schedule_username;
		}
		return SetupTimes[user];
	}

	var rooms = get_available_rooms();
	rooms = filter_rooms_by_location();
	setupTime = get_setup_time();
	rooms = exclude_busy_rooms();

	var select = dialog.find('select[name="room"]');
	create_room_select();
	replace_select_with_text_if_room_are_not_available();
}

function updateDiscountField(dialog, code_id) {
	function create_discount_select() {
		select.empty();
		select.append(new Option('None', ''));
		for(var key in codes) {
			var code = codes[key];
			var selected = code.id == code_id;
			select.append(new Option(code.name, code.id, false, selected));
		}
	}

  	var location_id = dialog.find('select[name="location"]').val();
  	var codes = discount_codes[location_id];
	var select = dialog.find('select[name="discount_code"]');
	create_discount_select();
}

function updateTreatmentField(select, treatment_length_id, location_id) {
	function sortTreatments(){
		treatments.sort(function(a, b) {
			if (a.name.localeCompare(b.name) == -1) return -1;
			if (a.name.localeCompare(b.name) == 1) return 1;
			if (a.length < b.length) return -1;
			if (a.length > b.length) return 1;
			return 0;
		});
	}
	location_id = typeof location_id !== 'undefined' ? location_id : false;
	treatment_length_id = typeof treatment_length_id !== 'undefined' ? treatment_length_id : false;
	select.empty();
	var options = select.attr('options');
	var i = 0;
	var treatments = Treatments;
	if (location_id && !is_wellness_center) {
		treatments = Location_Treatments[location_id];
	}

	function filter_not_available_treatments(treatments){
		var available_treatments = Location_Available_Treatments[location_id];
		for (var treatment in treatments){
			if (available_treatments.indexOf(parseInt(treatment)) == -1) {
				delete treatments[treatment];
			}
		}
		return treatments;
	}
	if (location_id) {
		treatments = filter_not_available_treatments($.extend(true, {}, treatments));
	}
	treatments = $.map(treatments, function(value, index) {
		return [value];
	});
	sortTreatments();

	treatments.forEach(function(treatment_length){
		var selected = treatment_length.id == treatment_length_id;
		if ((!treatment_length.is_deleted || selected) &&
				  (typeof Provider_Treatments == 'undefined' ||
							 (treatment_length.id in Provider_Treatments[selected_username]))) {
			var title = treatment_length.is_deleted ? '[Deleted] ' + treatment_length.full_title : treatment_length.full_title;
			select.append(new Option(title, treatment_length.id, false, selected));
		}
	});

	var option_custom = new Option("Custom Treatment ----", 0, false, treatment_length_id === 0);
	option_custom.style.fontStyle = "italic";
	select.append(option_custom);

	// In case when there are no treatment types available, reset treatment_length_id
	// so that Custom Treatment type is selected correctly and end_time_row is displayed.
	if (select.children().length == 1) {
		treatment_length_id = 0;
	}

	if (treatment_length_id === 0) {
		$('.end_time_row').show();
	} else {
		$('.end_time_row').hide();
	}
	return select;
}

function updateLocationField(select, location_id, Locations_available) {
	Locations_available = typeof Locations_available !== 'undefined' ? Locations_available : Locations;
	select.empty();
	var options = select.attr('options');
	var i = 0;
	for (var key in Locations_available) {
		var loc = Locations_available[key];
		var selected = loc.id == location_id;
		if (!loc.is_deleted || selected) {
			var title = loc.is_deleted ? '[Deleted] ' + loc.text : loc.text;
			select.append(new Option(title, loc.id, false, selected));
		}
	}
}

function getLocation($dialog, select_name) {
	var select = $dialog.find("select[name='" + select_name + "']");
	if (select.length > 0) {
		return select.val();
	} else {
		return -1;
	}
}

//This is for the schedule tour
function get_schedule_mode_text(edit_availability_in) { return edit_availability_in ? 'Availability' : 'Appointments'; }

function toggle_schedule_mode() {
	if (Edit_Availability)
		set_schedule_mode('appointments');
	else
		set_schedule_mode('availability');
}

function hide_show_providers_if_center_common_availability(){
	if (!center_common_availability) {
		return;
	}
	if (Edit_Availability) {
		$('.schedule_provider_item').first().trigger('click');
		$('.schedule_provider_item_healer').hide();
	} else {
		$('.schedule_provider_item_healer').show();
	}
}

function set_schedule_mode(mode) {
	fb.end(1);

	if (mode == 'availability') {
		Edit_Availability = true;
		$('#appointments_view_selector').hide();
		$('#add_timeslot_type_selector').show();
		show_appointments_view_7_days();
	} else if (mode == 'appointments') {
		Edit_Availability = false;
		$('#appointments_view_selector').show();
		$('#add_timeslot_type_selector').hide();
	}
	hide_show_providers_if_center_common_availability();
	if ($('#appointments_view_list').is(":visible") && Edit_Availability) {
		$('#7_days_button').trigger('click');
	}
	populateCalendar(initSlots);

	toggle_help_mode('stop');
}

function show_appointments_view_7_days() {
	if ($('#appointments_view_list').is(":visible")) {
		$('#appointments_view_list').hide();
		$('#appointments_view_7_days').show();

		$('#appointments_view_7_days_button').addClass('selected');
		$('#appointments_view_list_button').removeClass('selected');
		$('#calendar').show();
		if (RefreshCalendar) {
			$('#calendar').weekCalendar('refresh');
			RefreshCalendar = false;
		}
		$('#location_bar_edit').show();
	}
}

function show_appointments_view_list() {
	if (is_wellness_center) {
		window.location.href = url_confirmed_appointments;
	} else {
		set_schedule_mode('appointments');
		if ($('#calendar').is(":visible")) {
			$('#calendar').hide();
			$('#appointments_view_list').show();
			$('#location_bar_edit').hide();
		}
	}
}

function initClientSearchAutocomplete() {
	$('#search_client' + mode_data[current_mode]['id']).autocomplete({
		source: function(request, response) {
			var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
			response($.grep(clients, function(value) {
				if ($('#search_client' + mode_data[current_mode]['id']).data('page') == 'list_intake_forms_page'){
					if(value.has_email){
						return matcher.test(value.value);
					}
				} else {
					return matcher.test(value.value);
				}
			}));
		},
		minLength: 2,
		html: true,
		autoFocus: true,
		appendTo: mode_data[current_mode]['container'],
		select: function(event, ui) {
			$('#search_client' + mode_data[current_mode]['id']).val(ui.item.value);
			$('#id_client' + mode_data[current_mode]['id']).val(ui.item.id);
			if (typeof(list_intake_forms_page) != 'undefined'){
				if (list_intake_forms_page){
					var client_id = $("#id_client").val();
					if (client_id) {
						send_intake_form(client_id);
					}
				}
			}
			$('#id_type' + mode_data[current_mode]['id']).val(ui.item.type);

			if(ui.item.type == 'contact' && ui.item.facebook_id)
				sendFacebookInvite(ui.item.id, ui.item.facebook_id, Healer_Name);

			update_new_appointment_notification(ui.item.has_email);
		}
	});
}

function update_new_appointment_notification (has_email) {
	if (has_email) {
		$('#send_new_appointment_notification').attr('checked', 'true');
		$('#send_new_appointment_notification').removeAttr('disabled');
		$('#send_new_appointment_notification_label').removeClass('disabled_text');
	} else {
		$('#send_new_appointment_notification').removeAttr('checked');
		$('#send_new_appointment_notification').attr('disabled', 'true');
		$('#send_new_appointment_notification_label').addClass('disabled_text');
	}
}

function newClientSuccess(client) {
	var $dlg = $(mode_data[current_mode]['container']);
	var $client_search = $dlg.find("#search_client" + mode_data[current_mode]['id']);
	if ($client_search.css('display') == 'none') $client_search.show();
	$client_search.val(client.value);

	var $client = $dlg.find("#id_client" + mode_data[current_mode]['id']);
	$client.val(client.id);

	update_new_appointment_notification(client.has_email);

	clients.push(client);
	initClientSearchAutocomplete();

}

function create_client_link(calEvent) {
	return '<a href="/client/client_detail/' + calEvent.client +
			  '/" class="client_detail floatbox" data-fb-options="type:ajax" onclick="fb.start(\'/client/client_detail/' + calEvent.client +
			  '/\', {\'measureHTML\': \'true\', \'width\': \'300\', \'height\': \'150\'}); return false;" style="text-decoration:underline;">' +
			  calEvent.client_name + '</a>';
}

function get_current_username(field){
	var new_username = $(field).val();
	if (new_username !== schedule_username) {
		return new_username;
	} else {
		return false;
	}
}

function switch_timeslot_mode(mode){
	if (mode == 'new') {
		$('#timeslot_new').show();
		$('#timeslot_edit').hide();
	} else {
		$('#timeslot_new').hide();
		$('#timeslot_edit').show();
	}
}

function get_selected_username(username){
	if (typeof username !== 'undefined') {
		return username;
	} else {
		return selected_username;
	}
}

function dlg_timeslot_new(calEvent) {
	switch_timeslot_mode('new');
	var $dlg_add_timeslot = $("#add_timeslot_dlg");

	if (!defaultTimeslotWeekly) {
		var data = {
			'start':stripTimezone(calEvent.start),
			'end':stripTimezone(calEvent.end),
			'end_date':'',
			'location_id':getLocation($dlg_add_timeslot, 'timeslot_location'),
			'weekly':defaultTimeslotWeekly,
			'username': $('#timeslot_provider').val()
		};
		current_username = get_current_username('#timeslot_provider');
		selected_username = get_selected_username($('#timeslot_provider').val());
		startCalendarRequest(calEvent, Dajaxice.healers.timeslot_new, data, updatedCalendar);

	} else {
		hs_dialog($dlg_add_timeslot, {
			title:"New Availability",
			open: function () {
				$("#timeslot_location_row").show();
			},
			close:function () {
				$('#calendar').weekCalendar("removeUnsavedEvents");
				disableMouseOverZIndexEvent();
				$('#timeslot_provider').val(schedule_username);
				selected_username = schedule_username;
				hs_dialog("close");
			},
			buttons:{
				"Save":function () {
					var start_time = getTimeFieldVal(startField);
					var end_time = getTimeFieldVal(endField);
					var start = new Date(startDateField.val());
					start.setHours(start_time.getHours(), start_time.getMinutes());
					var end = start.clone();
					var end_date;
					end.setHours(end_time.getHours(), end_time.getMinutes());

					var weekly = $dlg_add_timeslot.find("#timeslot_weekly1").attr("checked")=="checked";
					if(weekly) {
						var ongoing = $dlg_add_timeslot.find("#timeslot_ongoing1").attr("checked");
						end_date = endDateField.val() && !ongoing ? stripTimezone(new Date(endDateField.val())) : '';
					} else {
						end_date = stripTimezone(start);
					}

					var data =  {
						'start':stripTimezone(start),
						'end':stripTimezone(end),
						'end_date':end_date,
						'location_id':getLocation($dlg_add_timeslot, 'timeslot_location'),
						'weekly':weekly,
						'username': $('#timeslot_provider').val()
					};

					current_username = get_current_username('#timeslot_provider');
					startCalendarRequest(calEvent, Dajaxice.healers.timeslot_new, data, updatedCalendar);

					$calendar.weekCalendar("updateEvent", calEvent);
					$('#timeslot_provider').val(schedule_username);
					hs_dialog("close");
				}
			}
		});

		resetForm($dlg_add_timeslot);

		var startDateField = $dlg_add_timeslot.find("input[name='start_date']").val(calEvent.start.toString('MM/dd/yyyy'));
		var endDateField = $dlg_add_timeslot.find("input[name='end_date']").val(calEvent.start.clone().addWeeks(3).toString('MM/dd/yyyy'));
		$('#timeslot_start_end_dates').hide();
		$('#timeslot_weekly1').click();
		$('#timeslot_ongoing1').attr('checked', 'checked');
		$('#timeslot_repeat_options').show();
		$dlg_add_timeslot.find('#timeslot_provider').val(schedule_username);

		var startField = $dlg_add_timeslot.find("input[name='start']");
		setTimeFieldVal(startField, calEvent.start);
		var endField = $dlg_add_timeslot.find("input[name='end']");
		setTimeFieldVal(endField, calEvent.end);

		$dlg_add_timeslot.find(".date_holder").text(calEvent.start.toString('dddd, MMMM d'));
		$(".datepicker").datepicker("enable");

		if (current_location_id != "all")
			$dlg_add_timeslot.find("select[name='timeslot_location']").val(current_location_id);
		else
			$dlg_add_timeslot.find("select[name='timeslot_location']").val($dlg_add_timeslot.find("select[name='timeslot_location'] option:first").val());

	}
}

function dlg_timeslot_edit(calEvent) {
	switch_timeslot_mode('edit');
	var $dlg_edit_timeslot = $("#add_timeslot_dlg");
	hs_dialog($dlg_edit_timeslot, {
		title:"Edit Availability",
		open:function () {
			$("#timeslot_location_row").hide();
		},
		buttons:{
			Save:function () {
				var event_changed = false;
				var $event = $.extend(true, {}, calEvent); //deepcopy

				var start_old = calEvent.ostart ? calEvent.ostart : calEvent.start;
				var end_old = calEvent.oend ? calEvent.oend : calEvent.end;
				var weekly = $dlg_edit_timeslot.find("#timeslot_weekly1").attr("checked")=="checked";
				var ongoing = $dlg_edit_timeslot.find("#timeslot_ongoing1").attr("checked");

				var start_time = getTimeFieldVal(startField);
				var end_time = getTimeFieldVal(endField);
				var start_new = calEvent.start.clone();
				start_new.setHours(start_time.getHours(), start_time.getMinutes());
				var end_new = start_new.clone();
				end_new.setHours(end_time.getHours(), end_time.getMinutes());

				var start_date = null;
				if(weekly && !ongoing && startDateField.val()) {
					start_date = new Date(startDateField.val());
					calEvent.start_date = start_date;
				}

				var end_date;
				if(weekly) {
					end_date = endDateField.val() && !ongoing ? new Date(endDateField.val()) : '';
				} else {
					end_date = start_new;
				}

				if (start_old.getHours()!=start_new.getHours() || start_old.getMinutes()!=start_new.getMinutes())
					event_changed = true;
				if (end_old.getHours()!=end_new.getHours() || end_old.getMinutes()!=end_new.getMinutes())
					event_changed = true;
				calEvent.start = start_new;
				calEvent.end = end_new;
				calEvent.end_date = end_date;

				if (calEvent.repeat_period && event_changed) {
					hs_dialog('close');
					dlg_timeslot_reschedule_choice(calEvent, $event);
				} else {
					var data =  {
						'timeslot_id': calEvent.slot_id,
						'start_old': stripTimezone(start_old),
						'end_old': stripTimezone(end_old),
						'start_new': stripTimezone(start_new),
						'end_new': stripTimezone(end_new),
						'start_date': start_date ? stripTimezone(start_date) : '',
						'end_date': end_date ? stripTimezone(end_date) : '',
						'weekly_new': weekly,
						'all_slots': calEvent.repeat_period !== 0,
						'username': calEvent.healer_username
					};
					startCalendarRequest(calEvent, Dajaxice.healers.timeslot_update, data, updatedCalendar);

					$calendar.weekCalendar("updateEvent", calEvent);
					hs_dialog('close');
				}
			},
			Delete: {
				title: 'Delete',
				button_class: 'float_left',
				link_class: 'red_text',
				click:function () {
					if (calEvent.repeat_period) {
						hs_dialog("close");
						dlg_timeslot_delete_choice(calEvent);
					} else {
						var data = {
							'timeslot_id':calEvent.slot_id,
							'start':stripTimezone(calEvent.start),
							'all_slots':false,
							'username': calEvent.healer_username
						};
						startCalendarRequest(calEvent, Dajaxice.healers.timeslot_delete, data, updatedCalendar);

						$calendar.weekCalendar("removeEvent", calEvent.id);
						hs_dialog("close");
					}
				}
			}
		}
	});

	resetForm($dlg_edit_timeslot);

	var startDateField = $dlg_edit_timeslot.find("input[name='start_date']").val(calEvent.start_date.toString('MM/dd/yyyy'));
	var tmpEndDateVal = calEvent.start_date;
	tmpEndDateVal.setDate(tmpEndDateVal.getDate() + 7);
	var endDateField = $dlg_edit_timeslot.find("input[name='end_date']").val(tmpEndDateVal.toString('MM/dd/yyyy'));
	if (calEvent.end_date && calEvent.repeat_period) {
		endDateField.val(calEvent.end_date.toString('MM/dd/yyyy'));
		$('#timeslot_start_end_dates').show();
		$('#timeslot_ongoing2').attr('checked', 'checked');
	} else {
		$('#timeslot_start_end_dates').hide();
		$('#timeslot_ongoing1').attr('checked', 'checked');
	}
	if (calEvent.repeat_period) {
		$('#timeslot_weekly1').click();
	} else {
		$('#timeslot_weekly2').click();
	}

	var startField = $dlg_edit_timeslot.find("input[name='start']");
	setTimeFieldVal(startField, calEvent.ostart ? calEvent.ostart : calEvent.start);
	var endField = $dlg_edit_timeslot.find("input[name='end']");
	setTimeFieldVal(endField, calEvent.oend ? calEvent.oend : calEvent.end);
	$dlg_edit_timeslot.find(".date_holder").text(calEvent.start.toString('dddd, MMMM d'));

	$(".datepicker").datepicker("enable");

	$dlg_edit_timeslot.find('.healer_name').html(calEvent.healer_name);
}

function dlg_timeslot_reschedule_choice(calEvent, $event) {
	var $dlg_timeslot_reschedule_choice = $("#confirm_timeslot_reschedule_all");
	var reloadCalendarOnClose = true;
	var data = {
		'timeslot_id':calEvent.slot_id,
		'start_new':stripTimezone(calEvent.start),
		'end_new':stripTimezone(calEvent.end),
		'start_date':calEvent.end_date && calEvent.repeat_period !== 0 ? stripTimezone(calEvent.start_date) : '',
		'end_date':calEvent.end_date && calEvent.repeat_period !== 0 ? stripTimezone(calEvent.end_date) : '',
		'weekly_new':calEvent.repeat_period !== 0,
		'username': calEvent.healer_username
	};

	hs_dialog($dlg_timeslot_reschedule_choice, {
		title:"Reschedule Availability",
		close: function() {
			if (reloadCalendarOnClose) getCalendar();
		},
		buttons:{
			"Just This One":function () {
				$.extend(data, {
					all_slots: false,
					start_old: stripTimezone($event.ostart ? $event.ostart : $event.start),
					end_old: stripTimezone($event.oend ? $event.oend : $event.end)
				});
				startCalendarRequest(calEvent, Dajaxice.healers.timeslot_update, data, updatedCalendar);

				$calendar.weekCalendar("updateEvent", calEvent);
				reloadCalendarOnClose = false;
				hs_dialog('close');
			},
			"All Weeks": {
				title: 'All Weeks',
				button_class: 'float_left',
				click: function () {
					$.extend(data, {
						all_slots: true,
						start_old: stripTimezone($event.ostart ? $event.ostart : $event.start),
						end_old: stripTimezone($event.oend ? $event.oend : $event.end)
					});
					startCalendarRequest(calEvent, Dajaxice.healers.timeslot_update, data, updatedCalendar);

					$calendar.weekCalendar("updateEvent", calEvent);
					reloadCalendarOnClose = false;
					hs_dialog('close');
				}
			}
		}
	});
}

function dlg_timeslot_delete_choice(calEvent) {
	var $dialogConfirmDelete = $("#confirm_timeslot_delete_all");
	var data = {
		timeslot_id: calEvent.slot_id,
		start: stripTimezone(calEvent.start),
		username: calEvent.healer_username
	};

	hs_dialog($dialogConfirmDelete, {
		title:"Delete Availability",
		buttons:{
			"Just This One":function () {
				data['all_slots'] = false;
				startCalendarRequest(calEvent, Dajaxice.healers.timeslot_delete, data, updatedCalendar);
				hs_dialog("close");
			},
			"All Weeks": {
				title: 'All Weeks',
				button_class: 'float_left',
				click: function () {
					data['all_slots'] = true;
					startCalendarRequest(calEvent, Dajaxice.healers.timeslot_delete, data, updatedCalendar);
					hs_dialog("close");
				}
			},
			"This and All Future": {
				title: 'This and All Future',
				button_class: 'float_left',
				click: function () {
					delete(data['all_slots']);
					startCalendarRequest(calEvent, Dajaxice.healers.timeslot_delete_future, data, updatedCalendar);
					hs_dialog("close");
				}
			}
		}
	});
}

function dlg_timeoff_new() {
	var $dialog = $("#add_timeoff_dlg");
	var start_date_field = $dialog.find("input[name=start_date]");
	var end_date_field = $dialog.find("input[name=end_date]");
	var start_time_field = $dialog.find("input[name=start_time]");
	var end_time_field = $dialog.find("input[name=end_time]");
	hs_dialog($dialog, {
		title: "Add Time Off",
		outsideClickCloses: false,
		open: function () {
			resetForm($dialog);

			$dialog.find('#all_day').attr('checked', true);
			update_timeoff_dlg_all_day();

			var date = new Date();
			start_date_field.val(date.toString('MM/dd/yyyy'));
			end_date_field.val(date.toString('MM/dd/yyyy'));

			$(".datepicker").datepicker("enable");
		},
		close: function () {
			$(".datepicker").datepicker("disable");
		},
		buttons:{
			Save : function () {
				var start_date = new Date(start_date_field.val());
				var end_date = new Date(end_date_field.val());
				if($dialog.find('#all_day').attr('checked')) {
					start_date.setHours(0, 0);
					end_date.setHours(23, 59);
				} else {
					var start_time = getTimeFieldVal(start_time_field);
					start_date.setHours(start_time.getHours(), start_time.getMinutes());
					var end_time = getTimeFieldVal(end_time_field);
					end_date.setHours(end_time.getHours(), end_time.getMinutes());
				}

				var data = {
					'start':stripTimezone(start_date),
					'end':stripTimezone(end_date),
					'username': schedule_username
				};
				startCalendarRequest(calEvent, Dajaxice.healers.timeoff_new, data, updatedCalendar);

				hs_dialog("close");
			}
		}
	});
}

function dlg_timeoff_edit(calEvent) {
	var $dialog = $("#add_timeoff_dlg");
	var start_date_field = $dialog.find("input[name=start_date]");
	var end_date_field = $dialog.find("input[name=end_date]");
	var start_time_field = $dialog.find("input[name=start_time]");
	var end_time_field = $dialog.find("input[name=end_time]");
	hs_dialog($dialog, {
		title: "Edit Time Off",
		outsideClickCloses: false,
		open: function () {
			resetForm($dialog);

			var all_day = calEvent.start.getHours() === 0 && calEvent.start.getMinutes() === 0 &&
					  calEvent.end.getHours()==23 && calEvent.end.getMinutes()==59;
			$dialog.find("#all_day").attr("checked", all_day);
			update_timeoff_dlg_all_day();

			start_date_field.val(calEvent.start.toString('MM/dd/yyyy'));
			setTimeFieldVal(start_time_field, calEvent.start);
			end_date_field.val(calEvent.end.toString('MM/dd/yyyy'));
			setTimeFieldVal(end_time_field, calEvent.end);

			$(".datepicker").datepicker("enable");
		},
		close: function () {
			$(".datepicker").datepicker("disable");
		},
		buttons:{
			Save: function () {
				var start_date = new Date(start_date_field.val());
				var end_date = new Date(end_date_field.val());
				if($dialog.find('#all_day').attr('checked')) {
					start_date.setHours(0, 0);
					end_date.setHours(23, 59);
				} else {
					var start_time = getTimeFieldVal(start_time_field);
					start_date.setHours(start_time.getHours(), start_time.getMinutes());
					var end_time = getTimeFieldVal(end_time_field);
					end_date.setHours(end_time.getHours(), end_time.getMinutes());
				}

				var data = {
					'timeslot_id':calEvent.slot_id,
					'start':stripTimezone(start_date),
					'end':stripTimezone(end_date),
					'username': schedule_username
				};
				startCalendarRequest(calEvent, Dajaxice.healers.timeoff_update, data, updatedCalendar);

				hs_dialog("close");
			},
			Delete: {
				title: 'Delete',
				button_class: 'float_left',
				link_class: 'red_text',
				click:function () {
					hs_dialog("close");
					dlg_timeoff_delete(calEvent);
				}
			}
		}
	});
}

function dlg_timeoff_delete(calEvent) {
	var $dialog = $("#delete_timeoff_dlg");
	hs_dialog($dialog, {
		title:"Delete Time Off",
		buttons:{
			No:function () {
				hs_dialog("close");
			},
			Yes:function () {
				var data = {
					'timeslot_id':calEvent.slot_id,
					'username': schedule_username
				};
				startCalendarRequest(calEvent, Dajaxice.healers.timeoff_delete, data, updatedCalendar);
				hs_dialog("close");
			}
		}
	});
}

function dlg_appt_new(calEvent) {
	var $dialogNewAppt = $("#new_appointment_container");
	hs_dialog($dialogNewAppt, {
		title: "New Appointment",
		outsideClickCloses: false,
		open: function () {
			resetForm($dialogNewAppt);
			var $treatment_select = $dialogNewAppt.find("select[name='treatment_length']");
			updateTreatmentField($treatment_select);
			var treatment = Treatments[$treatment_select.val()];
			var length;
			if ((!treatment) || ((calEvent.end - calEvent.start) != defaultTimeslotLength * 1800000)) {
				length = (calEvent.end - calEvent.start) / 60000;
				$dialogNewAppt.find(".end_time_row").show();
				$treatment_select.attr('value', 0);
			} else {
				length = treatment.length;
				$dialogNewAppt.find(".end_time_row").hide();
			}

			$dialogNewAppt.find("input[name='date']").val(calEvent.start.toString('MM/dd/yyyy'));
			setTimeFieldVal($dialogNewAppt.find("input[name='start']"), calEvent.start);
			setTimeFieldVal($dialogNewAppt.find("input[name='end']"), calEvent.start.clone().addMinutes(length));

			$dialogNewAppt.find('#appointment_provider').val(schedule_username);
			$dialogNewAppt.find("#appointment_new_repeat").removeAttr('checked');
			$dialogNewAppt.find('#appointment_new_repeat_options').hide();
			$dialogNewAppt.find("input[name='repeat_every']").val(1);
			$dialogNewAppt.find("select[name='repeat_period']").val(2);
			$dialogNewAppt.find("input[name='repeat_count']").val(10);
			$dialogNewAppt.find("#end_after_radio1").attr('checked', 'checked');
			disableInput('repeat_count');
			$dialogNewAppt.find("textarea[name='note']").val();

			selected_username = get_selected_username($dialogNewAppt.find('#appointment_provider').val());

			var location_field = $dialogNewAppt.find("select[name='location']");
			updateLocationField(location_field);


			if (current_location_id != "all")
				location_field.val(current_location_id);
			else
				location_field.val($dialogNewAppt.find("select[name='location'] option:first").val());
			$dialogNewAppt.find("select[name='location']").trigger('change');

			updateRoomField($dialogNewAppt);

			update_new_appointment_notification (false);
			$(".datepicker").datepicker("enable");
			dialog_is_active = true;
		},
		close: function () {
			$('#calendar').weekCalendar("removeUnsavedEvents");
			disableMouseOverZIndexEvent();
			$(".datepicker").datepicker("disable");
			$('.ui-autocomplete').hide();
			Location_Treatments = Location_Treatments_original;
			dialog_is_active = false;
			selected_username = schedule_username;
		},
		buttons:{
			Save : function () {
				var client_id = $dialogNewAppt.find("input[name='client']").val();
				client_id = client_id ? client_id : 0;
				var client_type = $dialogNewAppt.find("input[name='client_type']").val();
				var treatment_length = parseInt($dialogNewAppt.find("select[name='treatment_length']").val());
				var date = new Date($dialogNewAppt.find("input[name='date']").val());
				var start_time = getTimeFieldVal($dialogNewAppt.find("input[name='start']"));
				var start = date.clone();
				start.setHours(start_time.getHours(), start_time.getMinutes());
				var end;
				if (treatment_length === 0) {
					var end_time = getTimeFieldVal($dialogNewAppt.find("input[name='end']"));
					end = date.clone();
					end.setHours(end_time.getHours(), end_time.getMinutes());
				} else {
					end = start.clone().addMinutes(Treatments[treatment_length].length);
				}
				var note = $dialogNewAppt.find("textarea[name='note']").val();
				var repeat_period = NaN;
				var repeat_every = NaN;
				var repeat_count = NaN;
				if ($dialogNewAppt.find("#appointment_new_repeat").attr("checked")) {
					repeat_period = $dialogNewAppt.find("select[name='repeat_period']").val();
					repeat_every = $dialogNewAppt.find("input[name='repeat_every']").val();
					if ($dialogNewAppt.find("#end_after_radio2").attr("checked")) {
						repeat_count = $dialogNewAppt.find("input[name='repeat_count']").val();
					}
				}

				var location_id = getLocation($dialogNewAppt, 'location');
				var room_id = $dialogNewAppt.find("select[name='room']").val();
				if (!is_valid_room(room_id, location_id)) { return; }
				var data = {
					'client_id':client_id,
					'client_type':client_type,
					'start':stripTimezone(start),
					'end':stripTimezone(end),
					'location': location_id,
					'treatment_length':treatment_length,
					'repeat_period':repeat_period,
					'repeat_every':repeat_every,
					'repeat_count':repeat_count,
					'conflict_solving':0,
					'note':note,
					'notify_client':get_send_notification('#send_new_appointment_notification'),
					'username': $('#appointment_provider').val(),
					'room_id': room_id,
					'discount_code': $dialogNewAppt.find('select[name="discount_code"]').val()
				};
				current_username = get_current_username('#appointment_provider');
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_new, data, updatedCalendar);
				$('#appointment_provider').val(schedule_username);
				hs_dialog("close");
			}
		}
	});
}

function getClient(){
	var dlg = $("#edit_appointment_container");
	var client_id = dlg.find("#id_client_edit").val();
	if (typeof client_id === 'undefined') {
		return false;
	}
	var client_type = dlg.find("#id_client_type").val();
	return {id: client_id, type: client_type};
}

function dlg_appt_edit(calEvent, callback, healer_id) {
	healer_id = typeof healer_id !== 'undefined' ? healer_id : false;

	AjaxCallback = callback;
	var container_name = "#edit_appointment_container";
	if (healer_id) {
		container_name += '_' + String(healer_id);
	}
	var $dlg_appt_edit = $(container_name);
	var client_link = create_client_link(calEvent);
	var clientField = $dlg_appt_edit.find("#client_name");
	var dateField = $dlg_appt_edit.find("input[name='date']");
	var startField = $dlg_appt_edit.find("input[name='start']");
	var endField = $dlg_appt_edit.find("input[name='end']");
	var locationField = $dlg_appt_edit.find("select[name='location']");
	var treatmentField = $dlg_appt_edit.find("select[name='treatment_length']");
	var noteField = $dlg_appt_edit.find("textarea[name='note']");
	var roomField = $dlg_appt_edit.find("select[name='room']");
	var discountField = $dlg_appt_edit.find('select[name="discount_code"]');
	var action_links = $dlg_appt_edit.find(".action_links");
	var repeat = $dlg_appt_edit.find("#appointment_repeat");
	var repeat_options = $dlg_appt_edit.find("#appointment_repeat_options");
	var repeat_every = $dlg_appt_edit.find("#repeat_every_input");
	var repeat_period = $dlg_appt_edit.find("select[name='repeat_period']");
	var repeat_ongoing = $dlg_appt_edit.find("#end_after_radio1");
	var repeat_end_after = $dlg_appt_edit.find("#end_after_radio2");
	var repeat_count = $dlg_appt_edit.find("#repeat_count_input");
	var reload_calendar = false;

	if (healer_id) {
		$dlg_appt_edit.find(".healer_name").html(Names[healer_id]);
	}

	hs_dialog($dlg_appt_edit, {
		title: "Edit Appointment",
		dont_auto_focus: true,
		outsideClickCloses: false,
		open: function () {
			function activate_action_links(){
				if(calEvent.has_intake) {
					activate_intake_button(calEvent, action_links.find('.intake_link'));
					action_links.find('.separator').show();
				}

				if(calEvent.unavailable) {
					activate_notes_button(calEvent, action_links.find('.notes_link'));
				}
			}

			resetForm($dlg_appt_edit);
			$dlg_appt_edit.find('.healer_name').html(calEvent.healer_name);
			clientField.html(client_link);
			fb.activate(client_link);

			dateField.val(calEvent.start.toString('MM/dd/yyyy'));
			updateTreatmentField(treatmentField, calEvent.treatment_length, calEvent.location);
			updateLocationField(locationField, calEvent.location);

			setTimeFieldVal(startField, calEvent.start);
			setTimeFieldVal(endField, calEvent.end);
			noteField.val(calEvent.note);
			if (calEvent.client_has_email) {
				$('#send_update_notification').attr('checked', 'true');
				$('#send_update_notification').removeAttr('disabled');
				$('#send_update_notification_label').removeClass('disabled_text');
			} else {
				$('#send_update_notification').attr('disabled', 'true');
				$('#send_update_notification').removeAttr('checked');
				$('#send_update_notification_label').addClass('disabled_text');
			}
			selected_username = calEvent.healer_username;
			treatmentField.trigger('change');
			show_or_hide_room_row($dlg_appt_edit, calEvent.location);
			updateRoomField($dlg_appt_edit, calEvent.room);
			updateDiscountField($dlg_appt_edit, calEvent.discount_code);
			$(".datepicker").datepicker("enable");
			action_links.find('.separator').hide();
			activate_action_links();

			if(calEvent.repeat_period) {
				repeat.attr('checked', 'true');
				repeat_options.toggle(true);
				repeat_every.val(calEvent.repeat_every);
				repeat_period.val(calEvent.repeat_period);
				if(calEvent.repeat_count) {
					repeat_end_after.attr('checked', 'true');
					repeat_count.val(calEvent.repeat_count);
				} else {
					repeat_ongoing.attr('checked', 'true');
					repeat_count.val('');
				}
			} else {
				repeat.removeAttr('checked');
				repeat_options.toggle(false);
				repeat_every.val('');
				repeat_period.find('option').removeAttr('selected');
				repeat_ongoing.attr('checked', 'true');
				repeat_count.val('');
			}

		},
		close: function () {
			$(".datepicker").datepicker("disable");
			$dlg_appt_edit.find('.client_content').html('<span id="client_name"></span> | <a href="#" class="edit_client">edit</a>');
			activate_client_edit();
			current_mode = 'new';
			selected_username = schedule_username;
			if (reload_calendar) { getCalendar(); }
		},
		buttons:{
			Save : function () {
				var $event = $.extend(true, {}, calEvent); //deepcopy

				var event_changed = false;
				var note_changed = false;

				if (calEvent.treatment_length != treatmentField.val()) event_changed = true;
				calEvent.treatment_length = treatmentField.val();

				var date = new Date(dateField.val());
				var start_time = getTimeFieldVal(startField);
				var start = date.clone();
				start.setHours(start_time.getHours(), start_time.getMinutes());
				var end;
				if (calEvent.treatment_length === '0') {
					var end_time = getTimeFieldVal(endField);
					end = date.clone();
					end.setHours(end_time.getHours(), end_time.getMinutes());
				} else {
					end = start.clone().addMinutes(Treatments[calEvent.treatment_length].length);
				}

				if (!calEvent.start.equals(start)) event_changed = true;
				calEvent.start = date.clone();
				calEvent.start.setHours(start.getHours(), start.getMinutes());

				if (!calEvent.end.equals(end)) event_changed = true;
				calEvent.end = date.clone();
				calEvent.end.setHours(end.getHours(), end.getMinutes());
				if (end.getHours() === 0 && end.getMinutes() === 0) {
					calEvent.end.addDays(1);
				}

				if (calEvent.room != roomField.val()) event_changed = true;
				calEvent.room = roomField.val();
				if (calEvent.location != locationField.val()) event_changed = true;
				calEvent.location = locationField.val();

				if (calEvent.note != noteField.val()) note_changed = true;
				calEvent.note = noteField.val();

				if (calEvent.discount_code != discountField.val()) event_changed = true;
				calEvent.discount_code = discountField.val();

				var client = getClient();
				if (client) {
					event_changed = true;
				}
				if (event_changed || note_changed) {
					var location_id = getLocation($dlg_appt_edit, 'location');
					if (!is_valid_room(calEvent.room, location_id)) {
						calEvent = $event;
						reload_calendar = true;
						return;
					} else {
						reload_calendar = false;
					}
					if (calEvent.repeat_period && event_changed) {
						hs_dialog("close");
						dlg_appt_reschedule_choice(calEvent, $event, callback, true);
					} else {
						var data = {
							'appointment':calEvent.slot_id,
							'start_old':stripTimezone($event.start),
							'end_old':stripTimezone($event.end),
							'start_new':stripTimezone(calEvent.start),
							'end_new':stripTimezone(calEvent.end),
							'treatment_length':calEvent.treatment_length,
							'location_new': location_id,
							'note':calEvent.note,
							'conflict_solving':0,
							'all_slots':calEvent.repeat_period ? true : false,
							'notify_client':get_send_notification('#send_update_notification'),
							'username': calEvent.healer_username,
							'room_id': calEvent.room,
							'discount_code': calEvent.discount_code,

						};
						if (client) {
							data['client_id'] = client['id'];
							data['client_type'] = client['type'];
						}
						if (healer_id) {
							data['timeout_id'] = 99999999;
							Dajaxice.healers.appointment_update(callback, data);
						} else {
							startCalendarRequest(calEvent, Dajaxice.healers.appointment_update, data, callback ? callback : updatedCalendar);
						}

					}
				}
				hs_dialog("close");
			},
			Delete: {
				title: 'Delete',
				button_class: 'float_left',
				link_class: 'red_text',
				click: function () {
					hs_dialog("close");
					dlg_appt_delete(calEvent, callback);
				}
			}
		}
	});
}

function dlg_appt_reschedule_single(calEvent, $event, callback, from_edit_dialog) {

	var $dialogConfirmReschedule = $("#confirm_reschedule");
	var reloadCalendarOnClose = true;
	var start_old = stripTimezone($event.start);
	var end_old = stripTimezone($event.end);
	var start_new = stripTimezone(calEvent.start);
	var end_new = stripTimezone(calEvent.end);
	var location_new = from_edit_dialog ? getLocation($("#edit_appointment_container"), 'location') : $event.location;

	$("#reschedule_time").html("");
	$("#reschedule_time").append($calendar.weekCalendar("formatDate", calEvent.start, "l, n/j"));
	$("#reschedule_time").append("<br/>");
	$("#reschedule_time").append($calendar.weekCalendar("formatTime", calEvent.start, "g:i") + " - " + $calendar.weekCalendar("formatTime", calEvent.end, 'g:i a'));

	hs_dialog($dialogConfirmReschedule, {
		title: "Reschedule Appointment",
		close:function (event, ui) {
			if (reloadCalendarOnClose) getCalendar();
		},
		buttons:{
			No:function () {
				hs_dialog("close");
			},
			Yes:function () {
				if (!is_valid_room(calEvent.room, location_new)) { return; }

				var data = {	'appointment':calEvent.slot_id,
					'start_old':start_old,
					'end_old':end_old,
					'start_new':start_new,
					'end_new':end_new,
					'location_new':location_new,
					'treatment_length':calEvent.treatment_length,
					'note':calEvent.note,
					'conflict_solving':0,
					'all_slots':false,
					'notify_client':get_send_notification('#send_update_notification'),
					'username': calEvent.healer_username,
					'room_id':calEvent.room,
					'discount_code': calEvent.discount_code,
				};
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_update, data, callback ? callback : updatedCalendar);

				reloadCalendarOnClose = false;
				hs_dialog("close");
			}
		}
	});
}

function dlg_appt_reschedule_choice(calEvent, $event, callback, from_edit_dialog) {

	var $dialogConfirmReschedule = $("#confirm_reschedule_all");
	var reloadCalendarOnClose = true;
	var start_old = stripTimezone($event.start);
	var end_old = stripTimezone($event.end);
	var start_new = stripTimezone(calEvent.start);
	var end_new = stripTimezone(calEvent.end);
	var location_new = from_edit_dialog ? getLocation($("#edit_appointment_container"), 'location') : $event.location;
	var client = getClient();
	var data = {
		'appointment':calEvent.slot_id,
		'start_old':start_old,
		'end_old':end_old,
		'start_new':start_new,
		'end_new':end_new,
		'treatment_length':calEvent.treatment_length,
		'location_new':location_new,
		'note':calEvent.note,
		'conflict_solving':0,
		'all_slots':false,
		'notify_client':get_send_notification('#send_update_notification'),
		'username': calEvent.healer_username,
		'room_id': calEvent.room,
		'discount_code': calEvent.discount_code,
	};
	if (client) {
		data['client_id'] = client['id'];
		data['client_type'] = client['type'];
	}
	hs_dialog($dialogConfirmReschedule, {
		title: "Reschedule Appointment",
		close:function () {
			if (reloadCalendarOnClose) getCalendar();
		},
		buttons:{
			"Just This One":function () {
				if (!is_valid_room(calEvent.room, location_new)) { return; }
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_update, data, callback ? callback : updatedCalendar);

				reloadCalendarOnClose = false;
				hs_dialog("close");
			},
			"All Appointments": {
				title: 'All Appointments',
				button_class: 'float_left',
				click: function () {
					if (!is_valid_room(calEvent.room, location_new)) { return; }
					data['all_slots'] = true;

					startCalendarRequest(calEvent, Dajaxice.healers.appointment_update, data, callback ? callback : updatedCalendar);

					reloadCalendarOnClose = false;
					hs_dialog("close");
				}
			}
		}
	});
}

function dlg_appt_reschedule_conflict_solving(calEvent, exceptions, available_dates, client_type, timeout_id, start_old, end_old, start_new, end_new) {

	if (timeout_id) clearTimeout(timeout_id);
	var $dialogConflictsSolving = $("#conflicts_solving");
	var reduce_to = calEvent.repeat_count - calEvent.exceptions.length - exceptions.length;
	$dialogConflictsSolving.find("#slot_exceptions").html(exceptions.join(", "));
	if (reduce_to > 0) {
		$dialogConflictsSolving.find("#slot_reduce_count").html(reduce_to);
		$dialogConflictsSolving.find("#reduce_option").show();
	} else {
		$dialogConflictsSolving.find("#reduce_option").hide();
	}
	if (available_dates.length > 0) {
		$dialogConflictsSolving.find("#slot_available_dates").html(available_dates.join(", "));
		$dialogConflictsSolving.find("#reschedule_option").show();
	} else {
		$dialogConflictsSolving.find("#reschedule_option").hide();
	}
	if (reduce_to > 0 && available_dates.length > 0) {
		$dialogConflictsSolving.find("#options_join").show();
	} else {
		$dialogConflictsSolving.find("#options_join").hide();
	}


	var buttonsOpts = {};
	var data;
	if (available_dates.length > 0) {
		buttonsOpts.Reschedule = function () {
			if (!is_valid_room(calEvent.room, calEvent.location)) { return; }

			if (calEvent.slot_id) {
				data = {
					'appointment':calEvent.slot_id,
					'start_old':start_old,
					'end_old':end_old,
					'start_new':start_new,
					'end_new':end_new,
					'treatment_length':calEvent.treatment_length,
					'location_new':calEvent.location,
					'note':calEvent.note,
					'conflict_solving':2,
					'all_slots':true,
					'notify_client':get_send_notification('#send_update_notification'),
					'username':calEvent.healer_username,
					'room_id':calEvent.room,
					'discount_code': calEvent.discount_code,
				};
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_update, data, AjaxCallback ? AjaxCallback : updatedCalendar);
			} else {
				calEvent = prepareDates(calEvent);
				data = {
					'client_id':calEvent.client_id,
					'client_type':client_type,
					'start':stripTimezone(calEvent.start),
					'end':stripTimezone(calEvent.end),
					'location':calEvent.location,
					'treatment_length':calEvent.treatment_length,
					'repeat_period':calEvent.repeat_period,
					'repeat_every':calEvent.repeat_every,
					'repeat_count':calEvent.repeat_count,
					'conflict_solving':2,
					'note':calEvent.note,
					'notify_client':get_send_notification('#send_new_appointment_notification'),
					'username':calEvent.healer_username,
					'room_id':calEvent.room,
					'discount_code': calEvent.discount_code,
				};
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_new, data, AjaxCallback ? AjaxCallback : updatedCalendar);
			}
			hs_dialog("close");
		};
	}
	if (reduce_to > 0) {
		buttonsOpts["Reduce to " + reduce_to] = function () {
			if (!is_valid_room(calEvent.room, calEvent.location)) { return; }
			if (calEvent.slot_id) {
				data = {
					'appointment': calEvent.slot_id,
					'start_old': start_old,
					'end_old': end_old,
					'start_new': start_new,
					'end_new': end_new,
					'treatment_length': calEvent.treatment_length,
					'location_new': calEvent.location,
					'note': calEvent.note,
					'conflict_solving': 1,
					'all_slots': true,
					'notify_client': get_send_notification('#send_update_notification'),
					'username': calEvent.healer_username,
					'room_id': calEvent.room,
					'discount_code': calEvent.discount_code,
				};
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_update, data, AjaxCallback ? AjaxCallback : updatedCalendar);
			} else {
				calEvent = prepareDates(calEvent);
				data = {
					'client_id': calEvent.client_id,
					'client_type': client_type,
					'start': stripTimezone(calEvent.start),
					'end': stripTimezone(calEvent.end),
					'location': calEvent.location,
					'treatment_length': calEvent.treatment_length,
					'repeat_period': calEvent.repeat_period,
					'repeat_every': calEvent.repeat_every,
					'repeat_count': calEvent.repeat_count,
					'conflict_solving': 1,
					'note': calEvent.note,
					'notify_client': get_send_notification('#send_new_appointment_notification'),
					'username': calEvent.healer_username,
					'room_id': calEvent.room,
					'discount_code': calEvent.discount_code,
				};
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_new, data, AjaxCallback ? AjaxCallback : updatedCalendar);
			}
			hs_dialog("close");
		};
	}

	hs_dialog($dialogConflictsSolving, {
		'title': "Appointment Conflicts",
		close: function () {
			getCalendar(initSlots);
		},
		buttons:buttonsOpts
	});

}

function dlg_appt_delete(calEvent, callback) {

	AjaxCallback = callback;
	var id_suffix = calEvent.repeat_period ? '_r' : '';
	$("#dialog_client" + id_suffix).text(calEvent.client_name);
	$("#dialog_date" + id_suffix).text(calEvent.start.toString("dddd, M/d"));
	$("#dialog_time" + id_suffix).text(calEvent.start.toString("h:mm") + " - " + calEvent.end.toString("h:mm"));
	$("#dialog_location" + id_suffix).text(calEvent.location_title);

	if (calEvent.note && calEvent.note.length > 0) {
		$("#dialog_note" + id_suffix).text(calEvent.note);
		$("#dialog_note_item" + id_suffix).show();
	} else {
		$("#dialog_note_item" + id_suffix).hide();
	}
	if (calEvent.repeat_period) {
		var period = repeatChoices[calEvent.repeat_period];
		period += calEvent.repeat_every > 1 ? 's' : '';
		$("#dialog_repeat_r").text("Repeats every " + calEvent.repeat_every + " " + period);
	}

	if (calEvent.repeat_period) {
		dlg_appt_delete_choice(calEvent, callback);
	} else {
		dlg_appt_delete_single(calEvent, callback);
	}
}

function dlg_appt_delete_single(calEvent, callback) {

	var $dialogConfirmDelete = $("#confirm_delete");
	hs_dialog($dialogConfirmDelete, {
		title:"Delete Appointment",
		buttons:{
			No:function () {
				hs_dialog("close");
			},
			Yes:function () {
				var data = {
					'appointment':calEvent.slot_id,
					'start':stripTimezone(calEvent.start),
					'all_slots':false,
					'notify_client':get_send_notification('#send_update_notification'),
					'username':calEvent.healer_username
				};
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_delete, data, callback ? callback : updatedCalendar);
				hs_dialog("close");
			}
		}
	});
}

function dlg_appt_delete_choice(calEvent, callback) {

	var $dialogConfirmDelete = $("#confirm_delete_all");
	var data = {
		'appointment':calEvent.slot_id,
		'start':stripTimezone(calEvent.start),
		'notify_client':get_send_notification('#send_update_notification'),
		'username':calEvent.healer_username
	};
	hs_dialog($dialogConfirmDelete, {
		title:"Delete Appointment",
		buttons:{
			"Just This One":function () {
				data['all_slots'] = false;
				startCalendarRequest(calEvent, Dajaxice.healers.appointment_delete, data, callback ? callback : updatedCalendar);
				hs_dialog("close");
			},
			"All Sessions": {
				title: 'All Appointments',
				button_class: 'float_left',
				click: function () {
					data['all_slots'] = true;
					startCalendarRequest(calEvent, Dajaxice.healers.appointment_delete, data, callback ? callback : updatedCalendar);
					hs_dialog("close");
				}
			},
			"This and All Future": {
				title: 'This and All Future',
				button_class: 'float_left',
				click: function () {
					delete(data['all_slots']);
					startCalendarRequest(calEvent, Dajaxice.healers.appointment_delete_future, data, callback ? callback : updatedCalendar);
					hs_dialog("close");
				}
			}

		}
	});
}

function disableMouseOverZIndexEvent() {
	var $events = $('#calendar').find(".wc-cal-event");
	$.each($events, function () {
		$(this).unbind('mouseover.z-index');
	});
}

function send_intake_form(client_id){
	rest_ajax_post_request_long_timeout(url_send_intake_form, function(){
		showSuccess('Intake Form Successfully Sent.');
	}, {client_id: client_id})
}

function activate_intake_button(calEvent, $link){
	var label;
	$link.unbind('click');
	if (calEvent.intake) {
		label = 'View Intake »';
		$link.click(function(){
			fb.start(url_intake_form_answer + calEvent.healer_username + '/clients/' + calEvent.client + '/',
				{'measureHTML': 'true', 'width': '300', 'height': '150'});
			return false;
		});
	} else {
		label = 'Send Intake Form »';
		var action = function(){
			send_intake_form(calEvent.client_id);
		};
		$link.click(action);
	}
	$link.html(label);
}

function activate_notes_button(calEvent, $link){
	var label;
	var url_action;
	if (
		(is_wellness_center && calEvent.owner_healer_has_notes_for_client) ||
		(!is_wellness_center && calEvent.healer_has_notes_for_client)) {
		label = 'View Notes »';
		url_action = url_view_notes;
	} else {
		label = 'Create Note »';
		url_action = url_create_note;
	}
	$link.attr('href', url_action + calEvent.client + '/');
	$link.html(label);
}

function updateEventDetails($calendar, calEvent) {
	function activate_action_buttons(){
		if(calEvent.has_intake && calEvent.unavailable) {
			activate_intake_button(calEvent, $('#tooltip_intake_btn a'));
			$('#tooltip_intake_btn, #tooltip_separator').show();
		}

		if(calEvent.unavailable && !calEvent.timeoff) {
			activate_notes_button(calEvent, $('#tooltip_notes_btn a'));
			$('#tooltip_notes_btn').show();
		}
	}

	var date = '';
	var day_name = $calendar.weekCalendar("formatDate", calEvent.start, "l");
	if(calEvent.repeat_period) {
		date += '<span class="ui-icon ui-icon-refresh timeslot_repeat_icon"></span>';
		day_name += 's';
	} else {
		if(calEvent.timeoff != 1)
			day_name += ', ' + $calendar.weekCalendar("formatDate", calEvent.start_date, "n/j");
	}
	if(typeof calEvent.end_date == 'object' && calEvent.end_date.clearTime() > calEvent.start_date.clearTime()) {
		day_name += ', ' + $calendar.weekCalendar("formatDate", calEvent.start_date, "n/j") + " - " + $calendar.weekCalendar("formatDate", calEvent.end_date, "n/j");
	}
	$('#tooltip_date').html(date + day_name);
	$('#tooltip_time').text($calendar.weekCalendar("formatTime", calEvent.start, "g:i") + " - " + $calendar.weekCalendar("formatTime", calEvent.end, 'g:i a'));
	$('#tooltip_appointment, #tooltip_exceptions_block, #tooltip_note').hide();
	$('#tooltip_location, #tooltip_room, #tooltip_edit_btn').hide();
	$('#tooltip_confirm_btn, #tooltip_decline_btn, #tooltip_intake_btn, #tooltip_notes_btn, #tooltip_separator').hide();
	$('#tooltip_healer').hide();

	activate_action_buttons();

	if (center_main_mode) {
		$('#tooltip_healer').html(calEvent.healer_name);
		$('#tooltip_healer').show();
	}
	if(calEvent.timeoff == 1) {
		$('#tooltip_edit_btn').show();
		$('#tooltip_edit_btn').unbind('click').click(function() {dlg_timeoff_edit(calEvent);});
	} else {
		if(calEvent.unavailable) {
			$('#tooltip_client').html(create_client_link(calEvent));
			if(calEvent.treatment_length && typeof Treatments[calEvent.treatment_length] != 'undefined') {
				$('#tooltip_treatment_name').text(get_treatment_name_and_cost(calEvent));
			} else {
				$('#tooltip_treatment_name').text('Custom Treatment');
			}
			if(calEvent.location_title) {
				$('#tooltip_location').text(calEvent.location_title);
				$('#tooltip_location').show();
			}
			if(calEvent.room_name) {
				$('#tooltip_room').text(calEvent.room_name);
				$('#tooltip_room').show();
			}
			$('#tooltip_appointment').show();
			if(calEvent.confirmed) {
				$('#tooltip_edit_btn').show();
				$('#tooltip_edit_btn').unbind('click').click(function() {dlg_appt_edit(calEvent);});
			} else {
				$('#tooltip_confirm_btn').show();
				$('#tooltip_confirm_btn').unbind('click').click(function() {
					document.location.href='/schedule/appointments/confirm/'+calEvent.slot_id;
				});
				$('#tooltip_decline_btn').show();
				$('#tooltip_decline_btn').unbind('click').click(function() {
					document.location.href='/schedule/appointments/decline/'+calEvent.slot_id;
				});
			}
		} else {
			$('#tooltip_edit_btn').show();
			$('#tooltip_edit_btn').unbind('click').click(function() {dlg_timeslot_edit(calEvent);});
		}

		if(calEvent.exceptions.length) {
			var exceptions = [];
			for(var key in calEvent.exceptions) {
				if(key != 'length') {
					exceptions.push($calendar.weekCalendar("formatDate", new Date(key*1000) , "n/j"));
				}
			}
			var exceptions_html = "<span>Exceptions:</span> " + exceptions.join(', ');
			$('#tooltip_exceptions').html(exceptions_html);
			$('#tooltip_exceptions_block').show();
		}

		if(calEvent.note) {
			$('#tooltip_note').text(calEvent.note);
			$('#tooltip_note').show();
		}
	}
}

function createCalendar(start, end) {
	initNewClientDialog();

	$calendar = $('#calendar');

	$calendar.weekCalendar({
		timeslotHeight:getCalendarTimeslotHeight(),
		textSize:10,
		readonly:false,
		dateFormat:"n/j",
		useShortDayNames:true,
		timeSeparator:" - ",
		timeFormat:"g:i a",
		headerSeparator:' ',
		timeslotsPerHour:2,
		allowCalEventOverlap:true,
		overlapEventsSeparate: overlapEventsSeparate,
		firstDayOfWeek: get_first_day_of_week(),
		businessHours:{start:start, end:end, limitDisplay:true },
		daysToShow:7,
		defaultEventLength:defaultTimeslotLength,
		minDate:Date.today(),
		maxDate:Date.today().addDays(365),
		title: calendar_title,
		height:function ($calendar) {
			return $(".wc-toolbar").outerHeight() + $(".wc-header").outerHeight() + $(".wc-time-slots").outerHeight();
		},
		calendarAfterLoad:function ($calendar) {	
			disableMouseOverZIndexEvent();

			$("#not-available").hide();
			if (Edit_Availability && $('#calendar').is(":visible") && !populateCalendar.firsttime) {
				var tomorrowDate = Date.today().addDays(1);
				var availabilities = Timeslots.filter(function(e) {
					return e.unavailable == 0 && e.start >= tomorrowDate;
				});
				if(availabilities.length === 0) {
					$("#not-available").show();
				}
			}

			if (!Is_Mobile) {
				$('.wc-cal-event')
						  .attr('data-fb-tooltip', 'source:#appointment_schedule_details attachToHost:true fadeDuration:0 delay:10 placement:right width:300')
						  .mouseenter(function(obj) {
							  updateEventDetails($calendar, this.calEvent);
						  });

				if(typeof(Preview) == 'undefined')
					$('.wc-cal-event').each(function() {
						if(Edit_Availability && this.calEvent.unavailable === 0)
							$(this).addClass('fbTooltip');
						else if(!Edit_Availability && this.calEvent.unavailable==1)
							$(this).addClass('fbTooltip');
						else if(this.calEvent.timeoff==1)
							$(this).addClass('fbTooltip');
					});

				fb.activate();
			}
		},
		getHeaderDate:calendarHeaderDate,
		changedate:calendarWeekdaysStyle,
		draggable:function (calEvent, $event) {
			return !calEvent.readOnly && calEvent.timeoff != 1;
		},
		resizable:function (calEvent, $event) {
			return !calEvent.readOnly && calEvent.timeoff != 1;
		},

		eventDrop:function (calEvent, $event) {
			if (
					  calEvent.start.getDay() == calEvent.end.getDay() ||
								 (calEvent.end.getHours() === 0 && calEvent.end.getMinutes() === 0)
					  ) {
				this.updateEvent(calEvent, $event);
			} else {
				$calendar.weekCalendar("updateEvent", $event);
			}
		},
		eventDrag:function (calEvent, $event) {
			fb.end();
			$('.wc-cal-event').removeAttr('data-fb-tooltip');
			fb.activate();
		},
		eventResize:function (calEvent, $event) {
			calEvent.treatment_length = 0;
			this.updateEvent(calEvent, $event);
		},
		eventHeader:function (calEvent, calendar) {
			var options = calendar.weekCalendar('option');
			return calendar.weekCalendar('formatDate', calEvent.start, "g:i") +
					  options.timeSeparator +
					  calendar.weekCalendar('formatDate', calEvent.end, "g:i");
		},
		eventRender:function (calEvent, $event) {
			function hide_other_location_events(){
				if (is_wellness_center && calEvent.unavailable <= 1 &&
					calEvent.location != current_location_id && (center_main_mode || calEvent.timeoff !== 1)) {
					$event.addClass('hidden-override');
				}
			}
			var title = calEvent.client_name;
			if (typeof($event[0].calEvent) === 'undefined')
				$event[0].calEvent = calEvent;

			hide_other_location_events();
			var event_class = '';
			var backgroundColor;
			var timeBackgroundColor;
			if (Edit_Availability) {
				var zIndex = 1;
				var cursor = "pointer";
				var border = '';
				event_class = 'event_available event_shadow';

				if (calEvent.unavailable) {
					event_class = 'event_timeoff';
					calEvent.title = "Time Off";
					calEvent.readOnly = false;

					if (calEvent.timeoff != 1) {
						//private appointments
						event_class = 'event_unavailable_disable';
						if (calEvent.unavailable == 3) { //private availability
							event_class += ' availability';
						} else if (calEvent.unavailable == 4) {
							event_class = 'hidden-override'; // hidden appointments for room conflict checking.
						}
						if (calEvent.repeat_period){
							//calEvent.title = '<table><tr><td><span class="ui-icon ui-icon-refresh timeslot_repeat_icon" style="display: inline; " /></td><td>' + calEvent.client_name + '</td></tr></table>';
							calEvent.title = '<span class="ui-icon ui-icon-refresh timeslot_repeat_icon" style="display: inline; " />' + title;
						}
						else {
							calEvent.title = title;
						}


						calEvent.readOnly = true;
						cursor = "default";
						zIndex = 2;
					}

				} else if ((current_location_id == "all") || (calEvent.location == current_location_id) || !calEvent.location) {
					calEvent.readOnly = false;

					if (calEvent.repeat_period !== 0) {
						calEvent.title = '<span class="ui-icon ui-icon-refresh timeslot_repeat_icon" style="display: inline; " /><span style="color:white;">Weekly</span>';

						if (location_colors[calEvent.location]) {
							backgroundColor = location_colors[calEvent.location];
							timeBackgroundColor = location_colors[calEvent.location];
						} else {
							backgroundColor = $event.css('backgroundColor');
							if(backgroundColor === '')
								backgroundColor = '#68A1E5';
							timeBackgroundColor = backgroundColor;
						}
					} else {
						calEvent.title = 'One-Time';

						if (location_colors[calEvent.location]) {
							backgroundColor = make_dark_color(location_colors[calEvent.location], -0.15);
							timeBackgroundColor = make_dark_color(location_colors[calEvent.location], -0.15);
						} else {
							backgroundColor = $event.find(".wc-time").css('backgroundColor');
							timeBackgroundColor = backgroundColor;
						}
					}

					zIndex = 3;

				} else {
					calEvent.readOnly = true;
					calEvent.title = "";
					backgroundColor = "#aaa";
					timeBackgroundColor = "#aaa";
					cursor = "default";
				}

			} else {
				if (calEvent.unavailable == 1) {
					if (calEvent.timeoff == 1) {
						event_class = 'event_timeoff';
						calEvent.title = "Time Off";
						zIndex = 2;
					} else {
						event_class = 'event_unavailable event_shadow';
						if (calEvent.repeat_period)
							calEvent.title = '<table><tr><td><span class="ui-icon ui-icon-refresh timeslot_repeat_icon" style="display: inline;" /></td><td>' + title + '</td></tr></table>';
						else
							calEvent.title = title;

						if ((current_location_id == "all") || (calEvent.location == current_location_id)) {
							calEvent.readOnly = calEvent.confirmed!=1;
							cursor = calEvent.confirmed!=1 ? "default" : cursor;

							backgroundColor = location_colors[calEvent.location];
							timeBackgroundColor = location_colors_dark[calEvent.location];

						} else {
							calEvent.readOnly = true;
							backgroundColor = "#777";
							timeBackgroundColor = "#555";
							cursor = "default";
						}

						if (calEvent.confirmed === 0) {
							event_class = 'event_unconfirmed';
						}

						zIndex = 3;
					}
				} else if (calEvent.unavailable === 0) {
					event_class = 'event_available event_readonly event_timehide';
					calEvent.title = '';
					calEvent.readOnly = true;

					if (location_colors[calEvent.location]) {
						backgroundColor = make_dark_color(location_colors[calEvent.location], -0.15);
						timeBackgroundColor = make_dark_color(location_colors[calEvent.location], -0.15);
						border = "1px dotted " + make_dark_color(location_colors[calEvent.location], 0.15);
					}

					zIndex = 1;
				} else if (calEvent.unavailable == 4) {
					event_class = 'hidden-override'; // hidden appointments for room conflict checking.
				} else {
					//private appointments
					event_class = 'event_unavailable_disable event_readonly';
					calEvent.readOnly = true;
					if (calEvent.unavailable == 3) { //private availability
						event_class += ' event_timehide event_no_border_radius';
					}
				}
			}

			if(event_class) {
				$event.addClass(event_class);
			}

			if (is_wellness_center && backgroundColor && typeof(backgroundColor) != 'undefined' &&
					  backgroundColor !== '#777' && backgroundColor !== '#aaa') {

				backgroundColor = providers_colors[calEvent.healer_username];
				if (!Edit_Availability && calEvent.unavailable === 0 && typeof(backgroundColor) != 'undefined') {
					backgroundColor = make_dark_color(backgroundColor, -0.15);
				}
				if (calEvent.unavailable === 0) {
					// needed for correct colors for center availability
					if (typeof backgroundColor == 'undefined') {
						backgroundColor = '#68a1e5';
					}
					timeBackgroundColor = backgroundColor;
				} else {
					timeBackgroundColor = providers_colors_dark[calEvent.healer_username];
				}
			}

			$event.css({
				"backgroundColor":backgroundColor,
				"cursor":cursor,
				"border":border,
				'z-index':zIndex
			});

			$event.find(".wc-time").css({
				"backgroundColor":timeBackgroundColor
			});
		},
		eventAfterRender:function (calEvent, $event) {
			$event.css({
				"max-width":'98%'
			});
			$event.width('90%');
			removeDragHandle($event);
			hide_appts_or_slots();
		},

		updateEvent:function (calEvent, $event) {

			if (!checkSaving(calEvent, $event)) return;
			if (Edit_Availability) {
				if (calEvent.repeat_period) {
					dlg_timeslot_reschedule_choice(calEvent, $event);
				} else {
					var data = {
						'timeslot_id': calEvent.slot_id,
						'start_old': stripTimezone($event.start),
						'end_old': stripTimezone($event.end),
						'start_new': stripTimezone(calEvent.start),
						'end_new': stripTimezone(calEvent.end),
						'start_date': '',
						'end_date': '',
						'weekly_new': calEvent.repeat_period !== 0,
						'all_slots': calEvent.repeat_period !== 0,
						'username': calEvent.healer_username
					};
					startCalendarRequest(calEvent, Dajaxice.healers.timeslot_update, data, updatedCalendar);
				}
			} else {
				if (calEvent.repeat_period) {
					dlg_appt_reschedule_choice(calEvent, $event);
				} else {
					dlg_appt_reschedule_single(calEvent, $event);
				}
			}
		},
		eventNew:function (calEvent, $event) {

			if (Edit_Availability) {
				$("#not-available").hide();
				dlg_timeslot_new(calEvent);
			} else {
				dlg_appt_new(calEvent);
			}
		},
		eventClick:function (calEvent, $event) {
			if (!checkSaving(calEvent)) return;

			if (calEvent.readOnly)
				return;

			if (calEvent.timeoff == 1) {
				dlg_timeoff_edit(calEvent);
			} else {
				if (Edit_Availability) {
					dlg_timeslot_edit(calEvent);
				} else {
					dlg_appt_edit(calEvent);
				}
			}
		},
		data:function (start, end, callback) {
			callback(get_timeslots_for_week(start));
		}
	});

	initTimesOnChange($("#new_appointment_container"));
	initTimesOnChange($("#edit_appointment_container"));

	updateAppointmentsList();

	initDatePicker();

	$('.add_timeslot_buttons span').click(function (e) {
		if ($(this).attr("id") == "timeslot_regular_button")
			defaultTimeslotWeekly = false;
		else
			defaultTimeslotWeekly = true;

		var bg_color = $(this).find("img.color_box").css("background-color");

		$("#timeslot_regular_button").find("img.color_box").css("background-color", bg_color);
		$("#timeslot_weekly_button_box").css("background-color", bg_color);
	});
}

function after_populate_calendar_refresh() {
	if (!$("#schedule_mode_message").length)
		$(".ui-widget-header.wc-toolbar").prepend(
				  '<span class="wc-title-button grey_box" id="schedule_mode_message"></span>'
		);

	if (Edit_Availability) {
		$(".wc-toolbar").addClass('edit_availability_title');
		$('#schedule_mode_message').html('Click the Grid Below to Add Availability');
		$('#schedule_mode_message').addClass('single_button');
	} else {
		$(".wc-toolbar").removeClass('edit_availability_title');
		updateAppointmentsList();
		$('#schedule_mode_message').html('Click the Grid Below to Add an Appointment');
		$('#schedule_mode_message').removeClass('single_button');
	}
}

function get_send_notification(id) {
	var checkbox = $(id);
	return ((checkbox.length === 0) || checkbox.is(":checked"));
}

function update_timeoff_dlg_all_day() {
	var timeoff_dlg = $('#add_timeoff_dlg');
	var checked = timeoff_dlg.find('#all_day').attr("checked")=="checked";
	var date;
	if(checked) {
		disableInput('start_time');
		disableInput('end_time');
		$('.timeEntry_control').hide();
		date = new Date();
		date.setHours(0, 0);
		setTimeFieldVal(timeoff_dlg.find("input[name=start_time]"), date);
		date.setHours(23, 59);
		setTimeFieldVal(timeoff_dlg.find("input[name=end_time]"), date);
	} else {
		enableInput('start_time');
		enableInput('end_time');
		$('.timeEntry_control').show();
		date = new Date();
		date.setHours(10, 0);
		setTimeFieldVal(timeoff_dlg.find("input[name=start_time]"), date);
		date.setHours(18, 0);
		setTimeFieldVal(timeoff_dlg.find("input[name=end_time]"), date);
	}
}

function activate_client_edit(){
	var html_elements = '<input placeholder="Client Name or Last Name" id="search_client_edit" class="ui-autocomplete-input ui-autocomplete-loading" maxlength="75" type="text" style="width: 180px;" autocomplete="off" role="textbox" aria-autocomplete="list" aria-haspopup="true">';
	html_elements += '<input type="hidden" id="id_client_edit" name="client"/>';
	html_elements += '<input type="hidden" id="id_type_edit" name="client_type"/>';
	html_elements += '<a href="#" onclick="dlg_new_client();" style="display: block; color: #1770BF; font-style: italic;">New Client...</a>';
	$('.edit_client').click(function(){
		var element = $(this);
		var current_client = element.parent().children('#client_name').children('a').html();
		current_mode = 'edit';
		element.parent().html(html_elements);
		$('#search_client_edit').focus();
		fb.resize();
		initClientSearchAutocomplete();
	});
}

function location_has_rooms(location_id) {
	return All_Rooms.filter(function(room) { return room.location == location_id; }).length !== 0;
}

function is_valid_room(room_id, location_id) {
	if(!room_id) {
		if (location_has_rooms(location_id)) {
			showError('Please select a room.');
			return false;
		}
	}
	return true;
}

function show_or_hide_room_row(dialog, location_id) {
	if (location_has_rooms(location_id)) {
		dialog.find('.room_row').show();
	} else {
		dialog.find('.room_row').hide();
	}
}

function hide_appts_or_slots(){
	if (center_main_mode){
		if (Edit_Availability) {
			$('.event_unavailable_disable').hide();
		} else {
			$('.event_timehide').hide();
		}
	}
}

/*** Settings ***/

function recreate_calendar(update){
	update = typeof update !== 'undefined' ? update : false;
	populateCalendar.firsttime = true;
	if (update) {
		fetchCalendar();
	} else {
		populateCalendar(initSlots);
		populateCalendar(initSlots);
	}
}

function set_schedule_full_width(status){
	if (status) {
		$('.content_frame').css('width', 'auto').css('max-width', 'none').css('margin', '8px 0 16px 10px');
		if (!is_mobile()) {
			$('#left_column').hide();
		}
	} else {
		$('.content_frame').css('width', '').css('max-width', '').css('margin', '');
		$('#left_column').show();
	}
	create_width_setting_links(status);
}

function set_side_by_side_setting(status, update){
	update = typeof update !== 'undefined' ? update : false;
	create_side_by_side_setting_links(status);
	if (status) {
		overlapEventsSeparate = true;
		wcenter_overlapEventsSeparate = true;
	} else {
		overlapEventsSeparate = false;
		wcenter_overlapEventsSeparate = false;
	}
	recreate_calendar(update);
}

function set_first_week_day_setting(status){
	create_first_week_day_setting_links(status);
	if (status) {
		start_from_sunday = true;
	} else {
		start_from_sunday = false;
	}
	recreate_calendar();
}

function set_schedule_provider_dropdown(status) {
	function activate_provider_dropdown(){
		$('.schedule-provider-select').addClass('provider_dropdown').hide().click(function(){
			$('.schedule-provider-select').hide();
		});
		$('#selected_provider').show().mouseenter(function(){
			$('.schedule-provider-select').show();
		});
		$('#provider_menu').mouseleave(function(){
			$('.schedule-provider-select').hide();
		});
		update_menu_name();
	}

	function deactivate_provider_dropdown(){
		$('#selected_provider').hide().unbind('mouseenter');
		$('.schedule-provider-select').removeClass('provider_dropdown').show().unbind('click');
		$('#provider_menu').unbind('mouseleave');
	}

	if (status) {
		activate_provider_dropdown();
	} else {
		deactivate_provider_dropdown();
	}

	create_provider_dropdown_setting_links(status);
}

function save_settings(status, set_function, save_function){
	return function(status){
		set_function(status);
		save_function(function(){}, {status: status},
				  {'error_callback': function(){
					  showError('Error saving settings. Please try again.');
				  }}
		);
	};
}

var save_first_week_day_setting = save_settings(status,
		  set_first_week_day_setting, Dajaxice.healers.save_first_week_day_setting);

var save_side_by_side_setting = save_settings(status,
		  set_side_by_side_setting, Dajaxice.healers.save_side_by_side_setting);

var save_schedule_full_width = save_settings(status,
		  set_schedule_full_width, Dajaxice.healers.save_schedule_full_width);

var save_provider_dropdown_setting = save_settings(status,
		  set_schedule_provider_dropdown, Dajaxice.healers.save_schedule_dropdown_provider_list);


function create_settings_links(status, save_function, names, element_id){
	return function(status){
		function activate_links() {
			$('.' + on).click(function(){
				save_function(true);
			});
			$('.' + off).click(function(){
				save_function(false);
			});
		}

		var html;
		var on = element_id + '_on';
		var off = element_id + '_off';
		if (status) {
			html = '<a class="' + off + '">' + names[0] + '</a>';
		} else {
			html = '<a class="' + on + '">' + names[1] + '</a>';
		}
		$('#' + element_id).html(html);
		activate_links();
	};
}

var create_width_setting_links = create_settings_links(status,
		  save_schedule_full_width, ['Normal Width', 'Full Width'], 'switch_schedule_width');

var create_side_by_side_setting_links = create_settings_links(status,
		  save_side_by_side_setting, ['Overlap', 'Side by Side'], 'switch_side_by_side');

var create_first_week_day_setting_links = create_settings_links(status,
		  save_first_week_day_setting, ['Next 7 days', 'Sunday - Saturday'], 'switch_first_week_day');

var create_provider_dropdown_setting_links = create_settings_links(status,
		  save_provider_dropdown_setting, ['∨', '∧'], 'switch_provider_dropdown');


/*** End Settings ***/

function switch_provider_visibility() {
	$('.provider_visibility').hide();
	$('#provider_visibility_' + schedule_username).show();
}

function show_calendar_with_location(id){
	current_location_id = id;
	$('#calendar').weekCalendar('refresh');
}

function show_schedule_error(element, username) {
	element = $(element);
	var name = element.data('name');
	var first_name = element.data('first-name');
	var url = element.data('url');

	schedule_username = username;
	switch_provider_selected();

	$('#schedule_content').hide();
	$('#schedule_error').find('.name').html(name);

	var link = '<a href="' + url + '">Go to ' + first_name + "'s Profile »</a>";
	$('#schedule_error').find('.link').html(link);
	$('#schedule_error').show();
}


$(function(){
	set_schedule_full_width(schedule_full_width);
	if (is_wellness_center) {
		create_side_by_side_setting_links(wcenter_overlapEventsSeparate);
	}
	create_first_week_day_setting_links(start_from_sunday);

	if(typeof(list_intake_forms_page) != 'undefined'){
		if(list_intake_forms_page){
			return;
		}
	}

	$('#location_bar_edit a').click(function (e) {
		var id = $(this).attr("id");
		if (!id)
			return;
		$('#location_menu > li > a').html($(this).html());
		location_menu.show(0,0);
		show_calendar_with_location(id);
	});

	var timeoff_dlg = $('#add_timeoff_dlg');
	timeoff_dlg.find('#all_day').click(update_timeoff_dlg_all_day);

	timeoff_dlg.find('input[name=start_date]').change(function (e) {
		var start_field = timeoff_dlg.find('input[name=start_date]');
		var end_field = timeoff_dlg.find('input[name=end_date]');
		var start_date = new Date(start_field.val());
		var end_date = new Date(end_field.val());
		if (end_date < start_date) {
			end_field.val(start_date.toString('MM/dd/yyyy'));
		}
	});

	$(window).resize(calendarTimeslotHeight);
	activate_client_edit();

	var main = $('.appointment_container,#new_appointment_container');
	main.find('select[name="location"]').change(function() {
		var element = $(this);
		var dialog = element.parents('form');
		var location_id = element.val();
		show_or_hide_room_row(dialog, location_id);
		var treatment_field = dialog.find('select[name="treatment_length"]');
		var treatment = parseInt(treatment_field.val());
		treatment_field = updateTreatmentField(treatment_field, treatment, location_id);
		// trigger change to update location if location is unavailable for selected treatment
		//treatment_field.trigger('change');
		updateRoomField(dialog);
		updateDiscountField(dialog);
	});

	main.find('input[name="start"],input[name="end"]').change(function() {
		if (dialog_is_active) {
			updateRoomField($(this).parents('form'));
		}
	});

	main.find('select[name="treatment_length"]').change(function() {
		// function filter_locations() {
		// 	// Keep private locations, other center's locations and treatment locations. Remove all other center Locations.
		// 	return Locations.filter(function(location){
		// 		if (location.wcenter_id === 0 ||
		// 				  location.wcenter_id != treatment_wcenter_id ||
		// 				  treatment_locations.indexOf(location.id) !== -1) {
		// 			return location;
		// 		}
		// 	});
		// }

		// function get_location_wcenter_id(location_id) {
		// 	for(var key in Locations) {
		// 		var location = Locations[key];
		// 		if (location.id == location_id) {
		// 			return location.wcenter_id;
		// 		}
		// 	}
		// }

		// function change_selected_location_if_location_is_not_available_anymore() {
		// 	function old_location_is_available_to_select() {
		// 		for (var key in Locations_available) {
		// 			var location = Locations_available[key];
		// 			if (location.id == location_id) {
		// 				return true;
		// 			}
		// 		}
		// 		return false;
		// 	}

		// 	function get_another_available_wcenter_location() {
		// 		for (var key in Locations_available) {
		// 			var location = Locations_available[key];
		// 			if (location.wcenter_id == treatment_wcenter_id) {
		// 				return location.id;
		// 			}
		// 		}
		// 	}

		// 	if (old_location_is_available_to_select()) {
		// 		return location_id;
		// 	} else {
		// 		return get_another_available_wcenter_location();
		// 	}

		// }
		var dialog_form = $(this).parents('form');
		// var treatment_length_id = parseInt($(this).val());
		// var location_field = dialog_form.find('select[name="location"]');
		// var location_id = location_field.val();

		// if (treatment_length_id === 0) {
		// 	updateLocationField(location_field, location_id);
		// } else {
		// 	var treatment = Treatment_Types[treatment_length_id];
		// 	var treatment_locations = Treatments_Locations[selected_username][treatment];
		// 	if (treatment_locations.length === 0) {
		// 		updateLocationField(location_field, location_id);
		// 	} else {
		// 		var treatment_wcenter_id = get_location_wcenter_id(treatment_locations[0]);
		// 		var Locations_available = filter_locations();
		// 		location_id = change_selected_location_if_location_is_not_available_anymore();
		// 		updateLocationField(location_field, location_id, Locations_available);
		// 	}
		// }
		updateRoomField(dialog_form);
	});

	switch_provider_visibility();

	if (is_wellness_center) {
		set_schedule_provider_dropdown(provider_dropdown);
		$('.schedule_provider_item').each(function(){
			var color = $(this).attr('data-color-selected');
			if (color !== '#FFFFCC') {
				color = make_dark_color(color, -0.2);
			} else {
				color = '#FFFFFF';
			}
			$(this).css('background-color', color);
			$(this).attr('data-color-not-selected', color);
			$(this).attr('data-color', color);
		});
		$('.schedule_provider_item').hover(function(){
					  $(this).css('background-color', $(this).attr('data-color-selected'));
				  }, function(){
					  $(this).css('background-color', $(this).attr('data-color'));
				  }
		);
	}
});