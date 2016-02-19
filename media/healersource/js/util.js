var top_menu = null;
var left_menu = null;
var modality_menu = null;
var menu_timeouts = {};
var phonegap = false;
var debug = false;
var ajax_requests_in_progress = [];

/* Buttons */
function activate_container_buttons(){
	$('.highlight_container span, .highlight_button').click(clickContained);
	$('.highlight_container span').click(highlightButton);
}

function activate_contact_buttons(){
	$('.contact').each(function() {
		var addr = 'support' + '@' + 'healersource' + '.' + 'com';
		var a = $(this).get(0);
		a.href = 'mailto:' + addr + '?subject=Contact%20Healersource';
		if (!$(this).html()) {
			$(this).html(addr);
		}
	});
}

function clickContained(e) {
	if (e.target.tagName.toLowerCase() == 'span') {
		var a = $(this).find('a');
		if (a.length != 0)
			a.click();

		var href = a.attr('href');
		if (href && href != '#')
			window.location.href = href;
	}
}

function highlightButton(e) {
	var span = $(this);
	if (!span.parent()) return;

	span.parent().find('span').each(function(i) {
		$(this).removeClass('selected');
	});

	span.addClass('selected');
}

/* Menu */
function setMenuTimeout(menu){
	menu_timeouts[menu] = setTimeout(function(){
		if (!$('#select2-drop-mask').is(':visible') && !$('.ui-autocomplete').is(':visible')) {
			$('#' + menu).hide();
		}
	}, 100);
}

function adjustMenu() {
	if (!left_menu || !top_menu)
		return;

	var menu = $('#left_menu, #modality_menu, #top_menu');
	if (is_smallscreen()) {
		if(menu.hasClass('mobile_nav')) return;

		left_menu.disable();
		top_menu.disable();
		if(modality_menu) modality_menu.disable();
		menu.addClass('mobile_nav');
		$('#left_menu ul, #modality_menu ul, #top_menu ul').removeAttr('style');
		// if "more" link not in DOM, add it
		if (!$(".more", menu)[0]) {
			$('<div class="more">&nbsp;</div>').insertBefore($('.parent'));
		} else {
			$('.more', menu).show();
		}
		$(".mobile_nav li a.parent").unbind('click');
		$(".mobile_nav li .more").unbind('click').bind('click', function() {
			$(this).parent("li").toggleClass("hover");
		});
	} else {
		if(!menu.hasClass('mobile_nav')) return;

		menu.removeClass('mobile_nav');
		left_menu = initSubmenu('left_menu');
		top_menu = initSubmenu('top_menu');
		if(modality_menu) modality_menu = initSubmenu('modality_menu');
		$('.more', menu).hide();
	}
}

function select_current_menu_item($menu_items) {
	function getElementToSelect($element){
		var $potential_menu = $element.parent().parent().parent();
		if ($potential_menu.hasClass('submenu')){
			return $potential_menu.prev();
		} else {
			return $element.parent();
		}

	}

	$menu_items.each(function () {
		if(this.href == current_page) {
			getElementToSelect($(this)).addClass('selected');
		}
	});
}

function initSubmenu(id) {
	if($('#'+id).length == 0)
		return null;

	else
		return new TINY.dropdown.init(id, {
			id: id,
			fade:true,
			slide:true,
			speed:3,
			active:'menuhover',
			timeout:0
		});
}

function activate_selection_menus(){
	$('.menu_selection').each(function(){
		var id = $(this).attr('id');
		eval(id + ' = initSubmenu("' + id + '")');
		eval(id + '.show(0,0)');
	});
}

