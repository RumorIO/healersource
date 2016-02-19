var phonegap = true;
var access_token = localStorage.getItem('access_token');
var debug = JSON.parse(localStorage.getItem('is_admin'));
var hs_url = 'https://' + domain;
// var ONLINE_STATUS_INTERVAL = 5000;
var required_scopes = ['user_website', 'email', 'user_friends', 'user_location', 'user_photos'].sort();
var facebook_login_error = 'Error logging in with Facebook.';

$(function(){
	function apply_ajax_settings(){
		// required for endless pagination
		var ajax_settings = {complete: function(){
								phonegap_fix_urls();
							}};

		if (access_token) {
			ajax_settings['beforeSend'] = function (xhr) {
				xhr.setRequestHeader('Authorization', 'Bearer ' + access_token);
			}
			$('#logout').show();
		}
		$.ajaxSetup(ajax_settings);
	}

	function apply_ajax_settings(){
		// required for endless pagination
		var ajax_settings = {complete: function(){
								phonegap_fix_urls();
							}};

		if (access_token) {
			ajax_settings['beforeSend'] = function (xhr) {
				xhr.setRequestHeader('Authorization', 'Bearer ' + access_token);
			}
			$('#logout').show();
		}
		$.ajaxSetup(ajax_settings);
	}

	// function check_version(){
	// 	rest_ajax_get_request(hs_url + '/version/', function(server_version){
	// 		if (server_version[0] !== client_version[0] ||
	// 			server_version[1] !== client_version[1] ||
	// 			server_version[2] !== client_version[2]
	// 		) {
	// 			$('#update_required').show();
	// 		}
	// 	});
	// }

	// set_base_for_urls();

	// setInterval(check_online_status, ONLINE_STATUS_INTERVAL);
	$(':input[placeholder]').placeholder();

	apply_ajax_settings();

	// check_version();
	$('.menu-link').unbind('click'); // for menu
});

if (typeof String.prototype.startsWith != 'function') {
  String.prototype.startsWith = function (str){
	return this.slice(0, str.length) == str;
  };
}

function android_fix_to_open_external_urls_in_browser(){
	if (!is_android()) {return;}

	$('a[target="_blank"]').click(function(e){
		e.preventDefault();
		open_link_in_android(this.href);
	})
}

function phonegap_fix_urls(){
	function fix_images(){
		$('img').each(function(){
			var url = $(this).attr('src');
			if (url.startsWith('/')) {
				var new_url;
				if (typeof $(this).data('external') !== 'undefined' || url.startsWith('/site_media/media/avatars/')) {
					new_url = hs_url + url;
				} else {
					new_url = url.slice(1, url.length);
				}
				this.src = new_url;
			}
		});
	}

	// function fix_links(){
	// 	$('a[target="_blank"],a[data-fb-options]').each(function(){
	// 		var url = $(this).attr('href');
	// 		if (typeof url === 'undefined') { return; }
	// 		if (url.startsWith('/')) {
	// 			url = hs_url + url;
	// 		}
	// 		$(this).attr('href', url);
	// 	})
	// }

	fix_images();
	// fix_links();
	android_fix_to_open_external_urls_in_browser();
}

function logout(){
	localStorage.removeItem('access_token');
	localStorage.removeItem('is_healer');
	localStorage.removeItem('is_admin');
	home();
}

function home(reset_last_page){
	reset_last_page = typeof reset_last_page !== 'undefined' ? reset_last_page : true;

	if (reset_last_page) {
		localStorage.setItem(app_id + 'last_page', 'home');
	}
	window.location.href = 'index.html';
}

var back = home;

// function check_online_status(){
 // 	var $message = $('#offline_message');

	// if (navigator.onLine) {
	// 	if ($message.is(':visible')) {
	// 		fb.end();
	// 	}
	// } else {
	// 	if (!$message.is(':visible')) {
	// 		fb.end(true);
	// 		hs_dialog($message, {
	// 			outsideClickCloses: false,
	// 			showClose: false,
	// 		});
	// 	}
	// }
// }

