var GAP_VALUE = 10;
var PHRASE_ROTATION_INTERVAL = 8;
var started_at, ended_at;
var settings_changed = false;
var person_type = '';
var person_id = '';
var is_image_loading = false;

var locations = [];
var favorites_exist = false;
var history_exists = false;
var skipped_exist = false;
var token = '';
var facebook_friends_exist = false;
var user_authenticated = false;
var user_has_avatar;
var sh_loading_in_progress = false;

var weeknames = {
	1: 'Monday',
	2: 'Tuesday',
	3: 'Wednesday',
	4: 'Thurday',
	5: 'Friday',
	6: 'Saturday',
	0: 'Sunday'
};

Function.prototype.scope = function(context) {
	var f = this;
	return function() {
		return f.apply(context, arguments);
	};
};

Timer = function() {
	this.tick_count = 0;
	this.glow_count = 0;
	this.glow_intervalId = null;
	this.tick_intervalId = null;
	this.period = 1000; // in ms
	this.glow_period = 21; // in ms
	this.isPaused = false;
};

var Phrase = {
	interval: 0,
	update: function (){
		function get_phrase(){
			var phrase = phrases[Math.floor(Math.random() * phrases.length)];
			if (phrase == $('#phrase_content').html()) {
				return get_phrase();
			}
			return phrase;
		}
		$('#phrase_content').fadeOut({
			duration: 1000,
			complete: function(){
				$('#phrase_content').html(get_phrase());
				$('#phrase_content').fadeIn(1000);
			}
		});
	},

	activate_rotation: function (){
		if (this.interval) {
			clearInterval(this.interval);
		}
		this.update();
		this.interval = setInterval(this.update, PHRASE_ROTATION_INTERVAL * 1000);
	},
	initiate_rotation: function(){
		if (!t.isPaused) {
			this.activate_rotation();
		}
	},
	toggle: function(){
		if (t.isPaused) {
			this.activate_rotation();
		} else {
			clearInterval(this.interval);
		}
	}
};

function enable_shadow() {
	$('#sh_img > img').css({'box-shadow': '0 0 20px 0px hsl(' + t.glow_count + ',42%,42%)'});
}

jQuery.extend(Timer.prototype, {

	onTick: function() {
		function update_timer_text(sec) {
			$("#timer").text(seconds_to_timer_text(sec));
		}

		if (!this.isPaused) {
			this.tick_count++;
			update_timer_text(this.tick_count);
		}
	},

	onGlow: function() {
		if (!this.isPaused && !is_image_loading) {
			this.glow_count++;
			enable_shadow();
		}
	},

	start: function() {
		this.glow_intervalId = setInterval(function() {this.onGlow();}.scope(this), this.glow_period);
		this.tick_intervalId = setInterval(function() {this.onTick();}.scope(this), this.period);
//		$('#sh_friends_buttons span').toggleClass('bold');
	},

	pause: function() {
		Phrase.toggle();
		this.isPaused = !this.isPaused;
//		$('#sh_friends_buttons span').toggleClass('bold');
	},

	stop: function() {
		clearInterval(this.glow_intervalId);
		clearInterval(this.tick_intervalId);

		var result = this.tick_count;
		this.tick_count = 0;
		this.isPaused = false;

		return result;
	}
});

function seconds_to_timer_text(sec) {
	var mins = parseInt(sec/60), seconds;
	seconds = sec % 60;

	if (seconds < 10)
		seconds = "0"+seconds;

	return mins+":"+seconds;
}

function arrange_healing_sent_history(new_item) {
	function name_from_timegap(gap, end) {
		if (gap == 0) {
			return 'Today';
		} else if (gap == 1) {
			return 'Yesterday';
		} else if (gap > 1 && gap < 7) {
			return weeknames[end.getDay()];
		} else{
			return $.datepicker.formatDate('MM d', end);
		}
	}

	var $blocks = $("#healing_sent_history .healing_history_block");
	var today = new Date();
	var d, day, month, year, gap, heading, $arranged_block;
	$blocks.each(function() {
		$block = $(this);
		day = $block.data("day");
		month = $block.data("month") - 1;
		year = $block.data("year");
		date = new Date(year, month, day);
		gap = parseInt((today - date) / (1000 * 60 * 60 * 24));

		title = name_from_timegap(gap, date);


		if (!$("#healing_sent_history_arranged [data-title='"+title+"']").length) {
			if(new_item) {
				$("#healing_sent_history_arranged").prepend(
						  "<div class='arranged_block' data-title='"+title+"'><div class='title'>"+title+"</div></div>");
				remove_last_block();

			} else {
				$("#healing_sent_history_arranged").append(
						  "<div class='arranged_block' data-title='"+title+"'><div class='title'>"+title+"</div></div>");
			}
		} else if(new_item) {
			remove_last_block();
		}
		$arranged_block = $("#healing_sent_history_arranged .arranged_block[data-title='"+title+"']");
		if(new_item){
			if($arranged_block.find(".healing_history_block").length){
				$block.insertBefore($arranged_block.find(".healing_history_block:first"));
			}else{
				$arranged_block.append($block);
			}
		}else{
			$arranged_block.append($block);
		}

	});
}