$(function() {
	// function set_base_for_urls(){
	// 	var pattern = /^url_/;
	// 	for (var varName in window) {
	// 		if (pattern.test(varName)) {
	// 			window[varName] = hs_url + window[varName];
	// 		}
	// 	}
	// }

	if ($.browser.msie  && parseInt($.browser.version) < 8) {
		if(window.location.href.indexOf("bad_browser") == -1)
			window.location.href = "/bad_browser/";
	}

	if(!window.getComputedStyle) {
		window.getComputedStyle = function(el, pseudo) {
			this.el = el;
			this.getPropertyValue = function(prop) {
				var re = /(\-([a-z]){1})/g;
				if (prop == 'float') prop = 'styleFloat';
				if (re.test(prop)) {
					prop = prop.replace(re, function () {
						return arguments[2].toUpperCase();
					});
				}
				return el.currentStyle[prop] ? el.currentStyle[prop] : null;
			};
			return this;
		};
	}
	activate_contact_buttons();
	activate_container_buttons();

	left_menu = initSubmenu('left_menu');
	top_menu = initSubmenu('top_menu');

	$('body').addClass('js');
	var $menu = $('#menu'),
			  $menulink = $('.menu-link');

	$menulink.click(function() {
		$menulink.toggleClass('active');
		$menu.toggleClass('active');
		$my_account_link.removeClass('active');
		$my_account_menu.removeClass('active');
		return false;
	});

	var $my_account_menu = $('.my_account_menu'),
			  $my_account_link = $('.my_account_button');

	$my_account_link.click(function() {
		$my_account_link.toggleClass('active');
		$my_account_menu.toggleClass('active');
		$menulink.removeClass('active');
		$menu.removeClass('active');
		return false;
	});

	$('#menu a, .my_account_menu a, .login_button').click(function() {
		$my_account_link.removeClass('active');
		$my_account_menu.removeClass('active');
		$menulink.removeClass('active');
		$menu.removeClass('active');
	});

	$("#left_menu li a, #modality_menu li a, #top_menu li a").each(function() {
		if ($(this).next('ul').length > 0) {
			$(this).addClass("parent");
		}
	});
	adjustMenu();

	$(window).bind('resize orientationchange', function() {
		adjustMenu();
	});

	fbClassOptions = {
		fbTooltip: 'measureHTML:yes width:0 height:0 doAnimations:false fadeTime:0'
	};

	fbPageOptions = {
		afterBoxStart: fbAfterBoxStart,
		afterBoxEnd: fbAfterBoxEnd
	};

	function updateFbPageOptions() {
		if(is_smallscreen()) {
			if(!fbPageOptions['measureHTML']) {
				fbPageOptions = {
					afterBoxStart: fbAfterBoxStart,
					afterBoxEnd: fbAfterBoxEnd,
					width: '100%',
					height: '100%',
					measureHTML: 'no',
					showOuterClose: 'false',
					showClose: 'true'
				};
			}
		} else {
			if(fbPageOptions['measureHTML']) {
				fbPageOptions = {
					afterBoxStart: fbAfterBoxStart,
					afterBoxEnd: fbAfterBoxEnd
				};
			}
		}
	}

	updateFbPageOptions();
	$(window).resize(updateFbPageOptions);

	$('#edit_location').find('#id_city').autocomplete({
		source: url_autocomplete_city,
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			event.preventDefault();
			var search_form = $('.location_settings');
			$('#id_city', search_form).val(ui.item.city);
			$('#id_state_province', search_form).val(ui.item.state);
			$('#id_postal_code', search_form).val(ui.item.zipcode);
			$('#id_country', search_form).val('USA');
		}
	});

	$(document).on('click', ".remove-limit-height", function(){
		$closest = $(this).closest('.healing_request');
		$target = $closest.find("."+$(this).data("target-class"));
		$target.removeClass("limit-height");
		$(this).removeClass("remove-limit-height").addClass("add-limit-height").html("Read less &raquo;");
	});

	$(document).on('click', ".add-limit-height", function(){
		$closest = $(this).closest('.healing_request');
		$target = $closest.find("."+$(this).data("target-class"));
		$target.addClass("limit-height");
		$(this).removeClass("add-limit-height").addClass("remove-limit-height").html("Read more &raquo;");

	});

	$(document).on("click", "a.link_form", function(e){
		if($(this).hasClass("empty_link_form"))
			return;

		e.preventDefault();
		var remote=$(this).data("remote"),
				  method=$(this).data("method") || "GET",
				  url=$(this).attr("href"),
				  confirm_text=$(this).data("confirm");

		if(confirm_text){
			res = confirm(confirm_text);
			if(!res){
				return;
			}
		}

		method = method.toUpperCase();

		if(method != "POST" && method != "PUT" && method != "PATCH")
			method = "GET";

		if(!remote || remote != "true"){
			var params = $(this).data("params");
			var $common_form = $("#common-form");
			if(typeof(params) != "undefined"){
				if(params.trim().length > 1){
					params = JSON.parse(params);
					for(var key in params){
						$common_form.append("<input type='hidden' name='"+key+"' value='"+params[key]+"'  />");
					}
				}
			}
			$common_form.attr("action", url);
			$common_form.attr("method", method);
			$common_form.submit();
		}
	});

	$(document).keyup(function(e) {
		if ( (e.keyCode == 27) && (typeof(fb) != 'undefined') )
			fb.end();
	});

	function activateMenus(){
		function activateMenu(menu_item_name, submenu_element_name, first_row){
			first_row = typeof first_row !== 'undefined' ? first_row : false;
			var menu_item = $('#' + menu_item_name);
			var submenu_element = $('#' + submenu_element_name);

			menu_item.mouseenter(function(){
				submenu_element.css('left', $(this).position().left);
				if (first_row) {
					submenu_element.css('top', $(this).position().top + $(this).height());
				}
				window.clearTimeout(menu_timeouts[submenu_element_name]);
				submenu_element.show();
			}).mouseleave(function(){
				setMenuTimeout(submenu_element_name);
			});
			submenu_element.mouseenter(function(){
				window.clearTimeout(menu_timeouts[submenu_element_name]);
			}).mouseleave(function(){
				setMenuTimeout(submenu_element_name);
			});
		}

		activateMenu('menu_item_me', 'additional_nav_menu');
		if (typeof no_find_popup == 'undefined') {
			activateMenu('menu_item_find', 'find_healer_menu', true);
		}
	}

	if (!is_mobile()) {
		activateMenus();
	}

	// if (phonegap) {
	// 	set_base_for_urls();
	// }

	initProviderSearchAutocomplete();
	initCitySearchAutocomplete();
}); // document.ready

