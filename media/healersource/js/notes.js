var current_client_id = false;
var current_note_id;
var marker_elements = {};
var marker_id;
var marker_chosen = false;
var dots = {};
var DIAGRAM_SIZE;
var current_mode;
var total_diagrams;
var is_new_note;
var visible_diagrams_ids;
var dragging_in_progress = false;
var clients;
var favorite_diagrams;
var dot_creation_enabled = true; // required for phonegap to avoid creating dot
								 // when diagram selection menu is open (right
								 // after mouseleave event)
var search_filter_client_id = false;
var initial_note_data;
var position_diagram_right = false; // temporary variable which is set when
  									// diagram has to be positioned right and
  									// gets reset after it's shown.

$.fn.visible = function() {
	return this.css('visibility', 'visible');
};

$.fn.hidden = function() {
	return this.css('visibility', 'hidden');
};

function isEven(n) {
	return parseInt(n) % 2 == 0;
}

Array.prototype.getUnique = function(){
   var u = {}, a = [];
   for(var i = 0, l = this.length; i < l; ++i){
	  if(u.hasOwnProperty(this[i])) {
		 continue;
	  }
	  a.push(this[i]);
	  u[this[i]] = 1;
   }
   return a;
};

function load_notes_list_for_client(client_id) {
	search_filter_client_id = client_id;
	load_notes_list();
}

function reset_search_filter(){
	$('#search_client_filter_note').val('');
	search_filter_client_id = false;
	$('#clear_search').hide();
	$('#notes_for').empty();
}

function clear_search(){
	reset_search_filter();
	load_notes_list();
}

function create_note_for_client(client_id) {
	current_client_id = client_id;
	create_note();
}

function initClientSearchAutocomplete() {
	var source = function(request, response) {
			var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), 'i');
			response($.grep(clients, function(value) {
				return matcher.test(value.value);
			}));
		};
	$('#search_client_new_note').autocomplete({
		source: source,
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			create_note_for_client(ui.item.id);
			reset_search_filter();
			return false;
		}
	});
	$('#search_client_filter_note').autocomplete({
		source: url_autocomplete_clients_with_notes,
		minLength: 2,
		html: true,
		autoFocus: true,
		select: function(event, ui) {
			$('#notes_for').html('for ' + ui.item.value);
			load_notes_list_for_client(ui.item.id);
		}
	});
}

function rest_ajax_post_request_note(url, callback, data){
	callback_ = function(){
		if (typeof arguments[0] !== 'undefined' &&
				arguments[0].error_type == 'no_notes_permission') {
			var error = 'We hope you have enjoyed your free trial of SOAP Notes. Please enter your payment information to continue.';
			showError(error, function(){
				if (!phonegap){
					window.location.href = url_account_settings + '#notes';
				}
			});
		} else {
			callback.apply(this, arguments);
		}
	};
	rest_ajax_post_request(url, callback_, data);
}

function new_note(client_id) {
	rest_ajax_post_request_note([url_create, client_id],
		function(note_id){
			edit_note(note_id, true);
		}, {client_id: client_id});
}

function duplicate_note(id){
	rest_ajax_post_request_note([url_duplicate, id],
		function(new_note_id){
			edit_note(new_note_id, true);
		}, {id: id});
}

function create_note() {
	if (current_client_id) {
		new_note(current_client_id);
		current_client_id = false;
		$('#search_client_new_note').val('');
	} else {
		showError('Please select a client');
	}
}

