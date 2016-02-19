var Timeslots = [];
var initSlots = [];
var GeneratedSlots = [];
var Treatment = null;
var setupTime = 0;
var Timeslots_Byweek = [];
var UnconfirmedSlots = [];
var GroupedSingleSlots = [];
var StartSlotsDate = null;
var WeeksToGenerate = 4;
var Booking = false;
var Edit_Availability;
var Cancellation_Policy = false;
var First_Bookable_Time = null;
var JS_Error = '';
var current_username = false;
var OtherHealersAppointmentsSlots = false;
var AvailableRooms = false;
var is_wcenter_schedule = false;
var start_from_sunday;
var embed = false;
var location_filter_id = false;

function get_first_day_of_week(){
	if (start_from_sunday) {
		return 0;
	} else {
		return Date.today().getDay();
	}
}

function getCalendar(slots) {
	if(slots)
		populateCalendar(slots);
	else
		fetchCalendar();
}

function expandData(data, keys) {
	var arr = [];
	var len = data.length;
	var klen = keys.length;
	var start = 0;
	var stop = klen;
	while (stop <= len) {
		var data_portion = data.slice(start, stop);
		var data_portion_with_keys = [];
		for(var ind in data_portion) {
			data_portion_with_keys[keys[ind]] = data_portion[ind];
		}
		arr.push(data_portion_with_keys);
		start = stop;
		stop += klen;
	}
	return arr;
}

function getDateKey(date) {
	return date.getYear() + date.getMonth() + date.getDate();
}

function checkConflict(start, end, slots, slot) {
	slot = typeof slot !== 'undefined' ? slot : false;
	if (slot) {
		if (slot.unavailable > 1) {
			return false;
		}
	}
	var slots_for_date = slots[getDateKey(start)];
	if(typeof slots_for_date == 'undefined') return false;
	for(var key in slots_for_date) {
		if(!Booking && slots_for_date[key].unavailable == 1) return false;
		if(!(slots_for_date[key].end <= start || slots_for_date[key].start >= end)) {
			return slots_for_date[key];
		}
	}
	return false;
}

function groupSlotsByDate(slots) {
	function addSlot() {
		if(typeof grouped_slots[date_key] == 'undefined') {
			grouped_slots[date_key] = [];
		}
		grouped_slots[date_key].push(slot);
	}

	var grouped_slots = {};
	for(var key in slots) {
		var slot = slots[key];
		if(typeof(slot) !== 'undefined') {
			var date_key = getDateKey(slot.start);
			addSlot();
		}
	}
	return grouped_slots;
}

function findRuleFirstStep(from_date, start, step) {
	var steps = 1;
	if(from_date > start) {
		var daysDiff = Math.floor((from_date - start) / 86400000); //60*60*24*1000
		steps += Math.floor(daysDiff / step) - 1;
	}
	return steps * step;
}

