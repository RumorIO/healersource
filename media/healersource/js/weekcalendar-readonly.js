var checkout_in_progress = false;

function fetchCalendar() {
	wcenter_id = typeof wcenter_id !== 'undefined' ? wcenter_id : false;
	var data = {healer: healer_username,
		only_my_locations: true};
	var treatment_type_id = Treatment.type;
	if (wcenter_id) {
		data.wcenter_id = wcenter_id;
		data.treatment_type_id = treatment_type_id;
		delete data.only_my_locations;
		Dajaxice.healers.getTimeslotsReadonly(function(slots){
			ScheduleDataCache[HealerId][treatment_type_id].initSlots = slots;
			loadScheduleData(HealerId, wcenter_id, Treatment);
		}, data);
	} else {
		Dajaxice.healers.getTimeslotsReadonly(populateCalendar, data);
	}
}

function openLoginDialog() {
	hs_dialog('close');
	hs_dialog("#login_dialog", "open");
}

function newClientSuccess(client) {}

function facebookLoginSuccess(id) {
    client_id = id;
	hs_dialog('close');
    hs_dialog("#booking_dialog", "open");
}

function booked(result) {
	if(result.confirm_email === true) {
		if(result.timeout_id) clearTimeout(result.timeout_id);
		if(result.user_email) user_email = result.user_email;
		hs_dialog('#confirm_email', {
			title:"Confirm email",
			title_class:'nav_login',
			buttons: {
				"Continue >>": function () {
					hs_dialog('close');
					hs_dialog("#booking_dialog", "open");
				}
			}
		});
		return;
	}
	checkout_in_progress = false;
	if(is_smallscreen() || is_mediumscreen()) fb.end(); // close schedule
	updatedCalendar(result);
	if (embed) {
		logout();
	}
}

function updateSlotTitles(slots) {
	for (i = 0; i < slots.length; i++) {
		slots[i].title = location_online[slots[i].location] ? "<a>Click To Book</a>" : "Call To Book";
	}
}

function changeTreatmentType(treatment_obj, is_treatment_mode, is_provider_mode, healer_id) {
	function get_title(){
		if (is_treatment_mode) {
			return length.title_center;
		} else {
			return length.title;
		}
	}

	function get_trigger_callback_function() {
		if (treatment_obj.lengths.length == 1) {
			return function() {
				$('#treatment_length span').first().trigger('click');
			};
		}
		return function(){};
	}

	$("#calendar_container, #provider_select, #locations_select, #no_availability_message").hide();
	$(".location_select").removeClass("selected");
	location_filter_id = false;

	$('#not-available').hide();
	var td = $("#treatment_length");
	var changeTreatmentCall = function (event) {
		changeTreatment(event.data.obj);
	};
	td.html("");
	var callback;
	if (treatment_obj.lengths) {
		for (var key in treatment_obj.lengths) {
			var length = treatment_obj.lengths[key];
			if (is_treatment_mode && available_treatment_lengths_treatment_mode.indexOf(length.id) === -1) {
				continue;
			}
			if (is_provider_mode && available_treatment_lengths_provider_mode.indexOf(length.id) === -1) {
				continue;
			}

			var link = $('<a href="javascript:void(0)" onclick="if(is_smallscreen()) {$(\'#fbContentWrapper\').scrollTo(\'#calendar\'); return false;}"></a>').append(get_title());
			var span = $('<span></span>')
						.bind('click', highlightButton)
						.bind('click', {obj:length},
							changeTreatmentCall).append(link);
			td.append(span).append('\n');

			callback = get_trigger_callback_function();

			if (is_provider_mode) {
				loadScheduleData(healer_id, wcenter_id, treatment_obj.lengths[0], true, callback);
			} else {
				callback();
			}
		}
	} else {
		callback = function(treatment) {
			changeTreatment(treatment);
		};

		if (is_provider_mode) {
			loadScheduleData(healer_id, wcenter_id, treatment_obj, true, callback);
		} else {
			callback(treatment_obj);
		}

	}

	$("#treatment_type_select_length").show();
	if(is_smallscreen()) {
		$('#fbContentWrapper').scrollTo('#treatment_type_select_length');
	}

	$('#providers_list').hide();
	$('#providers_list_filter').hide();
	$('#show_at_this_center').show();
}