function remove_last_block() {
	if(!$(".endless_container").length) {
		return;
	}
	$last_block = $("#healing_sent_history_arranged .arranged_block").last();
	if($last_block.find(".healing_history_block").length <= 1){
		$last_block.remove();
	} else {
		$last_block.find(".healing_history_block").last().remove();
	}
}

function roll_photos_block(photos) {
	if (t.isPaused) {return;}
	if(photos.length > current_photo + 1) {
		current_photo = current_photo + 1;
	}else{
		current_photo = 0;
	}
	$("#sh_img img").attr("src", photos[current_photo].source);
}

var current_photo = 0, roll_photos_interval, roll_photos_timeout;
function roll_photos(photos, required_gap) {
	required_gap = required_gap || GAP_VALUE;
	gap = required_gap - t.tick_count % required_gap;
	if(roll_photos_timeout){
		clearTimeout(roll_photos_timeout);
	}
	if(roll_photos_interval){
		clearInterval(roll_photos_interval);
	}
	roll_photos_timeout = setTimeout(
			  function(){
				  roll_photos_block(photos);
				  roll_photos_interval = setInterval(function(){
					  roll_photos_block(photos);
				  }, required_gap * 1000);
			  }, gap * 1000);
}

function initialize_map() {
	var zoom = 2;
	var lat = 22.876;

	if (is_smallscreen()) {
		zoom = 0;
		lat = 25;
		$('#map').height(150);
	}

	var map = new google.maps.Map(document.getElementById('map'), {
		zoom: zoom,
		center: new google.maps.LatLng(lat, 0),
		disableDefaultUI: true,
		navigationControl: false,
		mapTypeControl: false,
		scaleControl: false,
		draggable: false,
		scrollwheel: false,
		mapTypeId: google.maps.MapTypeId.TERRAIN
	});

	var infowindow = new google.maps.InfoWindow();

	var marker, i;

	for (i = 0; i < locations.length; i++) {
		marker = new google.maps.Marker({
			position: new google.maps.LatLng(locations[i][0], locations[i][1]),
			map: map,
			clickable: false,
			icon: STATIC_URL + 'healersource/img/red-heart.png'
		});
	}
}

function image_loaded(){
	is_image_loading = false;
	enable_shadow();
}

function login_with_facebook(){
	if (phonegap) {
		facebook_login();
	} else {
		window.location = url_send_healing_facebook;
	}
}

function check_fb_perms(required_scopes, scopes_to_check, token) {
	function refresh_token(){
		//window.location = '/oauth/login/facebook?next=' + url_send_healing_facebook;
		login_with_facebook();
	}

	if(token) {
		FB.api("/me/permissions",
				  {
					  access_token: token
				  },
				  function(res) {
					  if (typeof res.data == 'undefined') {
					  	refresh_token();
					  }
					  var keys = Object.keys(res.data[0]);
					  keys.sort();
					  required_scopes.sort();
					  var accepted_scopes = true;
					  for(var i=0; i< scopes_to_check.length; i++){
						  if(keys.indexOf(scopes_to_check[i]) === -1){
							  accepted_scopes = false;
						  }
					  }
					  if(!accepted_scopes){
					  		refresh_token();
						}
				  });
	}
}

function sh_back(){
	$('.content_item,.back,#history').hide();
	$('#main,#send_healing_content').show();
}

function remove_status(element, url, status_name, show_or_hide_function) {
	var row = element.parent().parent();
	rest_ajax_post_request([url, element.data('id')], function(exist){
		if (status_name == 'favorite') {
			favorites_exist = exist;
		} else {
			skipped_exist = exist;
		}
		show_or_hide_function();
		row.remove();
	});
}

function remove_favorite(element){
	remove_status(element, url_remove_status_favorite, 'favorite', show_or_hide_favorites);
}

function unskip(element){
	remove_status(element, url_remove_status_skipped, 'skipped', show_or_hide_skipped_link);
}

