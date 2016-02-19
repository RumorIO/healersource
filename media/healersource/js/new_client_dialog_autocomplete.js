$(function() {
	$('#new_user_form #id_first_name').autocomplete({
		source: url_autocomplete_contacts + '?contact_info=1',
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			$('#id_first_name').val(ui.item.first_name);
			$('#id_last_name').val(ui.item.last_name);
			$('#id_email').val(ui.item.email);
			$('#id_phone').val(ui.item.phone);
			return false;
		},
	});
});
