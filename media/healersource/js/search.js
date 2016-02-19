function updateSearchResults(event) {
	function updateSearchResultsCallback(data) {
		var $search_results = $('#search_results');
		$search_results.html(data);
		$('#search_results_loader').hide();
		if (typeof search_results_infinite_scroll !== 'undefined') {
			search_results_infinite_scroll.reset();
		}
		$search_results.trigger('updated');
	}

	function reset_city_if_any_location_is_selected(){
		if (city.indexOf('Everywhere') !== -1) {
			city = '';
		}
	}

	if (phonegap && is_android()) {
		$(document.activeElement).trigger('blur');
	}

	$('#search_results').find('.message').hide();
	$('#search_results_loader').show();
	var container = $(event.target).parent();
	var city = $('.search_city_or_zipcode', container).val();
	reset_city_if_any_location_is_selected();

	var remote_sessions = '';
	if (typeof embed_user === 'undefined') {
		var embed_user = '';
	}

	if (city.indexOf('Phone, Online, Skype, or Distance Sessions') !== -1) {
		city = '';
		remote_sessions = 1; // true
	}
	var specialty = $('#id_modality3').val();
	var query = {
		search_city_or_zipcode: city,
		modality: specialty,
		city: city ? $("#id_city", container).val() : '',
		state: city ? $("#id_state", container).val() : '',
		zipcode: city ? $("#id_zipcode", container).val() : '',
		modality_id: specialty ? $('#modality_id_hidden', container).val() : '',
		modality_category_id: specialty ? $('#modality_category_id_hidden', container).val() : '',
		display_type: search_results_display_type,
		remote_sessions: remote_sessions,
		embed_user: embed_user
	};
	update_selected_modality_vars();
	if (typeof exclude_centers !== 'undefined') {
		query.exclude_centers = 1; // true
	}

	query.phonegap = phonegap;
	rest_ajax_get_request_long_timeout(url_search, updateSearchResultsCallback, query);
}

function changeDisplayType(type) {
	search_results_display_type = type;
	$('#healers_form').trigger('changed');
	return false;
}

function focusCitySearchField(e) {
	var container = $(e.target).parent();
	$(e.target).val('');
	$("#id_city", container).val('');
	$("#id_state", container).val('');
	$("#id_zipcode", container).val('');
}

function get_modality_code(modality_id, modality_category_id) {
	if (modality_id) {
		return 'c:' + modality_id;
	} else if (modality_category_id) {
		return 'p:' + modality_category_id;
	}
	return '';
}

$(function() {
	var $healers_form = $('#healers_form'),
		$search_city_or_zipcode = $('.search_city_or_zipcode');

	$healers_form.bind('changed', updateSearchResults);
	$healers_form.submit(function(e) {
		e.preventDefault();
		$('#healers_form').trigger('changed');
	});
	$search_city_or_zipcode.click(focusCitySearchField);
	$search_city_or_zipcode.blur(function(){
		if ($('.search_city_or_zipcode').val() === '') {
			refreshSpecialtiesBox({'id': false}, modality_code, '#id_modality2', true);
		}
	});
	$search_city_or_zipcode.keyup(function(e) {
		var code = e.keyCode || e.which;
		if (code == '9') { //tab
			focusCitySearchField(e);
		}
	});
	//refreshSpecialtiesBox({id: city_select_code}, '', '#id_modality3');
	function run_search_if_get_params_not_equal_to_form_input(){
		var initial_modality_code = get_modality_code(getUrlParameter('modality_id'), getUrlParameter('modality_category_id'));
		var current_modality_code = $('#id_modality3').val();

		if (initial_modality_code !== current_modality_code) {
			$('#healers_form').trigger('changed');
		}
	}
	run_search_if_get_params_not_equal_to_form_input();
});