function dlg_edit_dot(dot_id, dot_data) {
	dot_data = typeof dot_data !== 'undefined' ? dot_data : false;

	var save_dot = function() {
		var text = $('#dot_text').val();
		if (dot_data) {
			dot_data.text = text;
			var dot_data_to_send = $.extend({}, dot_data)
			dot_data_to_send.position = JSON.stringify(dot_data.position)

			rest_ajax_post_request([url_dot_create, current_note_id],
				function(dot_id){
					dots[dot_id] = dot_data;
					refresh_dots();
					hide_keyboard();
					hs_dialog('close');
				}, dot_data_to_send
			);
		} else {
			rest_ajax_post_request([url_dot_save_text, dot_id],
				function(){
					dots[dot_id].text = text;
					refresh_tooltips(dot_id);
					hs_dialog('close');
				}, {text: text});
		}
	};

	function get_buttons(){
		function get_delete_button_name(){
			if (dot_data) {
				return 'Cancel';
			} else {
				return 'Delete';
			}
		}

		function delete_dot(){
			if (dot_data) {
				hs_dialog('close');
			} else {
				rest_ajax_post_request([url_dot_delete, dot_id],
					function(){
						delete dots[dot_id];
						refresh_dots();
						hs_dialog('close');
				});
			}
		}

		buttons = {
			Save: save_dot
		};
		buttons[get_delete_button_name()] = {
				button_class: 'float_left',
				click: delete_dot
			};
		return buttons;
	}

	var $dialog = $('#edit_dot_dialog');
	hs_dialog($dialog, {
		fixed_width: 300,
		open: function () {
			focus($('#dot_text'));
			$('#dot_text').unbind('keypress');
			$('#dot_text').on('keypress', function(e) {
				if (e.keyCode == 13 && !(e.shiftKey || e.ctrlKey || e.altKey || e.metaKey)) {
					save_dot();
					return false;
				}
			});

			if (!dot_data) {
				$('#dot_text').val(dots[dot_id].text);
			}
		},
		close: function () {
			$('#dot_text').val('');
			block_dot_creation_temporarily();
		},
		buttons: get_buttons()
	});
}

function show_note_menu(id) {
	$('#note_menu_' + id).slideToggle();
}

function newClientSuccess(client) {
	$('#search_client_new_note').val(client.value);
	create_note_for_client(client.id);
	clients.push(client);
	process_no_clients_situation();
}

function on_notes_list_load(response) {
	var elements = $('#recent_notes,.clients_search');
	if (!search_filter_client_id && !response.notes_exist) {
		elements.hide();
	} else {
		elements.show()
	}
	$('#notes_list').html(response.html);
	fb.activate();
}

function load_notes_list(){
	url = url_list;
	if (search_filter_client_id) {
		url = [url, search_filter_client_id];
		$('#clear_search').show();
	}
	rest_ajax_get_request(url, on_notes_list_load, {'is_mobile': is_mobile()});
}

function refresh_tooltips(id) {
	function get_elements(){
		if (id) {
			return $('.dot[data-id=' + id + ']');
		} else {
			return $('.dot');
		}
	}

	id = typeof id !== 'undefined' ? id : false;
	get_elements().each(function(){
		function activate_tooltip_edit_button(){
			$('.tooltip_edit_button').unbind('click').click(function(){
				dlg_edit_dot(id);
			})
		}

		var id = $(this).data('id');
		var text = dots[id].text;

		// show tooltip for phonegap even if no text.
		if (text !== '' || phonegap) {
			$(this).attr('data-fb-tooltip', 'source:#tooltip attachToHost:true fadeDuration:0 delay:10 placement:right beforeBoxStart:test_if_dragging_in_process afterBoxEnd:block_dot_creation_temporarily')
					.addClass('fbTooltip')
					.mouseenter(function() {
									$('#tooltip_text').html(text);
									activate_tooltip_edit_button();
								});
		} else {
			// can't totally disactivate it.
			$(this).mouseenter(function() {
				$('#tooltip_text').html('');
				activate_tooltip_edit_button();
			});
		}
	});
	fb.activate();
}

function test_if_dragging_in_process(){
	return !dragging_in_progress;
}

function activate_marker() {
	function choose_first_marker_if_not_chosen(){
		if (!marker_chosen) {
			marker_chosen = $('.marker').first().data('id');
		}
	}
	choose_first_marker_if_not_chosen();
	$('.marker_selected').removeClass('marker_selected');
	marker_id = marker_chosen;
	$('.diagram').css('cursor', 'crosshair');
	$('.marker[data-id=' + marker_chosen + ']').addClass('marker_selected');
}