/* ajax */
function dajaxProcess(response) {
	if (response.length && response[0].cmd) {
		Dajax.process(response);
		return true;
	}
	return false;
}

function ajax_request(dajaxice_function, callback, data, error, error_callback, timeout, loading_element_name) {
	timeout = typeof timeout !== 'undefined' ? timeout : 5000;
	loading_element_name = typeof loading_element_name !== 'undefined' ? loading_element_name : 'loading';
	var loading_element = $('#' + loading_element_name);
	loading_element.show();
	var timeout_id = setTimeout(function(){
		loading_element.hide();
		showError('Response timeout has expired');
	}, timeout);
	dajaxice_function(function() {
				  clearTimeout(timeout_id);
				  loading_element.hide();
				  callback.apply(this, arguments);
			  }, data,
			  {'error_callback': function(){
				  loading_element.hide();
				  clearTimeout(timeout_id);
				  showError(error);
				  if (typeof error_callback !== 'undefined') {
					  error_callback();
				  }
			  }});
}

function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function removeElementFromArray(array, element) {
	var index = array.indexOf(element);
	if (index !== -1){
		array.splice(index, 1);
	}
}

function rest_ajax_request(url, callback, data, type, error_callback, complete_callback, error_text, loading_element_name, timeout) {
	function rest_url(url_components){
		var clean_url_components = [];
		url_components.forEach(function(url_component){
			var component = url_component.toString();
			if (component.substring(component.length - 1, component.length) == '/') {
				component = component.substring(0, component.length - 1);
			}
			clean_url_components.push(component);
		});

		return clean_url_components.join('/') + '/';
	}

	function check_domain() {
		if(phonegap && hs_url && url.indexOf('http') !== 0) {
			url = hs_url + url;
		}
	}

	function before_complete(){
		if (timeout !== 0) {
			clearTimeout(timeout_id);
		}
		loading_element.hide();
	}

	error_text = typeof error_text !== 'undefined' ? error_text : '<p>Something\'s gone wrong and we\'re terribly sorry.. Please give one more try.</p><p>If it still doesn\'t work, please <a href="' + url_error_report + '" style="text-decoration: underline;">Let Us Know</a> about it so we can fix the problem ASAP.</p><p>Thanks!</p><p class="italic">The HealerSource Team</p>';
	complete_callback = typeof complete_callback !== 'undefined' ? complete_callback : function(){};
	loading_element_name = typeof loading_element_name !== 'undefined' ? loading_element_name : 'loading';
	timeout = typeof timeout !== 'undefined' ? timeout : 5000;

	if (phonegap && typeof navigator.connection !== 'undefined' && navigator.connection.type == Connection.NONE) {
		var $message = $('#offline_message');
		if (!$message.is(':visible')) {
			fb.end(true);
			hs_dialog($message, {
				outsideClickCloses: false,
			});
		}
		return;
	}

	if (typeof url == 'object') {
		url = rest_url(url);
	}

	check_domain();

	if (ajax_requests_in_progress.indexOf(url) !== -1) {
		return;
	}
	ajax_requests_in_progress.push(url);

	var loading_element = $('#' + loading_element_name);
	loading_element.show();

	if (timeout !== 0) {
		var timeout_id = setTimeout(function(){
			loading_element.hide();
			showError('Response timeout has expired.');
		}, timeout);
	}
	var ajax_settings = {
		type: type,
		url: url
	};

	ajax_settings['beforeSend'] = function(xhr, settings) {
		if (!csrfSafeMethod(settings.type)) {
			xhr.setRequestHeader('X-CSRFToken', localStorage.getItem('csrftoken'));
		}
		if (phonegap && access_token) {
			xhr.setRequestHeader('Authorization', 'Bearer ' + access_token);
		}
	}

	if (typeof data !== 'undefined') {
		ajax_settings.data = data;
	}

	$.ajax(ajax_settings).success(function(response){
		before_complete();
		if (response.ajax_error) {
			showError(response.ajax_error, error_callback);
		} else {
			callback.apply(this, arguments);
		}
	}).error(function(xhr, status, error){
		if (debug) {
			alert(JSON.stringify({status: xhr.status, response: xhr.responseText, error: error}));
		}
		before_complete();
		if (xhr.responseText) {
			try {
				detail = JSON.parse(xhr.responseText).detail;
				if (detail == 'Authentication credentials were not provided.' || detail == 'Invalid token') {
					if (phonegap) {
						logout();
						home();
					} else {
						// window.location.href = '/login';
					}
				}
			}
			catch(e){
				console.log(xhr.responseText);
			}
		}
		showError(error_text, error_callback);
	}).complete(function(){
		removeElementFromArray(ajax_requests_in_progress, url)
		complete_callback();
		if (phonegap) {
			phonegap_fix_urls();
		}
	});
}

