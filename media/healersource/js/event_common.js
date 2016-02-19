var event_id;

function add_attendee(person, type){
	var person_id = person.id;
	if (person_id) {
		var person_type = person.type;
		rest_ajax_post_request([url_events, event_id, 'attendee', 'add', person_type, person_id],
			function(html){
				$('#attendees').append(html);
				$('#add_attendee').val('');
				fb.resize();
			}, undefined, function(){
				$('#add_attendee').val('');
			});
	}
}

function initAttendeeAutocomplete(type) {
	$('#add_attendee').autocomplete({
		source: url_autocomplete_attendees,
		minLength: 2,
		html: true,
        autoFocus: true,
		select: function(event, ui) {
			add_attendee(ui.item, type);
		}
	});
}

function remove_attendee(event_id, attendee_id){
	rest_ajax_post_request([url_events, event_id, 'attendee', 'remove', attendee_id],
		function(){
			$('#attendee_' + attendee_id).remove();
		});
}
