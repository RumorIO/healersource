var default_payment_value = 15.15;
var block_save_settings = false;

function save_settings(){
	function get_payment_notes_value(){
		if ($('#notes_disable').prop('checked')) {
			return 0;
		} else {
			return payment_notes;
		}
	}

	function get_payment_schedule_setting_value(){
		var input = $('input[name="payment_schedule_setting"]');
		if (input.length > 0) {
			return $('input[name="payment_schedule_setting"]:checked').val();
		} else {
			return payment_schedule_setting;
		}
	}

	if (block_save_settings) {
		return;
	}

	if (!can_charge) {
		checkout(true);
		return;
	}

	var payment_schedule_setting_value = get_payment_schedule_setting_value();
	var payment_notes_value = get_payment_notes_value();
	if (payment_schedule_setting_value == '3' && !can_charge) {return;}
	rest_ajax_post_request_long_timeout(url_save_account_settings, function(error){
		if (error) {
			showError('There was an error updating your subscription, please try again.<br>' + error);
		} else {
			showSuccess('Subscription updated successfully!');
		}
	}, {
		payment_schedule: payment_schedule,
		payment_notes: payment_notes_value,
		payment_schedule_setting: payment_schedule_setting_value
	});
}

$(function(){
	function activate_account_settings(){
		function update_values_schedule() {
			var total = (number_of_providers * payment_schedule);
			if (total < payment_schedule_unlim) {
				$('#schedule_value').html('$' + payment_schedule);
				$('#total').html('$' + total + ' Total Monthly');
			} else {
				$('#payment_block_schedule').html('$' + payment_schedule_unlim + ' Unlimited Plan');
			}
		}

		function show_hide_payment_schedule_and_notes_blocks() {
			if ($('input[name="payment_schedule_setting"]:checked').val() == '3') {
				$('#payment_block_schedule').css('display', 'inline-block');
				$('#notes').hide();
			} else {
				$('#payment_block_schedule').hide();
				$('#notes').show();
			}
		}

		function activate_buttons(type){
			function set_initial_value(){
				var to_select;
				if (is_enabled) {
					to_select = 'on';
				} else {
					to_select = 'off';
				}
				$('#' + type + '_' + to_select).addClass('selected');
			}

			$('#' + type + '_on').click(function(){
				if (type == 'notes') {
					payment_notes = default_payment_notes;
				} else if (type == 'schedule') {
					payment_schedule_setting = 3;
				}
				save_settings();
			});

			$('#' + type + '_off').click(function(){
				if (type == 'notes') {
					payment_notes = 0;
				} else if (type == 'schedule') {
					payment_schedule_setting = 1;
				}
				save_settings();
			});

			if (type == 'notes') {
				is_enabled = payment_notes !== 0;
			} else if (type == 'schedule') {
				is_enabled = payment_schedule_setting == 3;
			}
			set_initial_value();
		}

		function activate_schedule_select(){
			$('input[name="payment_schedule_setting"]').click(save_settings);
		}

		if (typeof payment_schedule == 'undefined') {
			return;
		}

		update_values_schedule();

		$($('input[name="payment_schedule_setting"]')[payment_schedule_setting - 1]).prop('checked', true);
		$('input[name="payment_schedule_setting"]').change(show_hide_payment_schedule_and_notes_blocks);
		show_hide_payment_schedule_and_notes_blocks();

		activate_buttons('notes');
		if (!is_wellness_center) {
			activate_buttons('schedule');
		}
		activate_schedule_select();
	}
	activate_account_settings();
});
