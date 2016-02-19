function activate_room_select() {
	if (is_wellness_center) {
		$('#rooms_row').show();
		$('#location_select').change(function(){
			switch_location_tree();
		});
		switch_location_tree();
	}

	$('#treatment_edit_form').submit(function(event) {
		if (!$(this)[0].checkValidity()) {
			event.preventDefault();
		} else {
			select_checked_rooms();
		}
	});
	var isSafari = /constructor/i.test(window.HTMLElement);
	if (isSafari) {
		$('#treatment_edit_form').each(createAllErrors);
	}
}

function select_checked_rooms(){
	var selected_rooms = [];
	$('.room_select:checked').each(function(){
		selected_rooms.push($(this).val());
	});
	$('#id_rooms').children().each(function(){
		var element = $(this);
		if ($.inArray(element.val(), selected_rooms) !== -1) {
			element.attr('selected', 'selected');
		} else {
			element.removeAttr('selected');
		}
	});
}

function switch_location_tree(){
	if ($('input[name="location_select"]:checked').val() == 'any') {
		$('.room_select').each(function(){
			$(this).removeAttr('checked');
		});
		$('.room_select_location').hide();
	} else {
		$('.room_select_location').show();
	}
}

var createAllErrors = function() {
    var form = $( this ),
        errorList = $( "ul.errorMessages", form );

    var showAllErrorMessages = function() {
        errorList.empty();

        // Find all invalid fields within the form.
        var invalidFields = form.find( ":invalid" ).each( function( index, node ) {

            // Find the field's corresponding label
            var label = $( "label[for=" + node.id + "] "),
                // Opera incorrectly does not fill the validationMessage property.
                message = node.validationMessage || 'Invalid value.';

            errorList
                .show()
                .append( "<li><span>" + label.html() + "</span> " + message + "</li>" );
        });
    };

    // Support Safari
    form.on( "submit", function( event ) {
        if ( this.checkValidity && !this.checkValidity() ) {
            $( this ).find( ":invalid" ).first().focus();
            event.preventDefault();
        }
    });

    $( "input[type=submit], button:not([type=button])", form )
        .on( "click", showAllErrorMessages);

    $( "input", form ).on( "keypress", function( event ) {
        var type = $( this ).attr( "type" );
        if ( /date|email|month|number|search|tel|text|time|url|week/.test ( type ) && event.keyCode == 13 ) {
            showAllErrorMessages();
        }
    });
};

$(function () {
	activate_room_select();
});
