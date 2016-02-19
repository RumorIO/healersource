function dlg_add_length(treatment_type_id) {
	var $dialog = $('#treatment_length_form');
	$('#treatment_type_id').val(treatment_type_id);
	hs_dialog($dialog, {
		title: 'Add Treatment Type Length',
	});
}
function add_treatment_length() {
	function validate_form(){
		if ((parseInt($('#treatment_length_form').find('#id_length_hour').val()) * 60 +
			parseInt($('#treatment_length_form').find('#id_length_minute').val())) < 5 ||
			$('#treatment_length_form').find('#id_cost').val() == '' ||
			parseInt($('#treatment_length_form').find('#id_cost').val()) <= 0) {
				showError('Please enter correct values');
				return false;
		}
		return true;
	}
	if (validate_form()) {
		var data = $('#treatment_length_form').serialize(true);
		rest_ajax_post_request_no_timeout(url_add_treatment_type_length,
			function(response){
				location.reload();
			}, {data: data});
	};
}

function dlg_copy_my_treatment_types(wcenter_id) {
	var $dialog = $('#copy_my_treatment_types_dlg_' + wcenter_id);
	hs_dialog($dialog, {
		title: 'Copy My Treatment Types',
		buttons: {
			No: function () {
				hs_dialog('close');
			},
			Yes: function () {
				window.location.href = url_copy_my_treatment_types + wcenter_id;
			}
		}
	});
}

function activate_treatment_types_settings() {
	function enable_auto_select_deselect(){
		// enables auto selecting and deselecting of treatment lengths belonging to the same treatment type
		$('.tt_form').each(function(){
			var form = $(this);
			var types = form.find('.treatment_type_select_item');
			types.find('input,label').unbind('click');

			types.each(function(){
				var type = $(this);
				var type_input = type.find('input').first();
				var type_label = type.find('label').first();
				var id = type_input.attr('id');
				var lengths = form.find('.' + id);
				if (lengths.length !== 0) {
					type_input.click(function(){
						lengths.prop('checked', $(this).is(':checked'));
					});
					type_label.click(function(){
						var input = $(this).parent().find('input').first();
						input.prop('checked', !input.is(':checked'));
						lengths.prop('checked', input.is(':checked'));
						return false;
					});
				}
			});
			form.find('.treatment_length_select_item').find('input').change(function(){
				var input_id = $('#t_length_608').attr('class');
				process_treatment_checkboxes(form, $('#' + input_id));
			});
		});
	}

	enable_auto_select_deselect();

	$('.save_treatment_types').click(function(){
		function get_ids(type){
			var ids = [];
			form.find(type).find('input[type=checkbox]:checked').each(function(){
				ids.push($(this).val());
			});
			return ids;
		}

		var wcenter_id = $(this).attr('data-id');
		var form = $('#wcenter_tt_form_' + String(wcenter_id));
		//process_checkboxes(form);

		var selected_treatment_types = get_ids('.treatment_type_select_item');
		form.children('input[name=type_lengths]').val(JSON.stringify(get_ids('.treatment_length_select_item')));

		// Check if one treatment length is selected and then select treatment type itself
		var id;
		form.find('.treatment_length_select_item').find('input[type=checkbox]:checked').each(function(){
			id = $(this).data('treatment-type-id');
			if (selected_treatment_types.indexOf(id) == -1) {
				selected_treatment_types.push(id);
			}
		});
		form.children('input[name=types]').val(JSON.stringify(selected_treatment_types));
	});

	$('.copy_my_treatment_types').click(function(){
		dlg_copy_my_treatment_types($(this).attr('data-wcenter-id'));
	});
}

function process_treatment_checkboxes(form, treatment_type_checkbox_element){
	var id = treatment_type_checkbox_element.attr('id');
	var lengths_all = form.find('.' + id);
	var lengths_checked = form.find('.' + id + ':checked');
	if (lengths_all.length !== 0) {
		if (lengths_checked.length == lengths_all.length ) {
			// auto select treatment type if all lengths are selected
			treatment_type_checkbox_element.prop('checked', true);
		} else if (lengths_checked.length === 0){
			if (treatment_type_checkbox_element.is(':checked')) {
				lengths_all.prop('checked', true);
			}
		} else {
			treatment_type_checkbox_element.prop('checked', false);
		}
	}
}

function process_checkboxes(form){
	/* Mark all of treatment lengths selected for a certain type
		if none of them are selected while their treatment type is selected.
	*/
	var types = form.find('.treatment_type_select_item input');
	types.each(function(){
		process_treatment_checkboxes(form, $(this));
	});
}

$(function() {
	function process_all_checkboxes(){
		$('.tt_form').each(function(){
			process_checkboxes($(this));
		});
	}

	activate_treatment_types_settings();
	process_all_checkboxes();
});
