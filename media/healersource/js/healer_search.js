function update_selected_modality_vars(){
	modality_id = $('#modality_id_hidden').val();
	modality_category_id = $('#modality_category_id_hidden').val();
	modality_code = get_modality_code(modality_id, modality_category_id);
}

var modality_id;
var modality_category_id;

$(function(){
	update_selected_modality_vars();
	if ($('.search_city_or_zipcode').val() !== '') {
		if (!city_select_code) {
			rest_ajax_get_request_long_timeout(url_search_city_select_code, function(data) {
				refreshSpecialtiesBox({id: data}, modality_code, '#id_modality2');
			}, {
				query: JSON.stringify({city: $('#id_city').val(), state: $('#id_state').val()}),
			});
		} else {
			if ($('#id_modality2').length !== 0) {
				refreshSpecialtiesBox({id: city_select_code}, modality_code, '#id_modality2');
			}
		}
	} else {
		$('#id_modality2').val(modality_code).select2();
	}

	$('form:not(#search_form) input').keydown(function(e) {
		if (e.keyCode == 13) {
			$(this).closest('form').submit();
		}
	});

	$('#search_form').submit(function() {
		if ($('input[name="city"]').val() === '') {
			$('input[name="search_city_or_zipcode"]').val('');
		}
	});
});