function refresh_dots(){
	function activate_dots(){
		$('.dot').draggable({
			start: function() {
				dragging_in_progress = true;
				fb.end();
			},
			stop: function(event) {
				function fix_initial_position(){
					if (event.offsetX < 15 && event.offsetY < 15) {
						event.clientX -= event.offsetX;
						event.clientY -= event.offsetY;
					if (event.offsetX < 10 && event.offsetY < 10) {
							event.clientX -= 2;
							event.clientY -= 2;
						}
					}
					return event;
				}

				function reposition_if_out_of_bounds(position){
					if (position[0] < 0) {
						position[0] = 0;
						position[1] -= 8;
					}
					if (position[1] < 0) {
						position[1] = 0;
						position[0] -= 8;
					}
					if (position[0] > DIAGRAM_SIZE[0]) {
						position[0] = DIAGRAM_SIZE[0] - 14;
						position[1] -= 8;
					}

					if (position[1] > DIAGRAM_SIZE[1]) {
						position[1] = DIAGRAM_SIZE[1] - 14;
						position[0] -= 8;
					}
					return position;
				}

				dragging_in_progress = false;
				var element = $(this);
				var id = element.data('id');
				var position = reposition_if_out_of_bounds(
					get_position(element.parent().find('.diagram'),
						fix_initial_position(event)));
				rest_ajax_post_request([url_dot_save_position, id],
					function(){
						dots[id].position = position;
					}, {
						position: JSON.stringify(position)
					}, undefined, refresh_dots);
			},
			containment: 'parent',
			stack: ".dot"
		}).css('cursor', 'move');

		if (!phonegap) {
			$('.dot').click(function(event){
				dlg_edit_dot($(this).data('id'));
			})
		}
	}

	function position_dot(element, position){
		element.css('left', position[0]);
		element.css('top', position[1]);
	}

	$('.diagram_container').find('.dot').remove();

	for (var dot_id in dots) {
		dot = dots[dot_id];
		$('.diagram_container[data-id=' + dot.diagram_id + ']').prepend(
			'<div class="dot" data-id="' + dot_id + '" title="Click to Edit. Drag to Move.">' + marker_elements[dot.marker_id] + '</div>');
		position_dot($('.dot[data-id=' + dot_id + ']'), dot.position);
	}
	if (current_mode == 'edit') {
		activate_dots();
	}
	refresh_tooltips();
}

function show_selection_menu(){
	$('.section_select').css('display','inline-block');
	set_is_even_for_section_diagrams();
}

function reorder_diagrams(){
	function order_diagram(element, id, order) {
		element.attr('data-order', order);
		$('.diagram_thumb[data-id=' + id + ']').click(function(){
			show_diagram(order);
		}).show();
		i++;
	}

	var i = 1;

	$('.diagram_thumb').unbind('click');
	$('.diagram_container').removeAttr('data-order').each(function(){
		var element = $(this);
		var id = element.data('id');
		if (visible_diagrams_ids == 'all' || visible_diagrams_ids.indexOf(id) !== -1) {
			order_diagram(element, id, i);
			if (!diagram_in_favorites(id)) {
				$('.diagram_thumb[data-id=' + id + ']').hide();
			}
		} else {
			$('.diagram_thumb[data-id=' + id + ']').hide();
		}
	});
}

function set_is_even_for_section_diagrams(){
	// required to properly position even diagrams in the left.
	var n = 0;
	$('.section_diagram:visible').each(function(){
		n++;
		if (isEven(n)){
			$(this).data('even', true);
		}
	});
}

function refresh_diagrams(){
	function get_visible_diagrams_ids(){
		var diagrams = [];
		for (var id in dots) {
			var diagram_id = dots[id].diagram_id;
			diagrams.push(diagram_id);
		}
		return diagrams.getUnique();
	}

	if (current_mode == 'view') {
		visible_diagrams_ids = get_visible_diagrams_ids();
		total_diagrams = visible_diagrams_ids.length;
		if (total_diagrams === 0) {
			return;
		}
	} else {
		visible_diagrams_ids = 'all';
		total_diagrams = $('.diagram_container').length;
	}

	reorder_diagrams();
	show_diagram(1);
	$('#diagram_content').show();

}

