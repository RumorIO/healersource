function submit_search_form(){
	if($('input[name="search_city_or_zipcode"]').val() == 'Phone, Online, Skype, or Distance Sessions'){
		$('input[name="remote_sessions"]').val(1);
	}
	$('#search_form').submit();
}

$(function () {
	$('#id_modality2').change(function () {
		update_modality_hidden_ids($('#id_modality2'));
		if ($('.search_city_or_zipcode').val() !== '') {
			submit_search_form();
		}
	});

	$('#id_modality3').change(function (e) {
		update_modality_hidden_ids($('#id_modality3'));
		updateSearchResults(e);
	});
});

function update_modality_hidden_ids($select2) {
	var node;
	var slct_val = $select2.val();
	if ($select2.val()){
		var vals = slct_val.split(':');
		node = vals[0];
		var node_id = vals[1];
	}

	var container = $select2.parent().parent();
	var $modality_category_id_hidden = $('#modality_category_id_hidden', container);
	var $modality_id_hidden = $('#modality_id_hidden', container);
	// modality = $select2.find('option:selected').text(),
	$modality_category_id_hidden.val('');
	$modality_id_hidden.val('');

	if (node == 'p')
		$modality_category_id_hidden.val(node_id);
	else if (node == 'c')
		$modality_id_hidden.val(node_id);
}