function processSlotsRules(slots, from_date, weeks, generate_next) {
	generate_next = typeof generate_next !== 'undefined' ? generate_next : false;
	var new_available_slots = [];
	var new_unavailable_slots = [];
	if(typeof weeks == 'undefined') weeks = WeeksToGenerate;
	var endDate = from_date.clone().addWeeks(weeks);
	for(var i in slots) {
		var slot = slots[i];
		if(slot.repeat_period && ((typeof slot.generate_next == 'undefined') || slot.generate_next) &&
				  slot.start <= endDate
				  ) {
			var step = slot.repeat_every;
			var end_date = slot.end_date && (slot.end_date < endDate) ? slot.end_date : endDate;
			switch(slot.repeat_period) {
				case 2:
					step = step*7;
					break;
			}
			var first_step = slot.generate_next ? step : findRuleFirstStep(from_date, slot.start, step);
			var start =	slot.start.clone().addDays(first_step);
			var end = slot.end.clone().addDays(first_step);
			var groupedSlots = GroupedSingleSlots[slot.unavailable == 1];

			var generated_slots = false;
			var j = 1;
			while(start<end_date) {
				var repeat_pos = slot.repeat_pos ? slot.repeat_pos + j : j;
				if(slot.repeat_count && repeat_pos == slot.repeat_count) break;

				var is_not_exception = slot.exceptions[stripTimezone(start.clone().clearTime()) / 1000] != 1;
				if(is_not_exception && !checkConflict(start, end, groupedSlots, slot)) {
					var new_slot = {'slot_id': slot.slot_id,
						'unavailable': slot.unavailable,
						'repeat_period': slot.repeat_period,
						'repeat_every': slot.repeat_every,
						'start': start.clone(),
						'end': end.clone(),
						'start_date': slot.start_date,
						'end_date': slot.end_date,
						'treatment_length': slot.treatment_length,
						'location': slot.location,
						'location_title': slot.location_title,
						'client_id': slot.client_id,
						'client': slot.client,
						'client_name': slot.client_name,
						'note': slot.note,
						'repeat_count': slot.repeat_count,
						'repeat_pos': repeat_pos,
						'exceptions': slot.exceptions,
						'confirmed': slot.confirmed,
						'room': slot.room,
						'generate_next': false,
						'healer_name': slot.healer_name,
						'healer_username': slot.healer_username,
						'cost': slot.cost,
						'discount_code': slot.discount_code,
						'intake': slot.intake,
						'has_intake': slot.has_intake,
						'healer_has_notes_for_client': slot.healer_has_notes_for_client,
					};
					if(slot.unavailable == 1) {
						new_unavailable_slots.push(new_slot);
					} else {
						new_available_slots.push(new_slot);
					}
					generated_slots = true;
				}

				j++;
				start.addDays(step);
				end.addDays(step);
			}

			// mark last slot
			var new_slots = slot.unavailable == 1 ? new_unavailable_slots : new_available_slots;
			if(new_slots.length) {
				var last_slot = new_slots[new_slots.length - 1];
				if(!slot.repeat_count || (slot.repeat_count && last_slot.repeat_pos < slot.repeat_count - 1)) {
					last_slot.generate_next = true;
				}
			}

			// check original slot for conflict and start date
			var is_exception = slot.exceptions[stripTimezone(slot.start.clone().clearTime()) / 1000] == 1;
			if(is_exception || checkConflict(slot.start, slot.end, groupedSlots) ||
					  (!slot.generate_next && slot.start < from_date)
					  ) {
				slot.hide = true;
			}

			if (!generate_next && (generated_slots || slot.end_date < endDate)) {
				slot.generate_next = false;
			}
		}
	}
	return {'available': new_available_slots, 'unavailable': new_unavailable_slots};
}

function prepareDates(slot) {
	var date = Date.parseExact(slot.start_date, 'yyyy-MM-dd');
	slot.start = date.clone().addMinutes(slot.start_time);
	slot.end = date.clone().addMinutes(slot.end_time);
	slot.start_date = Date.parseExact(slot.start_date, 'yyyy-MM-dd');
	if(slot.end_date) {
		slot.end_date = Date.parseExact(slot.end_date, 'yyyy-MM-dd');
		if (slot.timeoff == 1) {
			slot.end = slot.end_date.clone().addMinutes(slot.end_time);
		}
		slot.end_date.setHours(23,59);
	}

	return slot;
}

function prepareSlotsDates(slots) {
	for(var key in slots) {
		var slot = slots[key];
		prepareDates(slot);
	}
}

function updateTimeslotsByWeek(slot) {
	var days_diff = Math.floor((slot.end - slot.start) / 86400000);
	var weeks = {};
	for(var d=0; d <= days_diff; d++) {
		var start = slot.start.clone().addDays(d);
		var midnightCurrentDate = new Date(start.getFullYear(), start.getMonth(), start.getDate());
		var fix = (midnightCurrentDate.getDay() >= new Date().getDay()) ? 0 : 7;
		midnightCurrentDate.setDate(midnightCurrentDate.getDate() - midnightCurrentDate.getDay() + new Date().getDay() - fix);
		if(weeks[midnightCurrentDate]) continue;
		weeks[midnightCurrentDate] = true;

		if (!Timeslots_Byweek[midnightCurrentDate]) { Timeslots_Byweek[midnightCurrentDate] = []; }
		Timeslots_Byweek[midnightCurrentDate].push(slot);
	}
}

function solveUnavailableConflicts(available_slots, unavailable_slots) {
	if(!Booking) return;

	if(unavailable_slots.length>0) {
		var grouped_unavailable_slots = groupSlotsByDate(unavailable_slots);
		for(var key in available_slots) {
			var slot = available_slots[key];
			if(checkConflict(slot.start, slot.end, grouped_unavailable_slots)) {
				available_slots[key].hide = true;
			}
		}
	}
}

function setReadOnly(slots, readonly) {
	for(var key in slots) {
		slots[key].readOnly = readonly;
	}
}

function hideSlots(slots, hide) {
	for(var key in slots) {
		slots[key].hide_tmp = hide;
	}
}

