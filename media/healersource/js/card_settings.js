function checkout(data, callback) {
	block_save_settings = true;
	stripe_checkout(data, 'Save Card', function(){
		if (!$('#loading').is(':visible')) {
			block_save_settings = false;
		}
	}, user_email, callback);
}

var checkout_callback = function(token, save_settings_on_callback){
	function get_loading_element(){
		if (!save_settings_on_callback) {
			return 'loading_card';
		}
	}

	var data = {stripe_token: token};
	if (typeof healer_account_setting_page !== 'undefined'){
		data.history = true;
	}

	rest_ajax_post_request_long_timeout(url_save_card,
		function(data){
			if (data.error) {
				showError('There was an error saving your card, please try again.<br>' + error);
			} else {
				$('#card_settings').html(data.html);
				can_charge = true;
				if (save_settings_on_callback) {
					save_settings();
				}
			}
			block_save_settings = false;
		}, data, function(){
			block_save_settings = false;
		}, undefined, undefined, get_loading_element()
	);
}

var checkout_callback_payments_settings = function(token){
	var data = {stripe_token: token};
	rest_ajax_post_request_long_timeout(url_save_card,
		function(data){
			if (data.error) {
				showError('There was an error saving your card, please try again.<br>' + error);
			} else {
				$('#id_booking_healersource_fee_1').prop('checked', true);
				$('#loading').show();
				$('#payments_settings').submit();
			}
		}, data
	);
}
