additional_setting_action = function() {
	if ($('#id_gift_certificates').prop('checked') && !stripe_connect_enabled) {
		$('#stripe_connect_required').slideDown();
	} else {
		$('#gift_certificate_form').submit();
	}
}

$(function(){
	activate_selection_menus();
});