function addSetupTimeToSlots(slots) {
	function addSetupTimeToSlot(slot) {
		slot_new = $.extend(true, {}, slot);
		slot_new.start = slot_new.start.clone();
		slot_new.end = slot_new.end.clone();
		//Setup time needed for other provider
		var setupTimeOther = slot_new.setup_time;
		if(slot_new.timeoff == '1') return slot;
		if(slot_new.start_time - setupTimeOther > 0) {
			slot_new.start.addMinutes(-setupTimeOther);
		}
		if(slot_new.end_time + setupTime < 1440) {
			slot_new.end.addMinutes(setupTime);
		}
		return slot_new;
	}
	var slots_output = {};
	for(var key in slots) {
		slots_output[key] = addSetupTimeToSlot(slots[key]);
	}
	return slots_output;
}

function calcSlotLength(slot) {
	return (slot.end - slot.start)/(1000*60);
}

function splitAvailabilityByTimeoff(slots, available, unavailable) {
	var grouped_available = groupSlotsByDate(available);
	var offtime = _.filter(unavailable, function(slot) {return slot.timeoff;});
	for(var key in offtime) {
		var slot = offtime[key];
		var date = slot.start.clone();
		date.setHours(0, 0);
		while(date <= slot.end) {
			var start = getDateKey(date) == getDateKey(slot.start) ? slot.start : date;
			var end = slot.end;
			if(getDateKey(date)!=getDateKey(slot.end)) {
				end = date.clone();
				end.setHours(23, 59);
			}
			var available_slots = grouped_available[getDateKey(date)];
			for(var akey in available_slots) {
				var aslot = available_slots[akey];
				if(aslot.start > end || aslot.end < start) {
					continue;
				} else if(aslot.start >= start && aslot.end <= end) {
					aslot.hide=true;
				} else if(aslot.start < start && aslot.end <= end) {
					aslot.oend = aslot.end.clone();
					aslot.end = start.clone();
				} else if(aslot.start >= start && aslot.end > end) {
					aslot.ostart = aslot.start.clone();
					aslot.start = end.clone();
				} else if(aslot.start < start && aslot.end > end) {
					aslot.oend = aslot.end.clone();
					aslot.end = start.clone();
					var new_slot = {
						'slot_id': aslot.slot_id,
						'unavailable': aslot.unavailable,
						'repeat_period': aslot.repeat_period,
						'repeat_every': aslot.repeat_every,
						'repeat_count': aslot.repeat_count,
						'generate_next': false,
						'start_date': aslot.start_date,
						'end_date': aslot.end_date,
						'start': end.clone(),
						'end': aslot.oend,
						'ostart': aslot.start,
						'location': aslot.location,
						'location_title': aslot.location_title,
						'exceptions': aslot.exceptions,
					};
					slots.push(new_slot);
					available_slots.push(new_slot);
				}
			}
			date.addDays(1);
		}

	}
}

// fixes 1052
// function add_setup_time_to_start(slots){
	// add_setup_time_to_start adds time to both start and end of the slot regardless of the actual availability.
	// this function helps remove slots which should be available.
// 	for(var key in slots) {
// 		var slot = slots[key];
// 		slot.start.addMinutes(setupTime);
// 		slot.end.addMinutes(setupTime);
// 	}
// }

function hide_slots_which_exceed_availability_interval(slots) {
	function get_slot_endtimes(){
		var endtimes = {};
		GeneratedSlots.forEach(function(slot){
			if (typeof slot.end_time !== 'undefined') {
				endtimes[slot.slot_id] = slot.end_time;
			}
		});
		return endtimes;
	}

	var slot_endtimes = get_slot_endtimes();

	for(var key in slots) {
		var slot = slots[key];
		if (slot.end.getHours()*60 + slot.end.getMinutes() > slot_endtimes[slot.slot_id]) {
			slot.hide = true;
		}
	}

}