function rest_ajax_post_request(url, callback, data, error_callback, complete_callback, error_text, loading_element_name) {
	rest_ajax_request(url, callback, data, 'post', error_callback, complete_callback, error_text, loading_element_name);
}

function rest_ajax_get_request(url, callback, data, error_callback, complete_callback, error_text, loading_element_name) {
	rest_ajax_request(url, callback, data, 'get', error_callback, complete_callback, error_text, loading_element_name);
}

function rest_ajax_post_request_long_timeout(url, callback, data, error_callback, complete_callback, error_text, loading_element_name) {
	rest_ajax_request(url, callback, data, 'post', error_callback, complete_callback, error_text, loading_element_name, 60000);
}

function rest_ajax_get_request_long_timeout(url, callback, data, error_callback, complete_callback, error_text, loading_element_name) {
	rest_ajax_request(url, callback, data, 'get', error_callback, complete_callback, error_text, loading_element_name, 60000);
}

function rest_ajax_post_request_no_timeout(url, callback, data, error_callback, complete_callback, error_text, loading_element_name) {
	rest_ajax_request(url, callback, data, 'post', error_callback, complete_callback, error_text, loading_element_name, 0);
}

function rest_ajax_get_request_no_timeout(url, callback, data, error_callback, complete_callback, error_text, loading_element_name) {
	rest_ajax_request(url, callback, data, 'get', error_callback, complete_callback, error_text, loading_element_name, 0);
}

function ajax_process_form_response(response, form, success, update_captcha){
	update_captcha = typeof update_captcha !== 'undefined' ? update_captcha : false;

	form.find('input,textarea').removeClass('error');
	if (typeof response.errors == 'undefined' || response.errors == '') {
		success();
	} else {
		response.error_elements.forEach(function(error_element){
			form.find('#id_' + error_element).addClass('error');
		});
		form.find('.form-errors').html(response.errors);
		form.find('.form-errors').removeClass('ui-helper-hidden');
		if (update_captcha) {
			$('img.captcha').attr('src', response.captcha.img)
			$('#id_msg_security_verification_0').val(response.captcha.code);
			$('#id_msg_security_verification_1').val('');
		}
	}
}

/* dialogs */
function fbAfterBoxStart() {
	if(is_smallscreen()) {
		$('.fbContentWrapper').css('overflow', 'scroll');
		if(fb.instances.length == 1) {
			$('body').height($(window).height());
			$('html, body').css('overflow', 'hidden');
		}
	}
	if (phonegap) {
		phonegap_fix_urls();
	}
}

function fbAfterBoxEnd() {
	if(is_smallscreen() && !fb.instances.length) {
		$('body').height('auto');
		$('html, body').css('overflow', 'visible');
	}
}

function isNull(val) { return ((typeof(val) == 'undefined') || (val == null)); }

function closeDialog(dialog) {
	if(isNull(dialog))
		return;

	hs_dialog("close");
}

function showResult (result, title, callback, title_class, button_name) {
	title_class = typeof title_class !== 'undefined' ? title_class : 'nav_info';
	button_name = typeof button_name !== 'undefined' ? button_name : 'Ok';
	if(result == "" || (typeof result == 'undefined')) return;

	var $dialog_result = $("#dlg_result");
	var $dialog_result_content = $("#dialog_result_content");
	if (!$dialog_result.length) {
		$dialog_result = $("<div></div>")
				  .attr('id', 'dlg_result')
				  .hide()
				  .appendTo($('body'));

		$dialog_result_content = $('<div></div>')
				  .attr('id', 'dialog_result_content')
				  .appendTo($dialog_result);
	}

	var buttons = {};
	buttons[button_name] = function() { hs_dialog("close"); };
	hs_dialog($dialog_result, {
		title: title ? title : "Message",
		fixed_width: 480,
		open: function() { $dialog_result_content.html(result); },
		close: function() {
			if (typeof callback != 'undefined')
				callback();
		},
		title_class: title_class,
		buttons: buttons
	});
}

function confirmDialog(url, title) {
	var $dialogConfirm = $("#dlg_confirm");
	if (!$dialogConfirm.length) {
		$dialogConfirm = $("<div></div>")
				  .attr('id', 'dlg_confirm')
				  .html("<p>Are you sure?</p>")
				  .hide()
				  .appendTo($('body'));
	}

	hs_dialog($dialogConfirm, {
		title: "Confirm " + title,
		title_class: 'nav_info',
		buttons: {
			"No" : function() { hs_dialog("close"); },
			"Yes" : function() {
				hs_dialog("close");
				location.href = url;
			}
		}
	});
}

