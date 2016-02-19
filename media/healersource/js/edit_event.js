$(function(){
	initProviderSearchAutocomplete();
	initAttendeeAutocomplete();
	initNewClientDialog('New Guest');
	$('#photo-clear_id').change(function(){
		var opacity;
		if ($(this).is(':checked')) {
			opacity = 0.5;
		} else {
			opacity = 1;
		}
		$('#event_photo').css('opacity', opacity);
	});
	$('input:file').change(function (){
		$('#event_photo').hide();
	});
});

function initProviderSearchAutocomplete() {
	$('#add_host').autocomplete({
		source: url_autocomplete_providers,
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			var healer_id = ui.item.id;
			rest_ajax_post_request([url_add_host, healer_id], function(html){
					$('#hosts').append(html);
					$('#add_host').val('');
				}, undefined, function(){
					$('#add_host').val('');
				});
		}
	});
}

function remove_host(event_id, healer_id){
	rest_ajax_post_request([url_remove_host, healer_id], function(html){
		$('#host_' + healer_id).remove();
	});
}

function newClientSuccess(person) {
	add_attendee(person);
}