function edit_note(id, note_is_new_note){
	note_is_new_note = typeof note_is_new_note !== 'undefined' ? note_is_new_note : false;
	is_new_note = note_is_new_note;

	loading_complete = false;
	hide_keyboard();
	if (is_tablet()){
		// reset soap_diagram_button
		switch_soap_diagram_button('soap', 'diagram');
	}

	rest_ajax_get_request([url_get, id],
		function(response){
			function process_note_links(){
				$('.note_link').hidden();
				if (response.prev_note) {
					element = $('#prev_note');
					element.visible();
					element.data('id', response.prev_note);
				}
				if (response.next_note) {
					element = $('#next_note');
					element.visible();
					element.data('id', response.next_note);
				}
			}

			function configure_mode_edit_or_view(){
				function reset_to_initial_state() {
					function reset_marker(){
						$('.marker_selected').removeClass('marker_selected');
						marker_id = false;
					}

					function reset_diagram_cursor() {
						$('.diagram').css('cursor', 'default');
					}

					reset_marker();
					reset_diagram_cursor();
					$('.diagram_thumb').show();
					$('#diagram_content').hide();
					$('.section_diagram').hide();
					if (is_tablet()) {
						$('.soap_diagram_button').show();
					}
					$('.diagrams_list_button').visible();
				}

				function enable_edit_mode(){
					current_mode = 'edit';
					initial_note_data = get_note_data();
					activate_marker();
					$('.tooltip_edit_button').visible();

					$('.text_cell').show();
					$($('#subjective_box').children()[1]).replaceWith($('<textarea id="subjective"></textarea>'));
					$($('#objective_box').children()[1]).replaceWith($('<textarea id="objective"></textarea>'));
					$($('#assessment_box').children()[1]).replaceWith($('<textarea id="assessment"></textarea>'));
					$($('#plan_box').children()[1]).replaceWith($('<textarea id="plan"></textarea>'));

					$('#subjective').val(note.subjective);
					$('#objective').val(note.objective);
					$('#assessment').val(note.assessment);
					$('#plan').val(note.plan);

					$('#subjective, #objective, #assessment, #plan').prop('disabled', false);

					$('.overall_condition_table input').prop('disabled', false)
					$('.marker_bar, .save_delete_buttons, .save_button').show();
					update_favorite_diagrams();
					$('.section_item').first().trigger('click');
					$('#section_top_bar').show();
					$('#cancel_changes').html('Cancel Changes');

					$('#created_date').click(function() {
						$('#created_date_input').show().focus().hide();
					})
				}

				function enable_view_mode(){
					current_mode = 'view';
					$('.tooltip_edit_button').hidden();

					$('.text_cell').hide();
					$($('#subjective_box').children()[1]).replaceWith($('<div id="subjective"></div>'));
					$($('#objective_box').children()[1]).replaceWith($('<div id="objective"></div>'));
					$($('#assessment_box').children()[1]).replaceWith($('<div id="assessment"></div>'));
					$($('#plan_box').children()[1]).replaceWith($('<div id="plan"></div>'));

					if (note.subjective) {
						$('#subjective_box').show();
						$('#subjective').html(note.subjective);
					}

					if (note.objective) {
						$('#objective_box').show();
						$('#objective').html(note.objective);
					}
					if (note.assessment) {
						$('#assessment_box').show();
						$('#assessment').html(note.assessment);
					}
					if (note.plan) {
						$('#plan_box').show();
						$('#plan').html(note.plan);
					}

					$('.overall_condition_table input').prop('disabled', true)
					$('.marker_bar, .save_delete_buttons, .save_button').hide();
					update_favorite_diagrams();
					$('#section_top_bar').hide();
					$('.section_diagram').each(function(){
						if (visible_diagrams_ids.indexOf($(this).data('id')) !== -1) {
							$(this).css('display','inline-block');
						}
					});
					$('#cancel_changes').html('&laquo; Go back to list');

					if (is_tablet() && Object.keys(dots).length === 0) { // don't show diagram if there are no dots
						switch_soap_diagram_button('diagram', 'soap');
						$('.soap_diagram_button').hide();
					}

					if (Object.keys(dots).length === 0) {
						$('.diagrams_list_button').hidden();
					}
					$('#created_date').unbind('click');
				}

				reset_to_initial_state();
				if (note.is_finalized) {
					enable_view_mode();
				} else {
					enable_edit_mode();
				}
			}

			function activate_section_dropdown(){
				$('#section_menu_toggle_button').unbind('mouseenter').mouseenter(function(){
					show_selection_menu();
				});

				$('#section_menu').unbind('mouseleave').mouseleave(function(){
					hide_selection_menu();
				});

				$('.section_item').unbind('click').click(function(){
					var section_id = $(this).data('id');
					$('.section_diagram').hide().each(function(){
						if ($(this).data('section-id') == section_id) {
							$(this).css('display','inline-block');
						}
					});
					set_is_even_for_section_diagrams();
				});

				$('.favorite').unbind('click').click(function(){
					var id = $(this).parent().data('id');
					var is_even = $(this).parent().data('even');
					rest_ajax_post_request([url_save_favorite_diagram, id],
						function(data){
							favorite_diagrams = data;
							update_favorite_diagrams();
							show_diagram_id(id, is_even);
						}, {
							action: !diagram_in_favorites(id) // add if not in favorites
						});
						return false;
				});
			}

			var note = response.note;
			$('#client_name').html(note.client_name);
			$('#created_date').html(note.created_date);
			process_note_links();

			current_note_id = id;

			if (note.condition) {
				$('input[name="condition"][value="' + note.condition + '"]').prop('checked', true);
			} else {
				$('input[name="condition"]').prop('checked', false);
			}
			$('#created_date_input').val(note.created_date_full);
			dots = response.dots;
			activate_section_dropdown();
			configure_mode_edit_or_view();
			switch_content('edit');
			refresh_arrow_buttons();
			DIAGRAM_SIZE = [$('.diagram').width(), $('.diagram').height()];
			refresh_dots();
			if (phonegap) {
				changeBackButton(function(){
					$('#cancel_changes').trigger('click');
				});
				switch_header(true);
			}
		});
	loading_complete = true;
}

