$(function(){
	function show_notes_menu_if_user_is_healer(){
		if (JSON.parse(localStorage.getItem('is_healer'))) {
			$('#notes_button').show();
			return;
		}

		if (localStorage.getItem('is_healer') === null) {
			rest_ajax_get_request(hs_url + '/is_healer/', function(is_healer){
				localStorage.setItem('is_healer', is_healer);
				show_notes_menu_if_user_is_healer();
			});
		}
	}

	if (access_token) {
		show_notes_menu_if_user_is_healer();

		if (localStorage.getItem('is_admin') === null) {
			rest_ajax_get_request(hs_url + '/is_admin/', function(is_admin){
				localStorage.setItem('is_admin', is_admin);
			});
		}

		$('#login_buttons').hide();
	} else {
		$('#notes_button').show();
	}
});

function redirect_to_last_page(){
	var last_page = localStorage.getItem(app_id + 'last_page');
	if (last_page && last_page !== 'home') {
		window.location.href = last_page + '.html';
	}
}

redirect_to_last_page();
