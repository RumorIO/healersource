var url_get_circle_list = '{% url 'get_circle_list_ajax' %}';
var url_get_received_healing_list = '{% url 'get_received_healing_list' %}';
var url_facebook_associate_user_ajax = '{% url 'facebook_associate_user_ajax' %}';

function load_list(mode, page){
	page = typeof page !== 'undefined' ? page : 1;
	if (mode == 'received') {
		rest_ajax_get_request_long_timeout(url_get_received_healing_list, function(response) {
			$('#list').append(response);
		});
	} else {
		rest_ajax_get_request_long_timeout(url_get_circle_list, function(response) {
			$('#list').append(response);
		}, {page: page, mode: mode});
	}
}

function enable_mode(mode, element) {
	$('.links').children().removeClass('active');
	$('#list').empty();
	if (mode == 'facebook') {
		$('#facebook').show();
	} else {
		$('#facebook').hide();
	}
	if (element) {
		$(element).addClass('active');
	}
	if (!localStorage.getItem('access_token') && (mode == 'facebook' || mode == 'favorites' || mode == 'received')) {
		return;
	}
	load_list(mode);
}

function send_healing_to(client_id) {
	localStorage.setItem('send_to_user_on_load', client_id);
	document.location.href = 'ghp.html';
}

function facebook_associate_login(){
	facebook_login(facebook_associate_user, undefined, true);
}

function facebook_associate_user(token) {
	rest_ajax_post_request_long_timeout(url_facebook_associate_user_ajax, function(response) {
		if (response.error) {
			showError(response.error);
		} else {
			enable_mode('facebook');
		}
	}, {token: token});
}

function facebook_invite(){
    facebookConnectPlugin.showDialog(
        {method: 'send', link: 'https://www.healersource.com'},
        function(){},
        function(error){
            if(error === 'Messaging unavailable.') {
                alert('Please, install Facebook Messanger to send an invitation.')
            } else {
                alert(error);
            }
        });
}

load_list('all');
$(window).scroll(function(){
	if ($(window).scrollTop() > $(document).height() - 2 * $(window).height()) {
		$('#list').find('a.next').click();
	}
});
