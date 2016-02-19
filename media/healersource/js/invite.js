function updateContactStatus(contact_id) {
	if($("#id_contact_"+contact_id).length>0) {
		$("#id_contact_"+contact_id).html('<span style="color: gray; font-style: italic;">Invitation Sent</span>');
	}
}

function inviteDialog(email, is_to_healer, contact_id) {
	$("input[name='emails']").val(email);

	var $dialogInvite = $("#invite_dialog");
	hs_dialog($dialogInvite, {
		title: (is_to_healer ? "Send Referral" : "Send Client Invitation"),
		title_class: (is_to_healer ? "nav_inbox" : "nav_clients"),
		open: function () {
			$('#simple_invite_form input').removeClass('error');
			$('#invite_error_list').html('');
			$('#invite_errors').removeClass('ui-helper-clearfix');
		},
		buttons:{
			Send:function () {
				var data = $('#simple_invite_form').serialize(true);

				if (is_to_healer)
					data += "&is_to_healer=1";

				if (typeof(contact_id) != 'undefined')
					data += "&contact_id=" + contact_id;

				rest_ajax_post_request_no_timeout(url_send_invite,
					function(response){
						function sendInviteSuccess(reload_page) {
							if (reload_page)
								window.location.reload();
						//	$("#invite_dialog").dialog("close");
							show_message_send_result($('#simple_invite_form'), $('#id_send_invitation_result_msg'), $("#invite_dialog"));
						//	updateContactStatus(contact_id);
						}

						$('#simple_invite_form input').removeClass('error');

						if (typeof response.errors == 'undefined') {
							$('#simple_invite_form').removeClass('ui-helper-clearfix');
							sendInviteSuccess(response.reload_page);
						} else {
							response.error_elements.forEach(function(error_element){
								$(error_element).addClass('error');
							});
							$('#invite_error_list').html(response.error_list);
							$('#invite_errors').addClass('ui-helper-clearfix');
						}
						$('img.captcha').attr('src', response.captcha.img)
						$('#id_msg_security_verification_0').val(response.captcha.code);
						$('#id_msg_security_verification_1').val('');
					}, {data: data});
			}
		}
	});
}

function sendFacebookInvite(contact_id, fb_contact_id, from_name, action) {
	var is_to_healer = true;
	if(typeof(action)==='undefined') {
		action = "add you as a Client";
		is_to_healer = false;
	}

	function openFacebookSendDialog(data) {
		function closeFacebookSendDialog(data) {
			if (typeof data.contact_id != 'undefined') {
				updateContactStatus(contact_id);
			} else {
				showError(data);
			}
			hs_dialog('close');
		}

		if (typeof data.confirmation_key !== 'undefined') {
			FB.ui({
					method:'send',
					name:'Click Here to Accept Your ' + (action == "add you as a Client" ? "Client Invitation" : "Referral" ),
					to:fb_contact_id,
					link: data.url,
					picture: 'https://www.healersource.com' + STATIC_URL + 'healersource/img/hs_logo.png',
					description: from_name + ' wants to ' + action + ' on HealerSource, the best place to find Wellness Practitioners online. '
				},
				function (response) {
					if (response) {
						rest_ajax_post_request_no_timeout(url_confirm_sent_join_invitation,
							closeFacebookSendDialog,
							{
								confirmation_key: confirmation_key,
								is_to_healer: is_to_healer
							});
					}
				}
			);
		} else {
			showError(data);
		}
	}

    FB.getLoginStatus(function (response) {
        if (response.status == "connected") {
			rest_ajax_post_request_no_timeout(url_create_join_invitation,
				openFacebookSendDialog,
				{
					contact_id: contact_id,
					key: fb_contact_id
				});
        } else {
            fbLogin();
        }
    });
}

function initNewClientDialog(title, hide_intake_field) {
	title = typeof title !== 'undefined' ? title : "New Client";
	hide_intake_field = typeof hide_intake_field !== 'undefined' ? hide_intake_field : false;

    var $dialogNewClient = $("#new_client_dialog");
    hs_dialog($dialogNewClient, {
        autoOpen: false,
        outsideClickCloses: false,
        title: title,
        title_class:'nav_clients',
        open: function () {
            clearForm($dialogNewClient);
            focus($('#id_first_name'));
            if (hide_intake_field) {
	            $dialogNewClient.find('#id_send_intake_form').parent().hide();
            }
        },
        buttons:{
            Save: function () {
				rest_ajax_post_request_long_timeout(url_new_client,
					function(response){
						$form = $('#new_user_form');
						$form.find('input').removeClass('error');
						if (typeof response.error_list == 'undefined') {
							$form.find('.form-errors').removeClass('ui-helper-clearfix').addClass('ui-helper-hidden');
							newClientSuccess(response.client);
                			fb.end();
						} else {
							$form.find('.form-errors').addClass('ui-helper-clearfix').removeClass('ui-helper-hidden');
							response.error_elements.forEach(function(error_element){
								$form.find('#id_' + error_element).addClass('error');
							});
							$form.find('.form_error_list').html(response.error_list);
							fb.resize();
						}
					}, {data: $('#new_user_form').serialize(true)});
            },
            Cancel: function(){
    			fb.end();
            }
        }
    });
}


function dlg_new_client() {
//	hs_dialog("close");
	hs_dialog("#new_client_dialog", "open");
}

function send_sh_to_friend(fb_contact_id){
	/* send_healing_url variable expected to be defined in template */
	FB.ui({
		method:'send',
		to: fb_contact_id,
		link: send_healing_url
	});
}

function send_link_through_fb(url) {
	FB.ui({
		method:'send',
		link:url
	});
}

function share_on_fb(url) {
	FB.ui({
		method: 'share',
		href: url
	});
}

function fb_app_request() {
	FB.ui({
		method: 'apprequests',
    	message: 'Join the The Healing Circle'
    });
}