function switch_content(content){
	$('.content').hide();
	$('#content_' + content).show();
}

function get_note_data(){
	return {
		subjective: $('#subjective').val(),
		objective: $('#objective').val(),
		assessment: $('#assessment').val(),
		plan: $('#plan').val(),
		condition: $('input[name="condition"]:checked').val(),
		created_date: $('#created_date_input').val()
	};
}

function ajax_save_note(finalize) {
	finalize = typeof finalize !== 'undefined' ? finalize : false;
	data = get_note_data();
	data.finalize = finalize
	rest_ajax_post_request([url_save, current_note_id],
		reload_list, data);
}

function refresh_arrow_buttons(){
	function get_left_button_diagram_order(){
		var diagram_prev_two = first_visible_diagram_order - number_of_diagrams_on_screen;
		if (diagram_prev_two > 0) {
			return diagram_prev_two;
		} else {
			return 1;
		}
	}

	function get_number_of_diagrams_on_screen(){
		if (is_mobile()) {
			return 1;
		} else {
			return 2;
		}
	}

	var number_of_diagrams_on_screen = get_number_of_diagrams_on_screen();

	$('.bottom_arrow').hidden().removeAttr('onclick');
	var first_visible_diagram_order = parseInt($('.diagram_container:visible').first().attr('data-order'));
	if (first_visible_diagram_order !== 1) {
		$('.bottom_arrow_left').visible();
		$('.bottom_arrow_left').attr('onclick', 'show_diagram(' + get_left_button_diagram_order() + ')');
	}
	if (first_visible_diagram_order < total_diagrams - (number_of_diagrams_on_screen - 1)) {
		$('.bottom_arrow_right').visible();
		$('.bottom_arrow_right').attr('onclick', 'show_diagram(' + (first_visible_diagram_order + number_of_diagrams_on_screen) + ')');
	}
}

function show_diagram(order) {
	$('.diagram_container').hide();
	var diagram_container = $('.diagram_container[data-order=' + order + ']');
	diagram_container.show();
	var next_diagram_containers = diagram_container.nextAll('.diagram_container[data-order]');
	if (next_diagram_containers.length === 0 || position_diagram_right) {
		var prev_diagram_containers = diagram_container.prevAll('.diagram_container[data-order]');
		if (prev_diagram_containers.length !== 0) {
			if (!is_mobile()) {
				prev_diagram_containers.first().show();
			}
		}
	} else {
		if (!is_mobile()) {
			next_diagram_containers.first().show();
		}
	}
	refresh_arrow_buttons();
	position_diagram_right = false;
}

function get_position(element, event){
	function fix_coordinate_if_negative(n){
		if (n < 0) {
			n = 0;
		}
		return n;
	}

	var offset = element.offset();
	var offset_t = offset.top - $(window).scrollTop();
	var offset_l = offset.left - $(window).scrollLeft();
	var x = Math.round((event.clientX - offset_l));
	var y = Math.round((event.clientY - offset_t));
	x = fix_coordinate_if_negative(x)
	y = fix_coordinate_if_negative(y)
	return [x, y];
}

function switch_header(inner){
	inner = typeof inner !== 'undefined' ? inner : false;

	$('.header_logo,.header_content,.header_additional_content').hide();
	if (inner) {
		$('.header_content,.header_additional_content').show();
	} else {
		$('.header_logo').show();
	}
}

