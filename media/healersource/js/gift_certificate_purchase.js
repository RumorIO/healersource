function checkout(){
	if (!is_authenticated) {
		user_email = $('#id_purchased_by_email').val();
	}
	if (!has_card) {
		stripe_checkout(undefined, undefined, undefined, user_email,
			parseInt($('#id_amount').val()), 'Gift Certificate');
	} else {
		$('#gift_certificate_purchase').submit();
	}
}


function checkout_callback(token, data){
	$('#id_card_token').val(token)
	$('#gift_certificate_purchase').submit();
}


$(function(){
	$('#id_amount').before('<div class="float_left">$ </div>');
});