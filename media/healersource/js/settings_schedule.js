function save_schedule_setting() {
	function get_selected_common_availability(){
		return $('input[name="common_availability"]:checked').val() == 'True';
	}

	if (common_availability_change_check && get_selected_common_availability() !== original_common_availability) {
		if (!confirm('Changing this setting will delete ALL Availability at your center. ' +
				'Your Appointments will not be affected. Are you REALLY SURE?')) {
			$('input[name="common_availability"]').not(':checked').prop('checked', true);
			return;
		}
	}
	$('#schedule_settings_form').submit();
}