function dlg_time_picker_mobile ($div_to_update) {
	var $dlg_time_picker_mobile = $("#dlg_time_picker_mobile");
	var $time_picker = $("#dlg_time_picker_mobile_picker");

	if (!$dlg_time_picker_mobile.length) {
		$dlg_time_picker_mobile = $("<div></div>")
				  .attr('id', 'dlg_time_picker_mobile')
				  .hide()
				  .appendTo($('body'));

		$time_picker = $('<div></div>')
				  .attr('id', 'dlg_time_picker_mobile_picker')
				  .appendTo($dlg_time_picker_mobile);

		$time_picker.scroller({
			preset: 'time',
			theme: 'ios',
			display: 'inline',
			mode: 'scroller'
		});
	}

	hs_dialog($dlg_time_picker_mobile, {
		title: "Pick A Time",
		open: function() {
			$time_picker.scroller('setDate', Date.parse($div_to_update.val()));
		},
		buttons: {
			'Set Time' : function() {
				$div_to_update.val(Date.parse($time_picker.scroller('getDate')).toString('h:mmtt'));
				fb.end(1);
			}
		}
	});
}

function submitFeedback() {
	function submitFeedbackCallback(msg) {
		showResult(msg, "Gratitude");
		$("#feedback").val("");
	}

	rest_ajax_post_request_no_timeout(url_submit_feedback, submitFeedbackCallback,
			  {text: jQuery(location).attr('href') + '\n\n' + $('#feedback').val()}
	);
}

function show_compose_message_dlg (to_username, to_name, is_not_authenticated, msg_subject, source) {
	function send_message(data){
		var form = $('#new_message_form');
		rest_ajax_post_request_no_timeout(url_send_message,
				  function(response){
					  ajax_process_form_response(response, form, function(){
						  show_message_send_result(form, $('#id_send_result_msg'));
					  })
				  }, {data: data, source: source});
	}
	if (is_not_authenticated) {
		hs_dialog('#compose_message_dlg', {
			title: 'Send a Message',
			title_class: 'nav_inbox',
			buttons: {
				Send: function() {
					var data = $('#new_message_form').serialize(true);
					data += '&recipient_username=' + to_username;
					send_message(data);
				}
			}
		});
	} else {
		$('#id_recipient').autocomplete({
			source: '/autocomplete/first_last/',
			minLength: 1,
			html: true,
			autoFocus: true,
			select: function(event, ui) {
				$('#recipient_hidden').val(ui.item.id);
				$('#id_subject').focus();
			}
		});

		$("#id_subject").val('');
		$("#id_body").val('');

		$("#id_recipient").removeClass('error');
		$("#id_subject").removeClass('error');
		$("#id_body").removeClass('error');

		hs_dialog("#compose_message_dlg", {
			title: "New Message",
			title_class: 'nav_inbox',
			outsideClickCloses: false,
			open: function() {
				if(!to_name) {
					$("#id_recipient").val('');
					$("#recipient_hidden").val('');
				} else {
					$("#id_recipient").val(to_name);
					$("#recipient_hidden").val(to_username);

					if(msg_subject) {
						$("#id_subject").val(msg_subject);
						$('#id_body').focus();
					} else {
						$('#id_subject').focus();
					}
				}
			},
			close: function() {
				$('.ui-autocomplete').hide();
			},
			buttons: {
				"Send" : function() {
					data = $('#new_message_form').serialize(true);
					send_message(data);
				}
			}
		});

		$("#id_recipient").click(function() {
			$("#id_recipient").val('');

			$("#recipient_hidden").val('');
			$("#id_recipient").removeClass('error');

		});

		$("#id_subject").focus(function() {
			$("#id_subject").removeClass('error');
		});

		$("#id_body").focus(function() {
			$("#id_body").removeClass('error');
		});
	}

	return false;
}

function show_message_send_result(form, msg) {
	form.hide();
	$('.hs_dialog_buttons').hide();
	msg.show();
	msg.fadeTo(0, 200);

	msg.fadeTo(2000, 0, function() {
		msg.hide();
		form.show();
		$('.hs_dialog_buttons').show();
		hs_dialog('close');
	});
}

