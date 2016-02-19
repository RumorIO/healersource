$(function(){
	initAttendeeAutocomplete('full');
	initNewClientDialog('New Guest');
});

function show_attendees(event_id_) {
	event_id = event_id_;
	hs_dialog($('#attendees_dlg'), {
		outsideClickCloses: false,
		open: function () {
			rest_ajax_get_request([url_events, event_id, 'show_attendees'], function(html){
					$('#attendees').html(html);
					fb.resize();
				});
		},
		close: function () {
			$('#attendees').html('');
		},
	});
}

function newClientSuccess(person) {
	add_attendee(person, 'full');
}