function show_calendar(){
	$('#no_availability_message').hide();
	$("#calendar_container").show();
	populateCalendar(initSlots);
	calendarWeekdaysStyle();

	// Hide calendar if there are no slots visible and show no availability message
	// tslots = _.filter(Timeslots, function(slot) {return !slot.hide});
	if (Timeslots.length == 0) {
		$("#calendar_container").hide();
		$('#no_availability_message').show();
	}
}

function switchLocation(location_id) {
	location_filter_id = location_id;
	if ((typeof(current_mode) != 'undefined') && (current_mode == 'treatment')) {
		loadWcenterProviders(Treatment);
	} else {
		show_calendar();
	}
}

function changeTreatment(treatment) {
	Treatment = treatment;
	$("#calendar_container").hide();
	$(".location_select").removeClass("selected");
	if ($(".location_select").length == 1) {
		$(".location_select").first().trigger('click');
	} else {
		$('#locations_select').show();
	}
}

function show_booking_dialog(calEvent) {
	if (calEvent.readOnly)
		return;

	if(typeof(Preview) != 'undefined') {
		fb.start("<p class='message nav_icon nav_info' style='margin-right: 20px;'>Online Booking is Disabled in Preview</p>");
		return;
	}

	if(location_online[calEvent.location] === 0) {
		showResult($('#healer_contact_box > div').html(), "Contact");
		return;
	}

	$("input[name='timeslot']").val(calEvent.slot_id);
	$("input[name='start']").val(stripTimezone(calEvent.start));
	update_appointment_details($('#calendar'), calEvent, "#dialog_date", "#dialog_time", "#dialog_treatment", "#dialog_location");
	if (!client_id) {
		hs_dialog($("#new_client_or_login_dialog"), "open");
	} else {
		hs_dialog($("#booking_dialog"), "open");
	}
}

function position_not_available(preserve_visibility) {
	var $not_available = $("#not-available");
	// var $calendar = $('#calendar');

	var visible = $not_available.is(':visible');
	// var height = $(".wc-toolbar").outerHeight() + $(".wc-header").outerHeight() + $(".wc-time-slots").outerHeight();
	// var _top = $calendar.offset().top + $('.fill_window:last').scrollTop() + height / 2;
	// var _left = $calendar.offset().left + ($calendar.width() + $(".wc-grid-timeslot-header").width() - $not_available.width()) / 2;
	// $not_available.css("top", Math.round(_top)).css("left", Math.round(_left)).show();

	if (preserve_visibility) {
		if (visible) {
			$not_available.css('display', 'inline-block');
		} else {
			$not_available.hide();
		}
	} else {
		$not_available.css('display', 'inline-block');
	}
}