function reload_list(){
	load_notes_list();
	switch_content('list');
	if (phonegap){
		changeBackButton(home);
		switch_header();
	}
}

function delete_note(){
	rest_ajax_post_request([url_delete, current_note_id], reload_list);
}

function update_favorite_diagrams(){
	$('.favorite').each(function(){
		if (favorite_diagrams.indexOf($(this).parent().data('id')) === -1) {
			$(this).html('☆');
		} else {
			$(this).html('★');
		}
	});
	refresh_diagrams();
}

function diagram_in_favorites(id){
	return favorite_diagrams.indexOf(id) !== -1;
}

function show_diagram_id(id, is_even){
	is_even = typeof is_even !== 'undefined' ? is_even : false;
	if (is_even) {
		position_diagram_right = true;
	}

	if (current_mode == 'view' && !diagram_in_favorites(id)) {
		return;
	}
	$('.diagram_thumb[data-id=' + id + ']').trigger('click');
}

function block_dot_creation_temporarily(){
	if (phonegap) {
		dot_creation_enabled = false;
		setTimeout(function(){
			dot_creation_enabled = true;
		}, 500); // don't allow dot creation for 0.5sec after closing diagram menu
	}
}

function hide_selection_menu() {
	$('.section_select').hide();
	block_dot_creation_temporarily();
}

function activate_section_dropdown(){
	$('#section_menu_toggle_button').mouseenter(function(){
		$('.section_select').css('display','inline-block');
	});
	$('#section_menu').mouseleave(function(){
		hide_selection_menu();
	});

	$('.section_item').click(function(){
		var section_id = $(this).data('id');
		$('.section_diagram').hide().each(function(){
			if ($(this).data('section-id') == section_id) {
				$(this).css('display','inline-block');
			}
		});
	});

	$('.section_item').first().trigger('click');

	$('.favorite').click(function(){
		var id = $(this).parent().data('id');
		rest_ajax_post_request([url_save_favorite_diagram, id],
			function(data){
				favorite_diagrams = data;
				update_favorite_diagrams();
				show_diagram_id(id);
			}, {
				action: !diagram_in_favorites(id) // add if not in favorites
			});
			return false;
	});
	update_favorite_diagrams();
}

function remove_trial_notice(){
	rest_ajax_post_request(url_remove_trial_notice, function(){
		$('.trial_notice').hide();
	});
}

function process_no_clients_situation(){
	var new_client_button_label;
	if (clients.length === 0) {
		new_client_button_label = '+ Create Your First Note';
	} else {
		new_client_button_label = '+ New Client';
		$('.add_note').show();
	}
	$('.new_client_link').html(new_client_button_label).show();
}

function switch_soap_diagram_button(from, to) {
	function fix_header2_position(){
		var margin;
		if (from == 'diagram') {
			margin = '-' + $('.smallscreen_logo').height();
		} else {
			margin = '3';
		}
		$('.diagram_section_dropdown,#date_menu').css('margin-top', margin + 'px');
	}

	if (current_mode == 'edit') {
		$('.additional_content').show();
	}
	$('.soap_diagram_button').removeClass(to + '_button');
	$('.soap_diagram_button').addClass(from + '_button');
	$('#' + from + '_content').hide();
	$('.' + from + '_additional_content').hide();
	$('#' + to + '_content').show();
	if (phonegap) {
		fix_header2_position();
	}
	hide_selection_menu();

}

function on_initial_data_load(data) {
	clients = data.clients;
	process_no_clients_situation();
	favorite_diagrams = data.favorite_diagrams;
	var current_client = data.current_client;
	if (current_client) {
		current_client_id = current_client.id;
		$('#search_client_new_note').val(current_client.name);
	}
}