function splitSlotsByTreatment(slots, available, unavailable) {
	var available_slots = _.filter(available, function(slot) {return !slot.hide;});
	var unavailable_slots = groupSlotsByDate(unavailable);
	available_slots.sort(function (a, b) {return a.start.compareTo(b.start);});
	for(var key in available_slots) {
		var slot = available_slots[key];
		if(location_online[slot.location] === 0) continue;

		// find next slot conflict
		var next_slot = available_slots[parseInt(key) + 1];
		if((typeof next_slot != 'undefined') && next_slot.start.getDay() == slot.start.getDay()) {
			var diff = (next_slot.start - slot.end)/(1000*60);
			if(diff < setupTime) {
				// decrease slot length to enable setupTime between slots
				slot.end.addMinutes(diff-setupTime);
			}
		}

		var slot_length = calcSlotLength(slot);
		if(slot_length < Treatment.length) {
			slot.hide = true;
		} else {
			var slotEnd = slot.end.clone();
			slot.end = slot.start.clone().addMinutes(Treatment.length);

			var start = slot.end.clone();
			var conflictSlot = checkConflict(slot.start, slot.end, unavailable_slots);
			if(conflictSlot) {
				slot.hide = true;
				start = conflictSlot.end.clone();
			} else {
				start.addMinutes(setupTime);
			}
			var end = start.clone().addMinutes(Treatment.length);

			if (slot.start < First_Bookable_Time) {
				slot.hide = true;
				var minutes = First_Bookable_Time.getMinutes();
				var hours = First_Bookable_Time.getHours();
				start = First_Bookable_Time.clone();
				start.setHours( (minutes > 30) ? ++hours : hours );
				start.setMinutes( (Math.ceil(minutes / 30) * 30) % 60 );
				end = start.clone().addMinutes(Treatment.length);
			}

			while(end <= slotEnd) {
				var new_slot = {
					'slot_id': slot.slot_id,
					'unavailable': slot.unavailable,
					'repeat_period': slot.repeat_period,
					'repeat_every': slot.repeat_every,
					'repeat_count': slot.repeat_count,
					'start_date': slot.start_date,
					'end_date': slot.end_date,
					'start': start,
					'end': end,
					'location': slot.location,
					'location_title': slot.location_title,
					'exceptions': slot.exceptions,
					'cost': slot.cost,
					'discount_code': slot.discount_code,
					'intake': slot.intake,
					'has_intake': slot.has_intake,
					'healer_has_notes_for_client': slot.healer_has_notes_for_client,
					'client_id': slot.client_id,
				};
				start = new_slot.end.clone();
				conflictSlot = checkConflict(new_slot.start, new_slot.end, unavailable_slots);
				if(conflictSlot) {
					start = conflictSlot.end.clone();
				} else {
					slots.push(new_slot);
					start.addMinutes(setupTime);
				}
				end = start.clone().addMinutes(Treatment.length);
			}
		}
	}
}

function applyEditAvailability(available, unavailable) {
	if((typeof Edit_Availability != 'undefined') && Edit_Availability) {
		setReadOnly(unavailable, true);
	} else if(typeof Edit_Availability != 'undefined') {
		setReadOnly(unavailable, false);
	}
}

function expand_data(slots){
	if(slots.keys && typeof(slots.keys) == 'object')
		slots = expandData(slots.data, slots.keys);
	return slots;
}

function remove_busy_room_slots(slots){
	// if any of the rooms are available then don't remove that slot
	var select_only_available_rooms = function(slot){
		var result = false;
		for (var i = 0; i < AvailableRooms.length; i++) {
			room_id = AvailableRooms[i];
			result |= is_no_room_conflict(slot, all_other_healers_slots, room_id);
		}
		return result;
	};

	if (AvailableRooms) {
		var processed_slots = processSlotsRules(OtherHealersAppointmentsSlots, StartSlotsDate, undefined, true);
		var all_other_healers_slots = $.extend(true, [], OtherHealersAppointmentsSlots);
		all_other_healers_slots = all_other_healers_slots.concat(processed_slots['available']).concat(processed_slots['unavailable']);
		slots = slots.filter(select_only_available_rooms);
	}

	return slots;
}