function hs_dialog($div_or_id, options) {
	switch ($div_or_id) {
		case "close":
			fb.end(); return;
		case "resize":
			fb.resize(0,0); return;
	}

	var $div = ($div_or_id instanceof jQuery) ? $div_or_id : $($div_or_id);

	var dom = $div.get(0);
	if(!dom) return;

	if (options != "open") {
		dom['fb_options'] = {afterItemStart:
			function() {
				if ((typeof options.dont_auto_focus == 'undefined') || (!options.dont_auto_focus))
					$div.find("input[type='text']:first").focus();

				if (options.open)
					options.open.apply(this, arguments);

				if(!is_smallscreen())
					fb.resize(0,0);

				$('input,select,textarea', $div).each(function() {
					if (this.type != "hidden")
						$(this).attr("tabindex", 0);
				});
			},
			doAnimations: false,
			mobileDoAnimations: false,
			overlayFadeTime: 0,
			resizeTime: 0,
			fadeTime: 0,
			imageTransition: 'none',
			transitionTime: 0,
			padding: 5
		};

		if (typeof(options.showClose) != 'undefined'){
			dom.fb_options.showClose = options.showClose;
		}

		if(options.afterStart) {
			dom.fb_options.afterBoxStart = function() {
				options.afterStart();
				fbAfterBoxStart();
			};
		} else {
			dom.fb_options.afterBoxStart = fbAfterBoxStart;
		}

		if (options.close) {
			dom.fb_options.afterBoxEnd = function() {
				fbAfterBoxEnd();
				options.close();
			}
		} else {
			dom.fb_options.afterBoxEnd = fbAfterBoxEnd;
		}

		if (options.beforeClose)
			dom.fb_options.beforeBoxEnd = options.beforeClose;

		if (typeof(options.outsideClickCloses) != 'undefined')
			dom.fb_options.outsideClickCloses = options.outsideClickCloses;

		if (options.title) {
			var $title = $div.find('h3:first');
			if (!$title.length) {
				$title = $('<h3></h3>');
				if(options.title_class) {
					$title.addClass(options.title_class);
					$title.addClass('nav_icon');
				}
				// else
				// 	$title.addClass("nav_schedule");
				$div.prepend($title);
			}
			$title.html(options.title);
		}

		 if(is_smallscreen()) {
			 dom.fb_options.width = '100%';
			 dom.fb_options.height = '100%';
			 dom.fb_options.measureHTML = 'no';
		 } else if (options.fixed_width) {
			 dom.fb_options.width = options.fixed_width;
		 }

		if (options.buttons) dom.buttons = options.buttons;
	}

	if (dom.buttons) {
		var $button_container = $div.find('.button_container').remove();
		$button_container = $('<div class="highlight_container button_container hs_dialog_buttons"></div>');
		$button_container.append('<hr />');
		$div.append($button_container);
		$.each(dom.buttons, function(name, props) {
			var $button = $('<span></span>');
			var $link = $('<span class="look_like_link">' + name + '</span>');
			$button.append($link).appendTo($button_container);

			if ($.isFunction(props)) {
				$button.click(props);
			} else {
				$button.click(props.click);
				if (props.button_class) $button.addClass(props.button_class);
				if (props.link_class) $link.addClass(props.link_class);
			}
		});
		$button_container.append('<div class="clearfix"></div>');
	}


	if ((typeof options.autoOpen == 'undefined') || (options.autoOpen != false)) {
		fb.start('#'+$div.attr('id'), dom.fb_options);
	}

}

function clearForm(form) {
	$(form).find('input[type="text"]').val('');
	$(form).find('textarea').val('');
}

function showError(error, callback) {
	// showResult(error, 'Error', callback, 'status_error');
	showResult(error, 'Sorry!', callback, '');
}

function showSuccess(message, callback) {
	showResult(message, 'Success', callback, 'status_success');
}

/* autocomplete - search */
function initProviderSearchAutocomplete() {
	$(".search_name_or_email").autocomplete({
		source: "/autocomplete/search_name_or_email/",
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			window.location = ui.item.id;
		}
	});
}

function initCitySearchAutocomplete(no_speciality_selection, skip_additional) {
	no_speciality_selection = typeof no_speciality_selection !== 'undefined' ? no_speciality_selection : false;
	skip_additional = typeof skip_additional !== 'undefined' ? skip_additional : false;

	var source = '/autocomplete/city/';
	if (!skip_additional) {
		source += 'search/';
	}

	$(".search_city_or_zipcode").autocomplete({
		source: url_autocomplete_city + "?any_location=1",
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			var container = $(this).closest('form');
			$(".search_city_or_zipcode").val(ui.item.value);
			var search_form = $('#search_form');
			$("#id_city", search_form).val(ui.item.city);
			$("#id_state", search_form).val(ui.item.state);
			$("#id_zipcode", search_form).val('');

			var healers_form = $('#healers_form');
			$("#id_city", healers_form).val(ui.item.city);
			$("#id_state", healers_form).val(ui.item.state);
			$("#id_zipcode", healers_form).val('');

			// healer request form
			$(".zipcode").val(ui.item.id);

			if(container.attr('fire_event'))
				container.trigger('changed');

			//select radio/select
			$(this).closest("form").find("[name='accept_location']").prop("checked", true);
			$(this).closest("form").find("[name='near_my_location'][value='False']").prop("checked", true);

			if (no_speciality_selection) {
				$('.search_form').submit();
			} else {
				refreshSpecialtiesBox(ui.item, modality_code, '#id_modality2', true);
			}
		}
	});
	$('.search_form').submit(function() {
		if($.isNumeric($('.search_city_or_zipcode', $(this)).val())) {
			$("#id_city", $(this)).val('');
			$("#id_state", $(this)).val('');
			$("#id_zipcode", $(this)).val($('.search_city_or_zipcode', $(this)).val());
		}
	});
}