$(function() {
	function initiate_notes(){
		var activate_event_type = phonegap && cordova && cordova.platformId === "android" ? 'touchend' : 'click';
		function activate_diagram_click() {
			$('.diagram').bind(activate_event_type, function(event){
				function fix_initial_position(event){
					if(event.type === 'touchend') {
						event.clientX = event.originalEvent.changedTouches[0].clientX;
						event.clientY = event.originalEvent.changedTouches[0].clientY;
					}
					event.clientX -= 7;
					event.clientY -= 7;
					return event;
				}

				function create_dot(diagram_id, position){
					dot_data = {
						diagram_id: diagram_id,
						marker_id: marker_id,
						position: position
					};

					dlg_edit_dot(false, dot_data);
				}

				if (marker_id && dot_creation_enabled){
					create_dot($(this).data('id'), get_position($(this),
						fix_initial_position(event)));
				}
			});
		}

		function swipe_diagram(button) {
			$('.diagram').unbind('click');
			if (!dragging_in_progress) {
				button.trigger('click');
			}
			setTimeout(function(){
				activate_diagram_click();
			}, 10);
		}

		function activate_top_header_phonegap_links(){
			if (phonegap) {
				$('.header_additional_content').click(function(){
					ajax_save_note();
				});
			}
		}

		activate_top_header_phonegap_links();

		// List page
		initClientSearchAutocomplete();
		initNewClientDialog(undefined, phonegap);
		if(phonegap) {
			load_notes_list();
			rest_ajax_get_request(url_load_initial_data, on_initial_data_load);
		}

		$('#search_client_filter_note').click(clear_search);

		// Edit page
		$('#save').click(function(){
			ajax_save_note();
		});

		$('#save_and_finalize').click(function(){
			hs_dialog($('#finalize_note_confirmation_dialog'), {
				fixed_width: 300,
				buttons: {
					Ok: function() {
						ajax_save_note(true);
						hs_dialog("close");
					},
					Cancel: function() { hs_dialog('close'); },
				}
			});
		});

		$('#cancel_changes').click(function(){
			function cancel_changes(){
				if (is_new_note) {
					delete_note();
				} else {
					reload_list();
				}
			}

			if (!loading_complete) {
				cancel_changes();
			}
			if (current_mode == 'edit' && !objects_are_equal(initial_note_data, get_note_data())) {
				hs_dialog($('#cancel_changes_confirmation_dialog'), {
					fixed_width: 300,
					buttons: {
						No: function() { hs_dialog('close'); },
						Yes: function() {
							cancel_changes();
							hs_dialog("close");
						}
					}
				});
			} else {
				cancel_changes();
			}
		});

		$('.note_link').click(function(){
			edit_note($(this).data('id'));
		});

		$('.marker').click(function(){
			marker_chosen = $(this).data('id');
			activate_marker();
		});

		$('#delete_note').click(function(){
			var $dialog = $('#delete_note_confirmation_dialog');
			hs_dialog($dialog, {
				fixed_width: 300,
				buttons: {
					No: function() { hs_dialog('close'); },
					Yes: function() {
						delete_note();
						hs_dialog("close");
					}
				}
			});
		});

		activate_diagram_click();

		$('img').on('dragstart', function(event) {
			event.preventDefault();
		});

		$('.diagrams').swipe({
			swipeLeft: function() {
				swipe_diagram($('.bottom_arrow_right'));
			},
			swipeRight: function() {
				swipe_diagram($('.bottom_arrow_left'));
			}
			//threshold: 0
		  });

		$('.section_diagram img').click(function(){
			var id = $(this).parent().data('id');
			var is_even = $(this).parent().data('even');
			show_diagram_id(id, is_even);
			hide_selection_menu();
		});

		$('#section_menu_toggle_button').click(function(){
			if ($('.section_select').is(':visible')) {
				hide_selection_menu();
			} else {
				show_selection_menu();
			}
		});

		$('.soap_diagram_button').click(function(){
			if ($(this).hasClass('soap_button')) {
				switch_soap_diagram_button('diagram', 'soap');
			} else {
				switch_soap_diagram_button('soap', 'diagram');
			}
		});
	}

	if (phonegap && !access_token) {
		$('.content').hide();
		$('#notes_unauth').show();
	} else {
		initiate_notes();
	}

	if (is_tablet()){
		$('.new_client_link').addClass('grey_box');
		//$('.clients_search').after($('.new_client_link'));

		$('.diagram_arrows').hide();
		$('#date_menu').before($('.marker_bar'));
	} else {
		$('.soap_diagram_button').hide();
	}

	$('#created_date_input').datepicker({
		onSelect: function(dateText, input) {
			dateText = dateText.split('/');
			year = dateText.pop();
			if(year !== new Date().getFullYear().toString()) {
				dateText.push(year);
			}
			$('#created_date').text(dateText.join('/'));
		}
	});
	// make dot edit textarea full height on mobile.
//	if (is_mobile()) {
//		$('#dot_text').css('height', $(window).height() - 190)
//	}

});
