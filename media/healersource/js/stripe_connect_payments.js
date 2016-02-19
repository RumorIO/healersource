var filters = {};

function client_appointments(data){
	var client_appointments_callback = function(response){
		function activate_checkboxes(){
			$('.appointment_checkbox').change(function(){
				recount_total();
			});
		}

		function recount_total(){
			var total = 0;
			$('.appointment_checkbox:checked').each(function(){
				total += parseFloat($(this).data('amount'));
			});
			$('#total').html(formatCurrency(total));
		}

		function get_selected_appointments(){
			var appointments = [];
			$('.appointment_checkbox:checked').each(function(){
				appointments.push({id: $(this).data('id'),
					date: $(this).data('date')});
			});
			return appointments;
		}

		if (response.error) {
			showError(response.error);
			return;
		}
		if (response.has_card) {
			if (response.appointments.length > 1){
				var dialog = $('#client_appointments_dialog');
				dialog.html(response.html);
				recount_total();
				activate_checkboxes();
				hs_dialog(dialog, {
					title: 'Balance',
					title_class: 'nav_payments_nopos',
					buttons: {
						'Charge Card': function() {
							var appointments = get_selected_appointments();
							if (appointments.length > 0) {
								charge_card(appointments);
								hs_dialog('close');
							}
						}
					}
				});
			} else {
				charge_card(response.appointments);
			}
		} else {
			stripe_checkout(data, 'Save Card', undefined, response.client_email);
		}
	};
	rest_ajax_post_request_long_timeout(url_client_appointments, client_appointments_callback, data);
}

function charge_card(appointments){
	rest_ajax_post_request_long_timeout(url_charge_card, function(response){
		if (response.error) {
			showResult(response.error);
			return;
		}
		load_payments();
	}, {'appointments': JSON.stringify(appointments)});
}

function checkout_callback(token, data){
	data.card_token = token;
	client_appointments(data);
}

function activate_select() {
	$('.payment_action').click(function(){
		var element = $(this).parent().parent();
		var data = {
			id: element.data('id'),
			date: element.data('date')
		};

		var action = $(this).data('action');

		if (action == 'mark_unpaid') {
			rest_ajax_post_request(url_mark_unpaid, load_payments, data);
		} else if (action == 'mark_paid') {
			rest_ajax_post_request(url_mark_paid, load_payments, data);
		} else if (action == 'charge_card') {
			client_appointments(data);
		}
	});
	activate_selection_menus();
}

function load_payments(){
	rest_ajax_get_request(url_load_payments,
		function(response){
			if (response.error) {
				showError(response.error);
			} else {
				$('#appointment_list').html(response.html).show();
				activate_select();
				var selected_paid_filter = $('.paid_filter').filter('.selected');
				if (selected_paid_filter.length > 0) {
					selected_paid_filter.trigger('click');
				}
				show_hide_nothing_found_message();
				fb.activateElements();
			}
		}, filters
	);
}

function show_hide_nothing_found_message(){
	$('#appointment_list').show();
	if (!$('.appointment').is(':visible')){
		$('#appointment_list').hide();
		$('#nothing_found').show();
	} else {
		$('#nothing_found').hide();
	}
}

function reset_filters(){
	filters = {}
	initiate_dates();
	clear_client_filter();
}

function clear_client_filter(){
	$('#client').val('');
	delete filters.client;
	$('#clear_client_filter_button').hide();
	load_payments();
}

function initiate_dates(){
	$('#date_start').val(initial_dates.start);
	$('#date_end').val(initial_dates.end);
	filters.start_date = initial_dates.start;
	filters.end_date = initial_dates.end;
}


function open_discount_codes_dialog(appointment_id, discount_code_id){
	$('#discount_code').val(discount_code_id);

	hs_dialog($('#discount_codes_dialog'), {
		title: 'Discount',
		autoFit: true,
		title_class: 'nav_payments_nopos',
		buttons: {
			Save: function() {
				rest_ajax_post_request(url_save_discount_code, function(){
					hs_dialog('close');
					load_payments();
				}, {
					discount_code_id: $('#discount_code').val(),
					appointment_id: appointment_id
				});
			}
		}
	});
}

$(function(){
	function activate_paid_filters(){
		function process_filter_results(){
			function show_hide_dividers(){
				$('.divider').show().each(function(){
					if (!$(this).nextUntil('.divider').is(':visible')) {
						$(this).hide();
					}
				});
			}

			show_hide_nothing_found_message();
			show_hide_dividers();
		}

		function paid_filter(element, class_to_hide){
			$('.appointment').show();
			if (element.hasClass('selected')) {
				element.removeClass('selected');
			} else {
				$('.' + class_to_hide).hide();
				$('.paid_filter').removeClass('selected');
				element.addClass('selected');
			}
			process_filter_results();
		}

		$('.paid_filter').unbind('click'); // reset binding
		$('#filter_unpaid').click(function(){
			paid_filter($(this), 'appointment_paid');
		});

		$('#filter_paid').click(function(){
			paid_filter($(this), 'appointment_unpaid');
		});
	}

	function initiate_date_filters(){
		$('#date_start').datepicker({
			onSelect: function(selectedDate){
				filters.start_date = selectedDate;
				load_payments();
			},
			onClose: function(selectedDate) {
				$('#date_end').datepicker('option', 'minDate', selectedDate);
			},
		});

		$('#date_end').datepicker({
			onSelect: function(selectedDate){
				filters.end_date = selectedDate;
				load_payments();
			},
			onClose: function(selectedDate) {
				$('#date_start').datepicker('option', 'maxDate', selectedDate);
			},
		});
	}

	function initClientSearchAutocomplete() {
		var source = function(request, response) {
			var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), 'i');
			response($.grep(clients, function(value) {
				return matcher.test(value.value);
			}));
		};

		$('#client').autocomplete({
			source: source,
			minLength: 2,
			html: true,
			autoFocus: true,
			select: function(event, ui) {
				filters.client = ui.item.id;
				$('#client').val(ui.item.value);
				load_payments();
				$('#clear_client_filter_button').show();
				return false;
			}
		}).keypress(function(e){
			if (e.keyCode == 13 && !$(this).val()) {
				clear_client_filter();
			}
		});
	}

	initiate_dates();
	load_payments();
	activate_paid_filters();
	initClientSearchAutocomplete();
	initiate_date_filters();
});
