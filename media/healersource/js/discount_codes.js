$(function(){
	$('#save_discount_code').click(function(){
		$('.errorMessages').html('');
		if ($('#id_type').val() == '%') {
			if (parseFloat($('#id_amount').val()) > 100) {
				$('.errorMessages').html('<li>Amount value has to be less or equal to 100%</li>');
				return;
			}
		}
		$('#discount_code_form').find(':submit').click();
	});
});