function populateCalendar(slots) {
	function error_occured() {
		if (slots == Dajaxice.EXCEPTION || (typeof(slots) != 'object')) {
			var error;
			if (typeof(slots) == 'string') {
				error = slots;
			} else {
				error = 'Error Getting Calendar Data. Please Try Again.';
			}
			showError(error);
			return true;
		}
		return false;
	}

	if (error_occured())
		return;

	if (dajaxProcess(slots))
		return;

	if (typeof populateCalendar.firsttime == 'undefined')
		populateCalendar.firsttime = true;

	if (typeof populateCalendar.hide == 'undefined')
		populateCalendar.hide = false;

	// if object instead of list - convert to list using keys
	slots = expand_data(slots);

	initSlots = $.extend(true, [], slots);
	prepareSlotsDates(slots);

	// filter_location and ignore unavailable slots
	if (location_filter_id) {
		slots = _.filter(slots, function(slot) {return slot.unavailable == 1 || slot.location == location_filter_id;});
	}

	StartSlotsDate = Booking ? First_Bookable_Time.clone() : Date.today().moveToDayOfWeek(0, -1);
	var weeks;
	// if(!populateCalendar.firsttime && !is_wcenter_schedule) {
		// var current_date = $('#calendar').weekCalendar('getCurrentFirstDay');
	if(!is_wcenter_schedule) {
		var current_date;
		if(!populateCalendar.firsttime) {
			current_date = $('#calendar').weekCalendar('getCurrentFirstDay');
		} else {
			current_date = new Date();
		}
		weeks = getWeeksDiff(StartSlotsDate, current_date);
		weeks = weeks + (WeeksToGenerate - weeks % WeeksToGenerate) + WeeksToGenerate;
	}

	var unavailable = _.filter(slots, function(slot) {return slot.unavailable == 1;});
	var available = _.filter(slots, function(slot) {return slot.unavailable === 0;});

	GroupedSingleSlots[false] = groupSlotsByDate(_.filter(available, function(slot) {return slot.repeat_period === 0;}));
	GroupedSingleSlots[true] = groupSlotsByDate(_.filter(unavailable, function(slot) {return slot.repeat_period === 0;}));

	var new_slots = processSlotsRules(slots, StartSlotsDate, weeks);
	if(weeks)
		StartSlotsDate.addWeeks(weeks - WeeksToGenerate);

	slots = slots.concat(new_slots['available']).concat(new_slots['unavailable']);
	unavailable = unavailable.concat(new_slots['unavailable']);
	available = available.concat(new_slots['available']);

	if(Treatment) {
		GeneratedSlots = $.extend(true, [], slots); //copy slots
		unavailable = addSetupTimeToSlots(unavailable);
		// fixes 1052
		// add_setup_time_to_start(slots);
		splitSlotsByTreatment(slots, available, unavailable);
	}

	solveUnavailableConflicts(available, unavailable);
	hide_slots_which_exceed_availability_interval(slots);
	if(typeof Edit_Availability != 'undefined') {
		splitAvailabilityByTimeoff(slots, available, unavailable);
	}
	applyEditAvailability(available, unavailable);

	Timeslots_Byweek = [];

	if (is_wcenter_schedule) {
		slots = remove_busy_room_slots(slots);
	}

	if (slots.length > 0) {
		var start_min, end_min;

		for (var i=0; i<slots.length; i++) {
			var start = slots[i].start;
			var end = slots[i].end;

			slots[i].id = i + 1;

			if (start >= end) {
				slots.splice(i--,1);

			} else if (start.getDay()!=end.getDay() &&
					  (end.getHours() !== 0 || end.getMinutes() !== 0) &&
					  slots[i].timeoff != 1
					  ) {
				slots.splice(i--,1);
			} else {
				if (!slots[i].confirmed && slots[i].unavailable == 1) {
					UnconfirmedSlots.push(slots[i]);
				}
				//Everything OK
				if(slots[i].slot_id)
					updateTimeslotsByWeek(slots[i]);
			}
		}
	}

	// don't calculate anymore - use office hours saved in healer
	var earliestHour = Math.floor(minutesAfterMidnight(Office_Hours_Start) / 60);
	var latestHour = Math.ceil(minutesAfterMidnight(Office_Hours_End) / 60);

	Timeslots = slots;

	createCalendar(earliestHour, latestHour);
	if (!populateCalendar.firsttime) {
		createCalendar(earliestHour, latestHour);
		var calendar = $('#calendar');
		if(calendar.is(':visible')) {
			$('#saving_message').fadeOut(200);
			calendar.weekCalendar('refresh');
		}
	}

	if(typeof after_populate_calendar_refresh == 'function')
		after_populate_calendar_refresh();

	calendarWeekdaysStyle();

	if(populateCalendar.hide) {
		$('#calendar_container').hide();
		$('#not-available').hide();
	}

	populateCalendar.firsttime = false;
	populateCalendar.hide = false;
}

function calendarHeaderDate(date, calendar) {
	if(date.equals(Date.today())) {
		return 'Today';
	} else {
		var options = calendar.weekCalendar('option');
		var dayName = options.useShortDayNames ? options.shortDays[date.getDay()] : options.longDays[date.getDay()];
		return dayName + (options.headerSeparator) + calendar.weekCalendar('formatDate', date);
	}
}

function getCalendarTimeslotHeight() {
	return is_smallscreen() ? 42 : 22;
}

function calendarTimeslotHeight() {
	var timeslotHeight = getCalendarTimeslotHeight();
	if(timeslotHeight != $('#calendar').weekCalendar('option', 'timeslotHeight')) {
		$('#calendar').weekCalendar('option', 'timeslotHeight', timeslotHeight);
		$('#calendar').weekCalendar('refresh');
	}
}

