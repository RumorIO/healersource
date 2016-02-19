var email;
var facebook_token = false;
var facebook_login_in_process = false;

function passwordValidate(data, form) {
	var fields = ['id_password1'];
	var $form = $(form);
	$form.find('.signup_error').remove();

	$.each(data.errors, function(key, val) {
		if($.inArray(key, fields) != -1) {
			if($('#' + key, $form).val()) {
				$('#' + key, $form).after('<p id="error_1_' + key + '" class="signup_error">' + val + '</p>');
			}
		}
	});
}

function switch_signup_type(type){
	if (type == 'client') {
		var form = $('.signup_client');
		var button = $('.client_signup_button');
		var container = $('.client_signup_form');
	} else if (type == 'healer') {
		var form = $('.signup_provider');
		var button = $('.provider_signup_button');
		var container = $('.healer_signup_form');
	} else if (type == 'wellness_center') {
		var form = $('.signup_wcenter');
		var button = $('.wcenter_signup_button');
		var container = $('.wcenter_signup_form');
	}

	set_first_name_placeholder(form);
	$('.signup_type_selection_button').removeClass('single_button');
	button.addClass('single_button');

	if (FacebookSignup) {
		form.submit();
		return;
	}

	$('.signup_form_main').hide();
	container.fadeIn(500);
	$("input[name=first_name]").focus();

	form.validate(url_signup_client_validate, {
		type: 'table',
		fields: ['password1'],
		dom: form.find('input[name=password1]'),
		event: 'change',
		callback: passwordValidate
	});
}

function enable_ambassador_signup () {
	$('.signup_type_selection_button').removeClass('single_button');
	$('.ambassador_signup_button').addClass('single_button');
	$('.signup_form_main').hide();

	$('#is_ambassador').val('1');
	open_signup_selection_dlg('Create Your Ambassador Account', 'Select Your Ambassador Account Type', false);
}

function set_first_name_placeholder(form){
	type = form.find('input[name="type"]').val();
	if (type == 'wellness_center') {
		placeholder = 'Spa or Center Name';
	} else {
		placeholder = 'Full Name';
	}
	form.find('input[name="first_name"]').attr('placeholder', placeholder);
}

function facebook_login_callback(token, $form) {
	facebook_token = token;
	facebook_login_in_process = false;
	$form.submit();
}

// Signup dialog ------------------------
function open_signup_dlg(type){
	var form = $('#signup_form')
	$('#signup_type').val(type);
	set_first_name_placeholder(form);
	hs_dialog('close');

	if (FacebookSignup) {
		form.submit();
		return;
	}

	hs_dialog($('#signup_dlg'), {
		fixed_width: 420,
		title: signup_dialog_title,
		title_class: 'nav_schwing',
		buttons: {
			'Signup &raquo;': function(){
				form.submit();
			}
		}
	});
}

function open_signup_selection_dlg(new_signup_dialog_title, signup_selection_dialog_title, hide_client){
	hide_client = typeof hide_client !== 'undefined' ? hide_client : true;
	signup_selection_dialog_title = typeof signup_selection_dialog_title !== 'undefined' ? signup_selection_dialog_title : 'Select your Account Type';

	if (hide_client) {
		$('.client_signup_button').hide();
	}
	if (typeof new_signup_dialog_title !== 'undefined') {
		signup_dialog_title = new_signup_dialog_title;
	}

	hs_dialog($('#signup_selection_dlg'), {
		title: signup_selection_dialog_title,
		title_class: 'nav_schwing',
	});
}

var signup_dialog_title = 'Create Your Free Profile Today';

// -----------------------------

$(function() {
	function activate_scrolling_to_signup_form(){
		if (!FacebookSignup) {
			$('.signup_type_selection_button').click(function(){
				scrollTo($('.signup_form:visible'));
			});
		}
	}

	function enable_ajax_signup(){
		function get_url(){
			if (FacebookSignup) {
				return url_facebook_signup;
			} else {
				return url_ajax_signup;
			}
		}

		function success($form, response){
			var type = $form.find('input[name="type"]').val();
			if (FacebookSignup) {
				facebook_signup_success(response, type);
			} else {
				signup_success($form, response);
			}
		}

		function signup_success($form, response){
			if (response.redirect_url) {
				if (phonegap) {
					window.location.href = 'login.html';
				} else {
					window.location.href = response.redirect_url;
				}
			} else if (response.message) {
				$form.addClass('ui-helper-hidden');
				$('#signup_panel').hide().after(response.message);
			} else if (response.url) {
				localStorage.setItem('email', response.email);
				window.location.href = response.url;
			}
		}

		function facebook_signup_success(response, type){
			if (response.error) {
				showError(response.error);
			} else {
				if (phonegap) {
					if (app_id == 2) {
						login(facebook_token, undefined, undefined, undefined, 'provider_choice.html');
						return;
					}
					localStorage.setItem('facebook_token', facebook_token);
					window.location.href = 'signup_fb_thanks_' + type + '.html';
				} else {
					window.location.href = response.url;
				}
			}
		}

		$('.signup_form').on('submit', function(event) {
			event.preventDefault();

			if (facebook_login_in_process) {
				return;
			}

			form = $(this);

			if (FacebookSignup && !facebook_token) {
				facebook_login_in_process = true;
				facebook_login(facebook_login_callback, form);
				return;
			}

			var data = {is_phonegap: phonegap,
				data: form.serialize()};
			if (FacebookSignup) {
				data.token = facebook_token;
			}

			rest_ajax_post_request_no_timeout(get_url(),
				function(response){
					ajax_process_form_response(response, form, function(){
						success(form, response);
					})
				}, data, undefined, function(){
					fb.resize();
				});
		});
	}

	$('input[name=username],input[name=password1]').keyup(function() {
		$(this).closest("form").find(".signup_error").remove();
	});

	activate_scrolling_to_signup_form();
	enable_ajax_signup();
	$('#signup_form').find('input[name="first_name"]').attr('placeholder', 'Spa or Center Name');
	if (intake_form) {
		switch_signup_type('client');
	}
});


