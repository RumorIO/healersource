function save_settings(){
	rest_ajax_post_request_long_timeout(url_save_account_settings, function(error){
		if (error) {
			showError("There was an error updating user's subscription, please try again.<br>" + error);
		} else {
			showSuccess('Subscription updated successfully!');
		}
	}, {
		payment_schedule: $('#amount').val(),
		user_id: user_id,
	});
}