function add_favorite(id, type){
	url = [url_add_favorite, type, id];
	rest_ajax_post_request(url, function(){
		$('#favorite_' + id).html('Favorite');
		favorites_exist = true;
		show_or_hide_favorites();
	});
}

function send_healing_to_person(id, type) {
	person_type = type;
	sh_back();
	show_next_random_person(true, true, id);
}

function switch_content(name){
	$('.back').show();
	if (name == 'history') {
		$('#history').show();
		$('#send_healing_content').hide();
	} else {
		$('.content_item').hide();
		$('#' + name).show();
		if (name == 'skipped') {
			rest_ajax_get_request(url_list_skipped, function(data){
				$('#skipped').html(data);
				$('.unskip').click(function(){
					unskip($(this));
				});
			});
		} else if (name == 'favorites') {
			rest_ajax_get_request(url_list_favorite, function(data){
				$('#favorites').html(data);
				$('.favorite').click(function(){
					remove_favorite($(this));
				});
			});
		}
	}
}

function activate_pause_button() {
	$("#pause").click(function() {
		var name;
		if ($("#pause").html() == 'Continue') {
			name = 'Pause';
		} else {
			name = 'Continue';
		}
		$("#pause").html(name);
		t.pause();
	});
}

function show_next_random_person(skip, initial_load, specific_id) {
	skip = typeof skip !== 'undefined' ? skip : false;
	initial_load = typeof initial_load !== 'undefined' ? initial_load : false;
	specific_id = typeof specific_id !== 'undefined' ? specific_id : false;

	function image_loading_started(){
		is_image_loading = true;
		$('#sh_img > img').css({'box-shadow': 'none'});
	}

	var send_healing_to_person_callback = function(res){
		if (skip && !initial_load) {
			skipped_exist = true;
			show_or_hide_skipped_link();
		}

		if (res.no_persons) {
			if (!initial_load) {
				$("#sh_info_container,#map,#fb_share_links_under_map").show();
				$('#history').hide();
				$('#sh_box').html('');
			} else {
				showError('There is no one to send healing to.');
			}
			return;
		}
		$("#sh_box").replaceWith(res.html);
		if (initial_load){
			$("#sh_info_container,#map,#fb_share_links_under_map").hide();
			$('#history').show();
			$("#friends_container").show();
			scrollTo($("#friends_container"));
		}
		if(!skip) {
			$("#healing_sent_history").append(res.healed.sent_to);
			arrange_healing_sent_history(true);
			history_exists = true;
			show_or_hide_history_link();
		}
		clearInterval(roll_photos_interval);

		if(res.person_type) {
			t.stop();
			t.start();
			started_at = new Date();
			current_photo = 0;
			get_fb_profile_photos(res.next_random_fb_uid, token, roll_photos);
			person_type = res.person_type;
			person_id = res.person_id;
		}
		activate_pause_button();
		Phrase.initiate_rotation();
	};

	image_loading_started();

	var data = {
		id: person_id,
		type: person_type,
		initial_load: initial_load
	};

	if (specific_id) {
		data.specific_id = specific_id;
	}

	if(!skip) {
		var duration = t.stop();
		ended_at = new Date();

		data.started_at = started_at.toUTCString();
		data.ended_at = ended_at.toUTCString();
		data.duration = duration;
	}

	sh_loading_in_progress = true;
	rest_ajax_post_request(url_send_healing_to_person, send_healing_to_person_callback, data, undefined, function(){
		sh_loading_in_progress = false;
	});
}

function process_checkboxes(element){
	var other_checkboxes = $('#send_to_ghp_members');
	if (element.is(':checked')) {
		other_checkboxes.prop('checked', false).prop('disabled', true);
	} else {
		other_checkboxes.prop('disabled', false);
	}
}

function show_or_hide_favorites() {
	var elements = $('.favorites_checkbox, #favorites_page_link');
	if (favorites_exist) {
		elements.show();
	} else {
		$('#send_to_my_favorites_only').prop('checked', false);
		elements.hide();
	}
	process_checkboxes($('#send_to_my_favorites_only'));
}

function show_or_hide_history_link() {
	var element = $('#history_page_link');
	if (history_exists) {
		element.show();
	} else {
		element.hide();
	}
}

function show_or_hide_skipped_link() {
	var element = $('#skipped_page_link');
	if (skipped_exist) {
		element.show();
	} else {
		element.hide();
	}
}

t = new Timer();

