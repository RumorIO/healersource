var send_disabled = false;
function setInviteType(type) {
	$('#id_invite_type').val(type);
	if(type=='provider')
		$('#invite_provider_recommend').show(500);
	else
		$('#invite_provider_recommend').hide(500);
}
function setInviteProviderRecommend(recommend) {
	$('#id_invite_provider_recommend').val(recommend);
}
function addEmail() {
	var email = $("#search_contacts").val().trim();
	if(email) {
		addItem('email_list', email, email)
	}
	$('#search_contacts').autocomplete('close');
}
function addItem(field, value, text, contact_email) {
	var input = $('<input type="hidden" name="' + field + '" value="' + value + '">');
	var elem = $('<li></li>').html(text);
	elem.append(' (').append($('<a href="#" onclick="removeItem(this)">x</a>')).append(')');
	elem.append(input);
	if(contact_email) {
		var input = $('<input type="hidden" name="contact_emails" value="' + contact_email + '">');
		elem.append(input);
	}

	$('#search_contacts_container #contacts_list').append(elem);
	$("#search_contacts").val('');
	showList();
}
function removeItem(elem) {
	$(elem).parent().remove();
	showList();
}
function showList() {
	if($('#search_contacts_container #contacts_list li').length) {
		$('#search_contacts_container #contacts_list').show();
		$('.contacts_error').hide();
	} else {
		$('#search_contacts_container #contacts_list').hide();
	}
}
function validate() {
	if(send_disabled) return false;
	if($('#search_contacts').val().trim()) {
		addEmail();
	}
	send_disabled = true;
	$('#invite_postcard_form_send').parent().parent().addClass('highlight_button_disabled');
	return true;
}
function send() {
	if(!validate()) return;
	$('#invite_postcard_form').submit();
}
function send_inline() {
	if(!validate()) return;
	$.ajax({
		type: "POST",
		url: $('#invite_postcard_form').attr('action'),
		data: $('#invite_postcard_form').serialize(),
		success: function(data) {
			$('.contacts_error').hide();
			$('#contacts_list li').remove();
			$('#id_emails').val('');
			if(data == 'error') {
				$('.contacts_error').show();
			} else {
				fb.start('{% url "empty_page" %}',
							{
								width:'710px',
								height:'450px',
								type: 'iframe',
								afterItemStart: function() {
									var iframe = $('iframe#fbContent').contents()[0];
									iframe.open();
									iframe.write(data);
									iframe.close();
								}
							});
			}
		}
	}).always(function() {
		send_disabled = false;
		$('#invite_postcard_form_send').parent().parent().removeClass('highlight_button_disabled');
	});
}
$(document).ready(function() {
	$("#search_contacts").val('');
	$("#search_contacts").keypress(function(e) {
		if(e.which == 13) {
			addEmail();
			e.preventDefault();
		}
	});

	var import_link = is_iphone ? '' : 'import_link=1';
//	var collision = is_iphone ? 'none' : 'flip';
	var limit = is_iphone ? 5 : 8;
	$("#search_contacts").autocomplete({
		source: url_autocomplete_contacts + "?show_term=1&with_providers=1&limit=" + limit + "&"+import_link,
		position: {collision: 'fit'},
		minLength: 2,
		html: true,
        autoFocus: true,
		select: function(event, ui) {
			if(ui.item.facebook_id) {
				sendFacebookInvite(ui.item.id, ui.item.facebook_id, fb_from_name, fb_action);
			} else if(ui.item.id) {
				if(ui.item.type == 'email') {
					addEmail();
				} else if(ui.item.type == 'provider') {
					addItem('providers',
								ui.item.id,
								ui.item.value ? ui.item.value : ui.item.email,
								ui.item.email);
				} else {
					addItem('contacts',
								ui.item.id,
								ui.item.value ? ui.item.value : ui.item.email,
								ui.item.email);
				}
			} else {
				fb.start(event.target.href);
			}

			return false;
		}
	});

	if($('#id_invite_type').val() == 'provider') {
		$('#invite_type span').first().removeClass('selected');
		$('#invite_type span').last().addClass('selected');
		$('#invite_provider_recommend').show();
	}

	if($('#id_invite_provider_recommend').val() == 'false') {
		$('#invite_provider_recommend span').first().addClass('selected');
		$('#invite_provider_recommend span').last().removeClass('selected');
	}

	$('#id_postcard_background').change(function() {
		$('.invite_postcard').css('background-image', 'url(\'' + postcard_background_url + $(this).val() + '\')')
	});

	$('.switch_form').click(function(e) {
		if($('#form_type').val() == 'autocomplete') {
			var emails = [];
			$('input[name=email_list], input[name=contact_emails]').each(function() {emails.push(this.value);});
			$('#id_emails').val(emails.join("\n"));
			$('#autocomplete_form').hide();
			$('#add_spreadsheet').hide();
			$('#bulk_invite_form').show();
			$('#form_type').val('bulk_invite');
		} else {
			$('#contacts_list li').remove();
			$.each($('#id_emails').val().split("\n").reverse(), function(index, value) {
				if(value.trim()) {
					addItem('email_list', value, value);
				}
			});
			$('#autocomplete_form').show();
			$('#bulk_invite_form').hide();
			$('#add_spreadsheet').show();
			$('#form_type').val('autocomplete');
			$('.switch_form').parent().removeClass('selected');
		}
		e.preventDefault();
	});

	if(set_invite_type_provider) {
		$('#invite_type span').first().removeClass('selected');
		$('#invite_type span').last().addClass('selected');
		$('#invite_provider_recommend').show();
		$('#id_invite_type').val('provider');
	}
});