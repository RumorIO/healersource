function button_update(link, result, is_reset) {
	if (!result) {
		link.css('color', 'red');
		if (is_reset) {
			link.text('Reset Failed');
		} else {
			link.text('Sync Failed');
		}
	} else {
		link.css('color', 'green');
		if (is_reset) {
			link.text('Success!');
		} else {
			link.text('Success! - Sync Again');
		}

	}
	link.css('text-decoration', 'none');
}

function googleSync() {
	var link = $('#sync_button');
	if (link.text() != "Syncing...") {
		link.css('color', 'orange');
		link.css('text-decoration', 'blink');
		link.text('Syncing...');
 		rest_ajax_post_request_no_timeout(url_google_calendar_sync, function(result) {
			button_update(link, result.status);
			if ($('#debug').length !== 0) {
				$('#debug').html(result.data);
			}
		}, undefined, function(){
			button_update(link, false);
		});
	}
}

function googleReset(link, is_soft_reset) {
	if (confirm('All events on your google calendar will be deleted and recreated from scratch. Are you sure?')) {
		var link = $(link);
		var url;
		if (link.text() != "Resetting...") {
			link.css('color', 'orange');
			link.css('text-decoration', 'blink');
			link.text('Resetting...');
			if (link.data('soft-reset')) {
				url = url_google_calendar_soft_reset;
			} else {
				url = url_google_calendar_hard_reset;
			}
			rest_ajax_post_request_no_timeout(url, function(result) {
				if (result == 'Access Denied') {
					window.location.href = url_google_login;
				} else {
					button_update(link, result, true);
				}
			}, undefined, function(){
				button_update(link, false, true);
			});
		}
	}
}

function show_reset_links(){
	$('#reset_links').slideDown();
}