function start_SH(){
	facebook_authenticated = token !== '' && facebook_friends_exist;

	if (facebook_authenticated){
		$("#fb-root").bind("facebook:init", function() {
			check_fb_perms(
				required_scopes, scopes_to_check, token
			);
		});
	}

	arrange_healing_sent_history();

	$.endlessPaginate({
		paginateOnScroll: true,
		onCompleted: function() {
			arrange_healing_sent_history();
		}
	});

	activate_pause_button();

	$(document).on("click", "#timer_done.empty_link_form", function(e) {
		e.preventDefault();
		var duration = t.stop(), data;
		var ended_at = new Date();
		data = {
			'started_at': started_at.toUTCString(),
			'ended_at': ended_at.toUTCString(),
			'duration': duration
		};

		$("#timer_done")
				  .data("params", JSON.stringify(data))
				  .data("method", "POST")
				  .removeClass("empty_link_form")
				  .addClass("link_form")
				  .trigger("click");
	});

	$(document).on("click", "#timer_done", function(e) {
		show_next_random_person();
	});


	$(document).on("click", "#skip", function(e) {
		show_next_random_person(true);
	});

	$("#show_sh_page").click(function() {
		function launch_ghp(){
			function perform_checks(){
				// nothing is checked
				if ((!$('#send_to_ghp_members').is(':checked') &&
					!$('#send_to_my_favorites_only').is(':checked'))) {
					return false;
				}

				// if (!user_authenticated && $('#send_to_ghp_members').is(':checked')) {
				// 	login_redirect();
				// 	return false;
				// }

				if ($('#i_want_to_receive_healing').is(':checked') && !user_has_avatar) {
					if (phonegap) {
						showError('You need to add an avatar to receive healing.');
					} else {
						window.location.href = avatar_change_url;
					}
					return false;
				}
				return true;
			}
			if(!perform_checks()) {
				return;
			}
			show_next_random_person(true, true);
		}

		if (!settings_changed) {
			settings_changed = ($('#send_to_ghp_members').is(':checked') &&
				$('#i_want_to_receive_healing').is(':checked'));
		}
		if (settings_changed) {
			rest_ajax_post_request(url_save_settings, launch_ghp, {
				send_to_ghp_members: $('#send_to_ghp_members').is(':checked'),
				send_to_my_favorites_only: $('#send_to_my_favorites_only').is(':checked'),
				i_want_to_receive_healing: $('#i_want_to_receive_healing').is(':checked'),
			});
			return;
		}
		if (!sh_loading_in_progress) {
			launch_ghp();
		}
	});

	$('.send_healing_to_inputs input').click(function(){
		settings_changed = true;
	});

	$('#send_to_my_favorites_only').click(function(){
		process_checkboxes($(this));
	});

	show_or_hide_favorites();
	show_or_hide_history_link();
	show_or_hide_skipped_link();

	if (typeof send_to_user_on_load !== 'undefined') {
		send_healing_to_person(send_to_user_on_load, 'client');
	}

	if (localStorage.getItem('send_to_user_on_load')) {
		send_healing_to_person(localStorage.getItem('send_to_user_on_load'), 'client');
		localStorage.removeItem('send_to_user_on_load');
	}

}

function on_history_load(history){
	$('#history').html(history);
	$('.endless_more').click();
	start_SH();
}

function on_initial_data_load(data) {
	locations = data.locations;
	initialize_map();
	if (data.is_anonymous) {
		start_SH();
		return;
	}

	user_has_avatar = data.user_has_avatar;
	token = data.token;
	favorites_exist = data.favorites_exist;
	skipped_exist = data.skipped_exist;
	history_exists = data.history_exists;
	facebook_friends_exist = data.facebook_friends_exist;
	user_authenticated = true;
	$('#you_sent_panel, #you_received_panel').show();
	$('#healing_sent').html(data.healing_sent);
	$('#healing_received').html(data.healing_received);

	if(phonegap) {
		rest_ajax_get_request(url_history, on_history_load);
	}
}

function on_settings_load(settings) {
	for (var name in settings) {
		if (settings[name]) {
			$('#' + name).prop('checked', true);
		}
	}
}

function on_total_healing_sent_load(data){
	$('#healing_sent_total').html(data);
}

$(function() {
	$('.global_healing_panel').addClass('selected');
	if(phonegap) {
		rest_ajax_get_request(url_load_initial_data, on_initial_data_load, undefined, undefined, function(){
			rest_ajax_get_request(url_load_settings, on_settings_load);
			rest_ajax_get_request(url_total_healing_sent, on_total_healing_sent_load);
		});
	}
});
