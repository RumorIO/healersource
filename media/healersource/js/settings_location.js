$(function(){
	function activate_add_room_buttons() {
		$('.add_room').children('span').click(function(){
			$(this).hide();
			$(this).next().show();
			$(this).parent().addClass('grey_box');
			$(this).parent().find('input[name="name"]').focus();
		});
	}
	activate_add_room_buttons();
});

function add_location(setup, phonegap) {
	setup = typeof setup !== 'undefined' ? setup : false;
	var additional_form_is_visible = false;
	function save_form(){
		if (setup) {
			setup_save_and_next('{% url "provider_setup" 3 %}');
		}
		var $form = $('.location_settings')
		$form.submit();
	}

	var city = $('#id_city').val();
	var state = $('#id_state_province').val();
	var zipcode = $('#id_postal_code').val();

	if ( ((city != '') || (state != '')) && (zipcode == '') ) {
		alert('You must enter Postal or Zip Code.');
		return;
	}

	if (($('#id_title').val() == '') && additional_form_is_visible) {
		if ( ((city != '') && (state != '')) || (zipcode != '') ) {
			alert('You must enter Location Name.');
		} else {
			if (setup && !phonegap) {
				window.location.href = '{% url "provider_setup" 3 %}';
			}
		}

	} else if ( ((city != '') && (state != '')) || (zipcode != '') ) {
		if ($('#id_title').val() == '') {
			if (city && state) {
				$('#id_title').val(city + ', ' + state);
			} else {
				$('#id_title').val(zipcode);
			}
		}
		var $dialog_check_address = $("#dialog_check_address");
		hs_dialog($dialog_check_address, {
			autoOpen:true,
			title:"Check Your Address",
			title_class:'nav_tour',
			open:function () {
				var address = $('#id_address_line1').val() + ' ' +
						$('#id_address_line2').val() + ' ' +
						city + ' ' + state + ' ' + zipcode + ' ' +
						$('#id_country').val();

				var geocoder = new google.maps.Geocoder();
				geocoder.geocode( { 'address': address},
						function(data, textStatus){
							if (textStatus == 'OK') {
								var ll = data[0].geometry.location;
								initialize_gmap("map_canvas", ll.lat(), ll.lng(), $('#id_title').val());
							} else {
								alert('Could not load Google Map. Please try again or contact customer support.');
							}
						}
				);
			},
			buttons: {
				"Looks Good!": function (event) {
					var $target = $(event.target);

					if ($target.find('a').length == 0)
						$target = $target.parent();

					$target.html('Saving...');
					$target.unbind('click');

					save_form();
				},
				"&laquo; Try Again": {
					button_class: 'float_left',
					click: function () {
						hs_dialog("close");
					}
				}
			}
		});

	} else {
		save_form();
	}
}

additional_setting_action = function() {
	setTimeout(function(){
		if ($('#remote_sessions_on').hasClass('selected')) {
			window.location.href = url_remote_session_toggle_on;
		} else {
			window.location.href = url_remote_session_toggle_off;
		}
	}, 100);
}