var ScheduleDataCache = {};
var HealerId;
var current_mode = 'treatment';
var schedule_appointment_treatment_html;
var schedule_appointment_provider_html;
var available_treatment_lengths_provider_mode;
var selected_location_id;

function select_treatment_type_if_only_one_available(){
	if ($('.treatment_title').length == 1) {
		$('.treatment_title').trigger('click');
	}
}

function set_schedule_appointment_mode(mode){
	function activate_schedule_appointment_provider_mode_links(){
		$('.provider-item').click(function(){
				$('.provider-item').removeClass('single_button');
				$(this).addClass('single_button');
				$('#calendar_container').hide();
				$('.provider-item:not(.single_button)').parent().hide();
				$('#back_to_provider').css('display', 'inline');
				loadWcenterProviderTreatments($(this).data('healer-id'));
		});
		if ($('.provider-item').length == 1) {
			$('.provider-link').trigger('click');
		}
	}

	current_mode = mode;
	if (mode == 'provider') {
		$('#schedule_appointment_mode_treatment').html('');
		$('#schedule_appointment_mode_provider').html(schedule_appointment_provider_html);
		activate_schedule_appointment_provider_mode_links();
	} else if (mode == 'treatment') {
		$('#schedule_appointment_mode_provider').html('');
		$('#schedule_appointment_mode_treatment').html(schedule_appointment_treatment_html);
		select_treatment_type_if_only_one_available();
	}

	activate_container_buttons();

	$('.schedule_appointment_mode,#calendar_container,#back_to_provider').hide();
	$('#schedule_appointment_mode_' + mode).show();
}

function loadWcenterProviderTreatments(healer_id){
	ajax_request(Dajaxice.healers.load_wcenter_provider_treatments, function(data){
		$('#treatments_content').html(data.html);
		activate_container_buttons();
		available_treatment_lengths_provider_mode = data.available_treatment_lengths;
		select_treatment_type_if_only_one_available();
	}, {
		wcenter_id: wcenter_id,
		healer_id: healer_id,
		location_id: selected_location_id,
	});
}

function loadWcenterProviders(treatment){
	var treatment_type_length_id = treatment.id;
	if (typeof embedded_separate_center_provider_schedule !== 'undefined' && embedded_separate_center_provider_schedule) {
		loadScheduleData(healer_id, wcenter_id, treatment);
	} else {
		ajax_request(Dajaxice.healers.load_wcenter_providers, function(data){
			$('#provider_list').html(data.html);
			$('.provider-link').click(function(){
				$('.provider-item').removeClass('single_button');
				$(this).parent().addClass('single_button');
				loadScheduleData($(this).data('healer-id'), wcenter_id,
					$.parseJSON(data.treatment_type_lengths[$(this).data('treatment-type-length-id')]));
			});

			if (is_skip_provider_step) {
				$('.provider-link').first().trigger('click');
			} else {
				$('#provider_select').show();
				fb.activate();
				if ($('#provider_select').find('.provider-item').length == 1) {
					$('.provider-link').trigger('click');
				} else {
					$('#calendar_container').hide();
				}
			}
		}, {
			wcenter_id: wcenter_id,
			treatment_type_length_id: treatment_type_length_id,
		});
	}
}

function loadScheduleData(healer_id, wcenter_id, treatment, is_provider_mode_request, callback){
	is_wcenter_schedule = true;
	WeeksToGenerate = 13;
	function load_schedule_data(){
		data = ScheduleDataCache[healer_id][treatment_type_id];
		HealerId = healer_id;
		healer_username = data.healer_username;
		healer_fullname = data.healer_fullname;
		bookAheadDays = data.bookAheadDays;
		First_Bookable_Time = data.First_Bookable_Time;
		setupTime = data.setupTime;
		initSlots = data.initSlots;
		Office_Hours_Start = data.Office_Hours_Start;
		Office_Hours_End = data.Office_Hours_End;
		Appointment_Dialog_Title = data.Appointment_Dialog_Title;
		OtherHealersAppointmentsSlots = data.OtherHealersAppointmentsSlots;
		AvailableRooms = data.AvailableRooms;
		$('#locations_select').show();
		Treatment = treatment;
		if (!is_provider_mode_request) {
			show_calendar();
		}
		if (typeof callback !== 'undefined') {
			callback(treatment);
		}
	}

	var treatment_type_id = treatment.type;
	if (healer_id in ScheduleDataCache && treatment_type_id in ScheduleDataCache[healer_id]) {
		load_schedule_data();
	} else {
		ajax_request(Dajaxice.healers.load_wcenter_schedule_data, function(data){
			if (!(healer_id in ScheduleDataCache)) {
				ScheduleDataCache[healer_id] = {};
			}
			if (!(treatment_type_id in ScheduleDataCache[healer_id])) {
				ScheduleDataCache[healer_id][treatment_type_id] = {};
			}
			var other_healer_appts_slots = expand_data($.parseJSON(data.other_healers_appointments));
			prepareSlotsDates(other_healer_appts_slots);
			ScheduleDataCache[healer_id][treatment_type_id] = {
				healer_username: data.username,
				healer_fullname: data.name,
				bookAheadDays: data.bookAheadDays,
				First_Bookable_Time: Date.parseExact(data.first_bookable_time, "yyyy-MM-ddTHH:mm:ss"),
				setupTime: data.setup_time,
				initSlots: $.parseJSON(data.timeslot_list),
				Office_Hours_Start: data.office_hours_start,
				Office_Hours_End: data.office_hours_end,
				Appointment_Dialog_Title: data.appt_schedule_or_request,
				OtherHealersAppointmentsSlots: other_healer_appts_slots,
				AvailableRooms: data.rooms,
			};
			load_schedule_data();
		}, {healer_id: healer_id,
		wcenter_id: wcenter_id,
		treatment_type_id: treatment_type_id});
	}
}

$(function() {
	$('#show_at_this_center').click(function() {
		$('#providers_list').show();
		$('#providers_list_filter').show();
	});

	schedule_appointment_treatment_html = $('#schedule_appointment_mode_treatment').html();
	schedule_appointment_provider_html = $('#schedule_appointment_mode_provider').html();
	$('#schedule_appointment_mode_provider').html('');
	select_treatment_type_if_only_one_available();
});

function filterProviders(speciality_id) {
	if(speciality_id == 0) {
		$("#providers_list li").show();
	} else {
		$("#providers_list li").hide();
		if(speciality_id) {
			$("#providers_list li.spec_" + speciality_id).show();
		}
	}
}