function calendarWeekdaysStyle($calendar, newDate) {
	var calendar = $('#calendar');
	// return if no calendar is shown - to make schedule settings menu to work when schedule is not available.
	if (!calendar.length) {
		return;
	}
	if(typeof newDate == 'undefined') {
		newDate = calendar.weekCalendar('getCurrentFirstDay');
	}
	var firstDay = calendar.weekCalendar('option', 'firstDayOfWeek');
	var saturday = 6;
	var sunday = 0;
	if(firstDay !== 0) {
		saturday = 6-firstDay;
		sunday = 7-firstDay;
	}

	var minDate = calendar.weekCalendar('option', 'minDate');
	minDate = minDate.getDay()==firstDay ? minDate : minDate.addDays(firstDay - minDate.getDay());
	var yearDiff = newDate ? (newDate.getYear() - minDate.getYear())*365 : 0;
	var dateDiff = newDate ? newDate.getOrdinalNumber() + yearDiff - minDate.getOrdinalNumber() + 1 : 0;

	var currentDay = Date.today().getDay() - firstDay;
	if(!(dateDiff<7 && saturday==currentDay)) {
		calendar.find('td.day-'+(saturday+1)).addClass('wc-weekend');
	} else {
		calendar.find('td.day-'+(saturday+1)).removeClass('wc-weekend');
	}
	if(!(dateDiff<7 && sunday==currentDay)) {
		calendar.find('td.day-'+(sunday+1)).addClass('wc-weekend');
	} else {
		calendar.find('td.day-'+(sunday+1)).removeClass('wc-weekend');
	}

	calendar_title();
}

function removeDragHandle($event) {
	$('.ui-resizable-handle', $event).text('');
}

function getWeeksDiff(date1, date2) {
	return Math.ceil((stripTimezone(date2) - stripTimezone(date1))/(604800000)); //7*24*60*60*1000
}

function get_timeslots_for_week(start, updateSlotsFunction) {
	var weeksDiff = getWeeksDiff(StartSlotsDate, start);
	if(weeksDiff==WeeksToGenerate-1) {
		StartSlotsDate.addWeeks(WeeksToGenerate);

		var slots = Treatment ? GeneratedSlots : Timeslots;
		var new_slots = processSlotsRules(slots, StartSlotsDate);
		var unavailable_slots = new_slots['unavailable'];

		if(Treatment) {
			//fix time off not influencing repeated availability with limited dates thats over a month off
			var unavailable = _.filter(slots, function(slot) {return slot.timeoff==1;});
			unavailable_slots = new_slots['unavailable'].concat(unavailable);			
		}

		var available_slots = new_slots['available'];
		var all_new_slots = unavailable_slots.concat(available_slots);
		unavailable_slots = unavailable_slots.concat(
			_.filter(slots, function(slot) {return slot.unavailable==1;})
		);

		if(Treatment) {
			GeneratedSlots = GeneratedSlots.concat($.extend(true, [], all_new_slots));
			splitSlotsByTreatment(all_new_slots, available_slots, unavailable_slots);
		}
		solveUnavailableConflicts(available_slots, unavailable_slots);
		if(typeof Edit_Availability != 'undefined') {
			splitAvailabilityByTimeoff(all_new_slots, available_slots, _.filter(Timeslots, function(slot) {return slot.unavailable==1;}));
		}
		applyEditAvailability(available_slots, unavailable_slots);
		var prev_length = Timeslots.length;
		Timeslots = Timeslots.concat(all_new_slots);
		for (var i=prev_length; i<Timeslots.length; i++) {
			Timeslots[i].id = i + 1;
			updateTimeslotsByWeek(Timeslots[i]);
		}
	}
	var result = [];
	if (Timeslots_Byweek[start])
		result = Timeslots_Byweek[start];
	else
		result = Timeslots;
	if(typeof(updateSlotsFunction) == 'function') {
		updateSlotsFunction(result);
	}

	if (is_wcenter_schedule) {
		result = remove_busy_room_slots(result);
	}

	return _.filter(result, function(slot) {return !(slot.hide || slot.hide_tmp) && slot.slot_id;});
}

function minutesAfterMidnight(date) {
	date = typeof(date) == 'string' ? Date.parseExact(date, 'HH:mm') : date;
	return 60*date.getHours() + date.getMinutes();
}

function updateInitSlots(slots) {
	function filterInitSlots(element) {
		return (element.slot_id != slots[i].slot_id &&
				  element.unavailable == slots[i].unavailable) ||
				  element.unavailable != slots[i].unavailable;
	}

	for(var i in slots) {
		switch(slots[i].action) {
			case 'new':
				initSlots.push(slots[i]);
				break;
			case 'update':
				initSlots = _.filter(initSlots, filterInitSlots);
				initSlots.push(slots[i]);
				break;
			case 'delete':
				initSlots = _.filter(initSlots, filterInitSlots);
				break;
		}
	}
}

