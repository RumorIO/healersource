// function activate_payments_settings() {
// 	$('#full_deposit').click(function(){
// 		$('#partial_deposit_number').prop('disabled', true);
// 		$('input[name=deposit_percentage]').val(100);
// 	});
// 	$('#partial_deposit').click(function(){
// 		$('#partial_deposit_number').prop('disabled', false);
// 		$('#partial_deposit_number').focus();
// 	});

// 	$('#partial_deposit_number').change(function(){
// 		$('input[name=deposit_percentage]').val($(this).val());
// 	});

// 	function check_box(){
// 		var element_id;
// 		if (deposit_percentage == 100) {
// 			element_id = 'full_deposit';
// 		} else {
// 			element_id = 'partial_deposit';
// 		}
// 		$('#' + element_id).trigger('click');
// 	}

// 	function initiate_percentage_values(){
// 		$('input[name=deposit_percentage]').val(deposit_percentage);
// 		if (deposit_percentage != 100) {
// 			$('#partial_deposit_number').val(deposit_percentage);
// 		}
// 	}
// 	if (typeof deposit_percentage == 'undefined') {return;}
// 	check_box();
// 	initiate_percentage_values();
// }

// $(function(){
// 	activate_payments_settings();
// });