function refreshSpecialtiesBox(item, modality, name, update_modality_id) {
	modality = typeof modality !== 'undefined' ? modality : '';
	update_modality_id = typeof update_modality_id !== 'undefined' ? update_modality_id : false;

	var data = {};
	if (item.id !== false) {
		data.geo = item.id;
	}
	//No refresh method for select2, nor method to get params passed
	// ... so, i'll copy the params passed from django-select2 widget
	var opts = {
		minimumResultsForSearch: 6,
		allowClear: true,
		closeOnSelect: false,
		placeholder: ''
	};

	rest_ajax_get_request_long_timeout(url_geo_specialties, function(html) {
		var $id_modality2 = $("#id_modality2"),
				  $id_modality3 = $("#id_modality3"),
				  $select2_no_healers = $('#select2_no_healers'),
				  $select2_specialties = $('#select2_specialties');

		if (html === 'None') {
			$select2_no_healers.show();
			$select2_no_healers.find('span').html($('.search_city_or_zipcode').val());
			$select2_specialties.hide();
		} else {
			$select2_no_healers.hide();
			$select2_specialties.show();
			$id_modality2.select2('destroy');
			$id_modality2.html(html);
			$id_modality2.select2(opts);
			$id_modality3.html(html);
			$id_modality3.select2(opts);
		}
		if (modality) {
			$(name).val(modality).select2();
			$id_modality3.val(modality).select2();
		}
		if (update_modality_id) {
			update_modality_hidden_ids($(name));
		}
	}, data);
}

function setModality(id, name, is_category) {
	var container = $('.search_form:visible');

	if(is_category) {
		$('#modality_category_id_hidden', $('#search_form')).val(id);
		$('#modality_category_id_hidden', $('#healers_form')).val(id);
	} else {
		$('#modality_id_hidden', $('#search_form')).val(id);
		$('#modality_id_hidden', $('#healers_form')).val(id);
	}

	$('#search_form').val(name);
	$('#healers_form').val(name);
	if(container.attr('fire_event'))
		container.trigger('changed');
	fb.end();
	return false;
}

function update_modality(){
	function modalityCallback() {
		var instance = fb.getInstance(0);
		if(instance && instance.fbContent.contentDocument) {
			instance.fbContent.contentDocument.location.reload();
			fb.end();
		} else {
			fb.end('self');
		}
	}

	rest_ajax_post_request_no_timeout([url_update_modality, selected_modality_id], modalityCallback, {
		title: $('#modality_title_input').val(),
		description: $('#modality_description_textarea').val(),
		visible: $('#modality_visible').is(':checked')
	});
}

function getUrlParameter(sParam) {
	var sPageURL = window.location.search.substring(1);
	var sURLVariables = sPageURL.split('&');
	for (var i = 0; i < sURLVariables.length; i++)
	{
		var sParameterName = sURLVariables[i].split('=');
		if (sParameterName[0] == sParam)
		{
			return sParameterName[1];
		}
	}
}

/* facebook */
function fbLogin(iframe) {
	FB.login(function(response) {
		if(response.authResponse) {
			var url = facebook_callback_url + '?access_token=' + response.authResponse.accessToken + '&signed_request=' + response.authResponse.signedRequest;
			if(!iframe) {
				top.location.href = url;
			} else {
				location.href = url + '&fb=1';
			}
		}
	}, {scope: facebook_scopes});
}

function importFacebookContacts(import_facebook_url, iframe) {
	FB.getLoginStatus(function (response) {
		if (response.status == "connected") {
			if(iframe) {
				location.href = import_facebook_url;
			} else {
				top.location.href = import_facebook_url;
			}
		} else {
			fbLogin(iframe);
		}
	});
}

function get_photos_from_album(album_id, access_token, callback) {
	var photos = [], selected_img;
	FB.api(album_id+"/photos",
			  {
				  'access_token': access_token
			  },
			  function(response) {
				  photos = [];
				  for(var i=0; i< response.data.length; i++){
					  var e = response.data[i];
					  for(var j=0; j<e.images.length; j++){
						  if(e.images[j].height >= e.height) {
							  selected_img = e.images[j];
						  }
					  }

					  if (!selected_img){
						  photos.push(e.images[0]);
					  }else {
						  photos.push(selected_img);
						  selected_img = undefined;
					  }
				  }

				  callback(photos);
			  });
}

function get_fb_profile_photos(uid, access_token, callback) {
	if(!uid) {
		return;
	}
	var album_id;
	FB.api(uid+'/albums',
			  {
				  'access_token': access_token
			  },
			  function(response) {
				  for(var i=0; i<response.data.length; i++) {
					  var e = response.data[i];
					  if (e.name == "Profile Pictures") {
						  album_id = e.id;
						  get_photos_from_album(album_id, access_token, callback);
					  }
				  }
			  });
}