function updatedCalendar (result) {
	var callback;
	var button_name;
	if(dajaxProcess(result)) return;
	if(result.timeout_id) clearTimeout(result.timeout_id);
	if (result.intake_form_redirect) {
		callback = function(){
			var username;
			if (typeof center_username === 'undefined') {
				username = healer_username;
			} else {
				username = center_username;
			}
			window.location.href = url_intake_form + username;
		}
		button_name = 'Continue »';
	}
	showResult(result.message, result.title, callback, undefined, button_name);
	if (current_username && schedule_username != user_username) {
		schedule_switch(current_username);
	} else {
		if(result.slots.length > 0) {
			updateInitSlots(result.slots);
			getCalendar(initSlots);
		} else {
			getCalendar();
		}
	}
}

function is_schedule_available(){
	if (typeof schedule_username !== 'undefined') {
		return $('#new_appointment_container').length !== 0;
	} else {
		return true;
	}
}

function stripTimezone(date) {
	// block errors when schedule is not available.
	if (is_schedule_available()) {
		return Date.UTC(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes());
	}
}

function startCalendarRequest(calEvent, func, data, callback) {
	var timeout_id = onStartCalendarRequest(calEvent, func, data);
	data['timeout_id'] = timeout_id;
	func(callback, data);
}

function onStartCalendarRequest(calEvent, function_name, data) {
	JS_Error = '';
	if($('#calendar').is(':visible')) {
		var saving_el = $('#saving_message');
		if(!saving_el.length) {
			var el = $('.ui-widget-header.wc-toolbar');
			var saving_html = '<div id="saving_message" class="single_button" style="display:none; position:absolute; float:right; margin: 3px 0 0 650px; color:red; line-height: 1em;">Saving...</div>';
			el.prepend(saving_html);
			saving_el = $('#saving_message');
		}
		saving_el.fadeIn(200);
	}
	var timeout = new Timeout(function_name, data);
	if(calEvent) {
		calEvent.timeout_id = timeout.id;
	}
	return timeout.id;
}

function checkSaving(calEvent, $event) {
	if(calEvent.timeout_id) {
		if($event) {
			calEvent.start = $event.start;
			calEvent.end = $event.end;
			$('#calendar').weekCalendar("removeEvent", calEvent);
			$('#calendar').weekCalendar("updateEvent", $event);
		}
		return false;
	}
	return true;
}

function prepareFormData(form) {
	data = $(form).serialize(true);
	data += '&treatment_length=' + Treatment.id;
	return data;
}

function processDajax(data) {
	try {
		Dajax.process(data);
	} catch(e) {
		JS_Error = e;
	}
}

var Timeout = function(function_name, data) {
	this.function_name = function_name;
	this.data = data;
	this.initTimeout();
};

Timeout.prototype = {
	initTimeout: function() {
		var _this = this;
		this.id = setTimeout(function() {_this.ajaxTimeout();}, 15000);
	},
	ajaxTimeout: function() {
		onEndCalendarRequest();
		showError('Your changes were not saved. Please try again.', function() {
			location.reload(true);
		});
		if(initSlots) {
			populateCalendar(initSlots);
		} else {
			getCalendar();
		}
		new ErrorReport(this.function_name, this.data);
	}
};

var ErrorReport = function(function_name, data) {
	this.report = function_name + '\n' + JSON.stringify(data) + '\n';
	this.report += 'cookie: ' + navigator.cookieEnabled + '\n';
	if(JS_Error) {
		this.report += 'js error: ' + JS_Error + '\n';
		for (var prop in JS_Error)
		{
			this.report += prop + ' = ' + JS_Error[prop] + '; ';
		}
	}
	this.retry = 0;
	this.initTimeout();
};

ErrorReport.prototype = {
	initTimeout: function() {
		var that = this;
		this.id = setTimeout(function() {that.ajaxTimeout();}, 3000);
		this.retry += 1;
		this.send();
	},
	send: function() {
		var that = this;
		rest_ajax_post_request_no_timeout(url_error_report, function() {
			clearTimeout(that.id);
			that.id = null;
		}, {report: this.report});
	},
	ajaxTimeout: function() {
		if(this.retry < 10) {
			this.initTimeout();
		}
	}
};

function onEndCalendarRequest(timeout_id) {
	if(timeout_id) clearTimeout(timeout_id);
	$('#saving_message').fadeOut(200);
}

function newClientFailure(timeout_id, msg) {
	onEndCalendarRequest(timeout_id);
	if(typeof msg == 'undefined') {
		hs_dialog('#new_client_dialog', 'open');
	} else {
		showResult(msg);
	}
}

function loginFailure(timeout_id) {
	onEndCalendarRequest(timeout_id);
	hs_dialog('#login_dialog', 'open');
}

