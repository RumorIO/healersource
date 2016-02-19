$(function () {
	activate_minutes_validation();
});

function check_length_validation() {
	function set_validity(message){
		var element = $('#id_length_minute');
		if (element[0]) {
			element[0].setCustomValidity(message);
		}
	}
	if ((parseInt($('#id_length_hour').val()) * 60 + parseInt($('#id_length_minute').val())) < 5) {
		set_validity('Ensure this value is greater than or equal to 5.');
	} else {
		set_validity('');
	}
}

function activate_minutes_validation() {
	$('#id_length_hour').change(function() {
		check_length_validation();
	});

	$('#id_length_minute').change(function() {
		check_length_validation();
	});
	check_length_validation();
}