function createCalendar(start, end) {
	var $calendar = $('#calendar');
	var id = 10;
	var dialog_title = Appointment_Dialog_Title + " an Appointment";

	var calendar_size = end - start;
	if (calendar_size < 5)
		end += 5 - calendar_size;

	hs_dialog($("#new_client_or_login_dialog"), {
		autoOpen:false,
		title: dialog_title,
		open:function () {
			clearForm($dialogNewBookingUnreg);
		}
	});

	var $dialogNewBookingUnreg = $("#new_client_dialog");
	hs_dialog($dialogNewBookingUnreg, {
		autoOpen:false,
		title:"New Client",
		title_class:'nav_client',
		open:function () {
			$dialogNewBookingUnreg.find("input[name='first_name']").blur();
		},
		buttons: {
			"Next >>": function () {
				rest_ajax_post_request(url_ajax_signup_client, function(result){
					if (typeof result == 'number') {
						$('#new_user_error_list').html('');
						// $('#new_user_errors').removeClass('ui-helper-clearfix');
						$('#new_user_errors').addClass('ui-helper-hidden');
						client_id = result;
						hs_dialog("close");
						hs_dialog($dialogBooking, "open");
					} else {
						$('img.captcha').attr('src', result.captcha_image);
						$('#id_security_verification_0').val(result.captcha_code);
						$('#id_security_verification_1').val('');
						$('#new_user_error_list').html(result.error);
						// $('#new_user_errors').addClass('ui-helper-clearfix');
						$('#new_user_errors').removeClass('ui-helper-hidden');
						fb.resize();
					}
				}, {data: prepareFormData('#new_user_form')});
			}
		}
	});

	var $dialogLogin = $("#login_dialog");
	hs_dialog($dialogLogin, {
		autoOpen:false,
		title:"Log In",
		title_class:'nav_login',
		open:function () {
			$('#id_password', $dialogLogin).val('');
		},
		buttons: {
			"Next >>":function () {
				rest_ajax_post_request(url_ajax_login, function(result){
					if (typeof result == 'number') {
						$('#login_errors').removeClass('ui-helper-clearfix');
						$('#login_errors').addClass('ui-helper-hidden');
						$('#login_form input').removeClass('error');
						client_id = result;
						hs_dialog("close");
						hs_dialog($dialogBooking, "open");
					} else {
						$('#login_errors').addClass('ui-helper-clearfix');
						$('#login_errors').removeClass('ui-helper-hidden');
						$('#login_form input').addClass('error');
						$('#login_error_list').html(result);
						$('#login_dialog_failure_msg').show();
						fb.resize();
					}
				}, {data: prepareFormData('#login_form')});
			}
		}
	});
	var $dialogBooking = $("#booking_dialog");
	function get_note(){
		var note = $dialogBooking.find("textarea[name='note']").val();
		if (typeof note == 'undefined') {
			note = '';
		}
		return note;
	}

	hs_dialog($dialogBooking, {
		autoOpen:false,
		title: dialog_title,
		open:function (event, ui) {
			var note = get_note();
			clearForm($dialogBooking);
			$dialogBooking.find("textarea[name='note']").val(note);
			$dialogBooking.find("textarea[name='note']").show();
			$dialogBooking.find("textarea[name='note']").blur();
			$dialogBooking.find("#discount_code").blur();
		},
		buttons: {
			'Book Now':function () {
				function get_discount_code(){
					var code = $('#discount_code').val();
					if (typeof code == 'undefined') {
						code = '';
					}
					return code;
				}

				if(Cancellation_Policy && !$('#cancellation_policy_checkbox').is(":checked")) {
					$('#cancellation_policy_enforce').show();
					return;
				}

				var note = get_note();
				var timeout_id;
				var timeslot = $dialogBooking.find("input[name='timeslot']").val();
				var start = parseInt($dialogBooking.find("input[name='start']").val());
				var data = {
					'timeslot':timeslot,
					'start':start,
					'treatment_length':Treatment.id,
					'client':client_id,
					'note':note,
					'discount_code': get_discount_code(),
				};

				if (is_deposit_required) {
					// check conflicts before checkout
					startCalendarRequest(null, Dajaxice.healers.timeslot_book,
						$.extend({check_for_conflicts: true}, data), function(result){
							function reset_saving_indicator(){
								$('#saving_message').fadeOut(200);
							}

							function checkout() {
								var label;
								var amount = result.amount;
								if (result.card_autosave) {
									label = 'Save Card';
									amount = 0;
								}
								checkout_in_progress = true;
								stripe_checkout(data, label, reset_saving_indicator, user_email, undefined, amount, result.description, key);
							}

							function save_card(){
								data.save_card = true;
								key = stripe_app_public_key;
								checkout();
							}

							if (result.timeout_id) clearTimeout(result.timeout_id);
							if (result.no_conflicts && result.amount > 0 && !result.has_card) {
								var key;
								if (result.card_autosave) {
									save_card();
								} else {
									hs_dialog($('#save_card'), {
										title:"Save card",
										close: function(){
											if (!checkout_in_progress) {
												reset_saving_indicator();
											}
										},
										buttons:{
											"No": {
												button_class: 'float_right',
												click: function () {
													checkout();
													hs_dialog("close");
												}
											},
											"Yes": {
												button_class: 'float_right',
												click: function () {
													save_card();
													hs_dialog("close");
												}
											},
										}
									});
								}
							} else {
								data.skip_charge = true;
								startCalendarRequest(null,
									Dajaxice.healers.timeslot_book, data, booked);
							}
						});
				} else {
					startCalendarRequest(null,
						Dajaxice.healers.timeslot_book, data, booked);
				}
				hs_dialog("close");
			}
		}
	});

	$calendar.weekCalendar({
		timeslotHeight:getCalendarTimeslotHeight(),
		textSize:10,
		readonly:true,
		dateFormat:"n/j",
		useShortDayNames:true,
		timeSeparator:" - ",
		timeFormat:"g:i a",
		headerSeparator:' ',
		timeslotsPerHour:2,
		allowCalEventOverlap:true,
		overlapEventsSeparate:true,
		firstDayOfWeek: get_first_day_of_week(),
		businessHours:{start:start, end:end, limitDisplay:true },
		daysToShow:7,
		minDate:Date.today(),
		maxDate:Date.today().addDays(bookAheadDays),
		title:calendar_title,
		calendarAfterLoad:function ($calendar) {
			if (($calendar.weekCalendar("serializeEvents").length === 0) && ($('#calendar').is(":visible"))) {
				position_not_available(false);
			} else {
				$("#not-available").hide();
			}

			if (!Is_Mobile) {
				$('.wc-cal-event')
							.attr('data-fb-tooltip', 'source:#appointment_details attachToHost:true fadeDuration:0 delay:10 placement:right width:200')
							.mouseenter(function(obj) {
								update_appointment_details($calendar, this.calEvent, "#tooltip_date", "#tooltip_time", "#tooltip_treatment", "#tooltip_location");
								if (location_online[this.calEvent.location]) {
									$('#tooltip_book_now').show();
									$('#tooltip_contact').hide();

									$('#tooltip_book_now')[0].calEvent = this.calEvent;
								} else {
									$('#tooltip_book_now').hide();
									$('#tooltip_contact').show();
								}
							});

				if(typeof(Preview) == 'undefined')
					$('.wc-cal-event').addClass('fbTooltip');

				fb.activate();
			}
		},
		height:function ($calendar) {
			return $(".wc-toolbar").outerHeight() + $(".wc-header").outerHeight() + $(".wc-time-slots").outerHeight();		//$(window).height() - $("h1").outerHeight() - 1;
		},
		getHeaderDate:calendarHeaderDate,
		changedate:calendarWeekdaysStyle,
		eventHeader:function (calEvent, calendar) {
			var options = calendar.weekCalendar('option');
			return calendar.weekCalendar(
						'formatDate', calEvent.start, "g:i") +
						options.timeSeparator +
						calendar.weekCalendar(
									'formatDate', calEvent.end, "g:i");
		},
		eventRender:function (calEvent, $event) {
			if (typeof($event[0].calEvent) === 'undefined')
				$event[0].calEvent = calEvent;

			backgroundColor = location_colors[calEvent.location];
			timeBackgroundColor = location_colors_dark[calEvent.location];

			$event.css({
				"backgroundColor":backgroundColor
			});

			$event.find(".wc-time").css({
				"backgroundColor":timeBackgroundColor
			});
		},
		eventAfterRender:function (calEvent, $event) {
			$event.find(".wc-title").css({
				"line-height":$event.outerHeight() / 2 + "px"
			});
		},
		eventClick:function (calEvent, $event) {
			show_booking_dialog(calEvent);
		},
		data:function (start, end, callback) {
			callback(get_timeslots_for_week(start, updateSlotTitles));
		}
	});
}

$(function() {
	$(window).resize(calendarTimeslotHeight);
});

function checkout_callback(token, data){
	data.card_token = token;
	startCalendarRequest(null, Dajaxice.healers.timeslot_book, data, booked);
}

function go_to_first_availability(){
	function switch_to_first_availability(){
		if ($('#calendar').find('.wc-cal-event').length == 0) {
			if (counter > 12) {
				$('#calendar').weekCalendar('today');
			} else {
				$('#calendar').weekCalendar('nextWeek');
				counter++;
				switch_to_first_availability();
			}
		}
	}
	var counter = 1;
	switch_to_first_availability();
}