function calendar_title(date, calendar) {
	var $calendar = $('#calendar');
	var start_date = $calendar.weekCalendar('getCurrentFirstDay');
	var end_date = $calendar.weekCalendar('getCurrentLastDay');
	var m_names = ['January', 'February', 'March',
			  'April', 'May', 'June', 'July', 'August', 'September',
			  'October', 'November', 'December'];

	var m_names_short = ['Jan', 'Feb', 'Mar',
			  'Apr', 'May', 'June', 'July', 'Aug', 'Sept',
			  'Oct', 'Nov', 'Dec'];

	var prev = '<span onclick="$(\'#calendar\').weekCalendar(\'prevWeek\')" id="cal_prev">&lt;&lt;</span>';
	var start_string = m_names[start_date.getMonth()] + '&nbsp;&nbsp;' + start_date.getDate();

	var end_string;
	if (start_date.getMonth() == end_date.getMonth())
		end_string = end_date.getDate();
	else
		end_string = m_names_short[end_date.getMonth()] + ' ' + end_date.getDate();

	var next = '<span onclick="$(\'#calendar\').weekCalendar(\'nextWeek\')" id="cal_next">&gt;&gt;</span>';

	return prev + '<div style="min-width: 10em; display:inline-block; cursor:pointer;" id="cal_date" onclick="$(\'#calendar\').weekCalendar(\'today\')"> ' + start_string + ' - ' + end_string + ' </div>' + next;
}

current_location_id = 'all';

$(window).bind('unload', function() {} ); // call onload when back button pressed

//---------------------------------------------------------------------------------------------------------------------

function color_to_hex(color) {
	var hex = color.toString(16);
	return (hex.length > 1) ? hex : '0' + hex;
}

function hex_to_rgb(color) {
	r = parseInt(color.substr(1, 2), 16);
	g = parseInt(color.substr(3, 2), 16);
	b = parseInt(color.substr(5, 2), 16);
	return [r, g, b];
}

function make_dark_color(color, delta) {
	rgb = hex_to_rgb(color);
	hsl = rgbToHsl(rgb[0], rgb[1], rgb[2]);
	l = hsl[2] - delta;
	if (l < 0) l = 0;
	hsl[2] = l;

	rgb = hslToRgb(hsl[0], hsl[1], hsl[2]);
	return '#' + color_to_hex(rgb[0]) + color_to_hex(rgb[1]) + color_to_hex(rgb[2]);
}

/**
 * Converts an RGB color value to HSL. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
 * Assumes r, g, and b are contained in the set [0, 255] and
 * returns h, s, and l in the set [0, 1].
 *
 * @param   Number  r    The red color value
 * @param   Number  g    The green color value
 * @param   Number  b    The blue color value
 * @return  Array		The HSL representation
 */
function rgbToHsl(r, g, b){
	r /= 255;
	g /= 255;
	b /= 255;
	var max = Math.max(r, g, b), min = Math.min(r, g, b);
	var h, s, l = (max + min) / 2;

	if(max == min){
		h = s = 0; // achromatic
	}else{
		var d = max - min;
		s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
		switch(max){
			case r: h = (g - b) / d + (g < b ? 6 : 0); break;
			case g: h = (b - r) / d + 2; break;
			case b: h = (r - g) / d + 4; break;
		}
		h /= 6;
	}

	return [h, s, l];
}

/**
 * Converts an HSL color value to RGB. Conversion formula
 * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
 * Assumes h, s, and l are contained in the set [0, 1] and
 * returns r, g, and b in the set [0, 255].
 *
 * @param   Number  h       The hue
 * @param   Number  s       The saturation
 * @param   Number  l       The lightness
 * @return  Array           The RGB representation
 */
function hslToRgb(h, s, l){
	function hue2rgb(p, q, t){
		if(t < 0) t += 1;
		if(t > 1) t -= 1;
		if(t < 1/6) return p + (q - p) * 6 * t;
		if(t < 1/2) return q;
		if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
		return p;
	}
	var r, g, b;

	if(s === 0){
		r = g = b = l; // achromatic
	} else {
		var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
		var p = 2 * l - q;
		r = hue2rgb(p, q, h + 1/3);
		g = hue2rgb(p, q, h);
		b = hue2rgb(p, q, h - 1/3);
	}

	return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

// Checks if appointment conflicts with any of the slots for specific room_id
function is_no_room_conflict(appointment, slots, room_id) {
	function filter_timeslots_by_room(timeslots, room_id) {
		return timeslots.filter(function(slot) {
			return slot.room == room_id;
		});
	}

	slots = filter_timeslots_by_room(slots, room_id);
	slots = addSetupTimeToSlots(slots);
	slots = groupSlotsByDate(slots);
	if(slots) {
		return !checkConflict(appointment.start, appointment.end, slots);
	}
	return true;
}