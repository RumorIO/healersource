$(function(){
	$(".datepicker").datepicker();
	$('#id_start_0').change(function(){
		if (Date.parse($(this).val()) > Date.parse($('#id_end_0').val())) {
			$('#id_end_0').val($(this).val());
		}
	});
});

function submit_form() {
	function is_valid_dates(){
		function get_date(id){
			function fix_time(time) {
				return time.replace('PM', ' PM').replace('AM', ' AM');
			}
			var date = $(id + '_0').val() + ' ' + fix_time($(id + '_1').val());
			return new Date(date);
		}
		var start = get_date('#id_start');
		var end = get_date('#id_end');
		return end > start;
	}

	if (is_valid_dates()) {
		$('.event_form').submit();
	} else {
		showError('Please make sure Start Date is before End Date.');
	}
}