function login(fb_token, reset_last_page, login, password, app2_url){
	function get_url(username){
		var authentication_type = 'oauth2';
		if (fb_token) {
			authentication_type += '_facebook';
		}
		return hs_url + '/' + authentication_type + '/access_token/';
	}

	fb_token = typeof fb_token !== 'undefined' ? fb_token : false;
	reset_last_page = typeof reset_last_page !== 'undefined' ? reset_last_page : false;
	login = typeof login !== 'undefined' ? login : false;
	password = typeof password !== 'undefined' ? password : false;
	app2_url = typeof app2_url !== 'undefined' ? app2_url : 'list.html';

	var username;
	var error;
	var password;
	if (fb_token) {
		// facebook login
		username = 'n/a';
		password = fb_token;
		error = facebook_login_error;
	} else {
		if (login) {
			username = login;
			password = password
		} else {
			username = $('#id_email').val();
			password = $('#id_password').val();
		}
		error = 'Email or Password is incorrect. Please try again.';
	}

	if (!username || !password) {return;}

	rest_ajax_post_request(get_url(username), function(result){
		access_token = result.access_token;
		localStorage.setItem('access_token', access_token);
		if (app_id == 1) {
			home(reset_last_page);
		} else {
			window.location.href = app2_url;
		}
	}, {
		client_id: phonegap_client_id,
		client_secret: phonegap_client_secret,
		grant_type: 'password',
		scope: 'read write',
		username: username,
		password: password,
	}, undefined, undefined, error);
}

function facebook_login(callback, form, skip_login) {
	callback = typeof callback !== 'undefined' ? callback : false;
	skip_login = typeof skip_login !== 'undefined' ? skip_login : false;

	function login_through_facebook(){
		facebookConnectPlugin.login(required_scopes, function(data){
				var token = data.authResponse.accessToken;
				if (callback) {
					callback(token, form);
					return;
				}
				if (!skip_login) {
					login(token);
				}
			}, function(error){
				showError(facebook_login_error + ' (' + error.errorMessage + ').');
			});
	}
	if (!window.cordova) {
		facebookConnectPlugin.browserInit(facebook_key);
	}
	// make sure user is logged out before logging in
	facebookConnectPlugin.logout(login_through_facebook, login_through_facebook);
}

// only for facebook signup thanks page
function fb_login_continue(){
	login(localStorage.getItem('facebook_token'), true);
}

function open_link_in_android(url){
	navigator.app.loadUrl(url, {openExternal: true});
}

function is_android(){
	if (typeof device === 'undefined') { return; } // needed for testing in browser
	return device.platform == 'Android';
}

function is_ios(){
	if (typeof device === 'undefined') { return; } // needed for testing in browserInit
	return device.platform == 'iOS';
}

function changeBackButton(new_function){
	back = new_function;
	if (!is_android()) { return; }
	document.removeEventListener('backbutton', back, false);
	document.addEventListener('backbutton', new_function, false);
}

var app = {
	// Application Constructor
	initialize: function() {
		this.bindEvents();
	},
	// Bind Event Listeners
	//
	// Bind any events that are required on startup. Common events are:
	// 'load', 'deviceready', 'offline', and 'online'.
	bindEvents: function() {
		document.addEventListener('deviceready', this.onDeviceReady, false);
	},
	// onOnline: function(){
	// 	online = true;
	// 	// if ($('#offline_message').is(':visible')) {
	// 	// 	fb.end();
	// 	// }
	// },
	// onOffline: function(){
	// 	online = false;
	// 	// var $message = $('#offline_message');
	// 	// if (!$message.is(':visible')) {
	// 	// 	fb.end(true);
	// 	// 	hs_dialog($message, {
	// 	// 		outsideClickCloses: false,
	// 	// 		showClose: false,
	// 	// 	});
	// 	// }
	// },

	onDeviceReady: function() {
		if (typeof on_device_ready !== 'undefined') {
			on_device_ready();
		}
		window.analytics.startTrackerWithId(google_analytics_id);
		window.analytics.trackView(page_name);

		if (is_android()) {
			document.addEventListener('menubutton', home, false);
			document.addEventListener('backbutton', back, false);
			$(function(){
				android_fix_to_open_external_urls_in_browser();
			});
		}

		// if(navigator.network.connection.type == Connection.NONE){
		// document.addEventListener('online', app.onOnline, false);
		// document.addEventListener('offline', app.onOffline, false);
		// app.receivedEvent('deviceready');

	},
};

app.initialize();