/* schedule */
function update_appointment_details($calendar, calEvent, div_date, div_time, div_treatment, div_location) {
	$(div_date).text($calendar.weekCalendar("formatDate", calEvent.start, "l, n/j"));
	$(div_time).text($calendar.weekCalendar("formatTime", calEvent.start, "g:i") + " - " + $calendar.weekCalendar("formatTime", calEvent.end, 'g:i a'));
	$(div_treatment).text(Treatment.full_title);
	$(div_location).html(calEvent.location != -1 ? location_address[calEvent.location] : calEvent.location_name);
}

/* settings */
function setup_save_and_next(next_url) {
	var $form = $('#setup_body').find('form');
	$form.append('<input type="hidden" name="next" value="' + next_url + '" />');
	$form.submit();
}

function initialize_gmap(canvas_id, x, y, title) {
	var latlng = new google.maps.LatLng(x, y);
	var myOptions = {
		zoom: 14,
		center: latlng,
		mapTypeId: google.maps.MapTypeId.ROADMAP
	};

	var map = new google.maps.Map(document.getElementById(canvas_id),
			  myOptions);

	var marker = new google.maps.Marker({
		position: latlng,
		map: map,
		title:title
	});
}

/* responsive */
function screenSize() {
	var width = $(document).width();
	if(width < 570) {
		return "smallscreen";
	} else if(width >= 570 && width < 788) {
		return "mediumscreen";
	} else {
		return "widescreen";
	}
}

function checkScreen(screenString) {
	return (screenSize().indexOf(screenString) != -1)
}

function is_smallscreen() {
	return checkScreen('smallscreen');
}

function is_mediumscreen() {
	return checkScreen('mediumscreen');
}

function getWindowWidth() {
	var windowWidth = 0;
	if (typeof(window.innerWidth) == 'number') {
		windowWidth = window.innerWidth;
	}
	else {
		if (document.documentElement && document.documentElement.clientWidth) {
			windowWidth = document.documentElement.clientWidth;
		}
		else {
			if (document.body && document.body.clientWidth) {
				windowWidth = document.body.clientWidth;
			}
		}
	}
	return windowWidth;
}

function is_mobile_small(){
	return getWindowWidth() < 545;
}

function is_mobile(){
	return getWindowWidth() < 760;
}

function is_tablet(){
	return getWindowWidth() < 880;
}

/* stripe */
function formatCurrency(amount) {
	var DecimalSeparator = Number("1.2").toLocaleString().substr(1,1);
	var AmountWithCommas = amount.toLocaleString();
	var arParts = String(AmountWithCommas).split(DecimalSeparator);
	var intPart = arParts[0];
	var decPart = (arParts.length > 1 ? arParts[1] : '');
	decPart = (decPart + '00').substr(0,2);

	return intPart + DecimalSeparator + decPart;
}

/* scroll */
function scrollTo(element){
	$('html,body').animate({
		scrollTop: element.offset().top
	}, 700);
}

function activate_smooth_scrolling(){
	$('a[href*=#]:not([href=#])').click(function() {
		if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
			var target = $(this.hash);
			target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
			if (target.length) {
				scrollTo(target);
				return false;
			}
		}
	});
}

/* auth */
function login_redirect(){
	window.location.href = login_url;
}

function rotateItems(container_class, easing, options_hide, options_show, count) {
	var first_item = $(container_class + ' > div.rotate:visible').first();
	var next_item = $(container_class + ' > div.rotate:visible + div.rotate:hidden');
	options_hide = typeof options_hide !== 'undefined' ? options_hide : {};
	options_show = typeof options_show !== 'undefined' ? options_show : {};

	if(next_item.length) {
		next_item = next_item.first();
	} else {
		next_item = $(container_class + ' > div.rotate:hidden').first();
	}
	first_item.hide(easing, options_hide, function() {
		next_item.show(easing, options_show);
		next_item.trigger('fadein');
	});
	if(typeof count !== "undefined")
		if (++rotation_count[container_class] == count)
			stopInterval(container_class);
}

/* phonegap keyboard */
function focus(element){
	element.focus();
	if (phonegap && typeof cordova !== 'undefined') {
		cordova.plugins.Keyboard.show();
	}
}

function hide_keyboard(){
	if (phonegap && typeof cordova !== 'undefined') {
		cordova.plugins.Keyboard.close();
	}
}

/* other */
function activate_gallery(preview){
	preview = typeof preview !== 'undefined' ? preview : false;
	var $element = $('.show_gallery');
	$element.unbind();
	$element.click(function(e) {
		var element;
		if (preview) {
			element = $('.gallery_box');
		} else {
			element = $(this).next('.gallery_box');
		}
		element.find('a:first').trigger('click');
		return false;
	});
}

function objects_are_equal(a, b){
	return JSON.stringify(a) == JSON.stringify(b);
}
