function display_or_hide_location_form(){
	if ($('#id_location').val() == 'new_location') {
		$('#location_form').show();
	} else {
		$('#location_form').hide();
	}
}

$(function(){
	$('#id_location').after($('#location_form'));
	$('#id_location').change(display_or_hide_location_form);
	display_or_hide_location_form();
});
