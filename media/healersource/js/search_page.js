var link=true;
var search_results_infinite_scroll;
var search_results_display_type = 'list';

function updateLinks() {
	$('.modality_link').unbind();
	$('.modality_link').mouseover(function() {link=false;});
	$('.modality_link').mouseout(function() {link=true;});
	$('.recommendations_link').unbind();
	$('.recommendations_link').mouseover(function() {link=false;});
	$('.recommendations_link').mouseout(function() {link=true;});
	$('.reviews_link').unbind();
	$('.reviews_link').mouseover(function() {link=false;});
	$('.reviews_link').mouseout(function() {link=true;});

	if (!phonegap) {
		$('.search_results_provider').unbind();
		$('.search_results_provider').click(function(e) {
			if (!e.isTrigger) {
				if(link) {
					if(embed_user) {
						$(this).prev().prev().attr('target', '_blank');
						$(this).prev().prev()[0].click();
					} else {
						if(is_smallscreen()) {
							document.location.href = $(this).prev().prev().attr('href');
						} else {
							$(this).prev().trigger('click');
						}
					}
				}
			}
		});
	}
}

function updateReadMore() {
	if(is_smallscreen()) {
		$('.search_results_provider .about_cell > div').each(function() {
			if($(this).outerHeight() > 70) {
				$(this).css('height', '70px');
				$('.read_more_link', $(this).parent()).show();
			}
		});
	} else {
		$('.search_results_provider .about_cell > div').css('height', 'auto');
		$('.read_more_link').hide();
	}
}

$(window).resize(updateReadMore);

function concierge_popup() {
	hs_dialog($("#concierge"), {
		autoOpen: true,
		fixed_width: 770,
	});
}

var search_results_updated = function(){
	if (phonegap) {
		phonegap_fix_urls();
	}
	updateLinks();
	updateReadMore();
	fb.activate();
	activate_gallery();
};

$(function() {
	updateLinks();
	updateReadMore();
	activate_gallery();

	$.endlessPaginate({
		paginateOnScroll: true,
		onCompleted: function() {
			$('#search_results').trigger('updated');
		}
	});

	$('#search_results').bind('updated', search_results_updated);

	modality_code = get_modality_code(modality_id, modality_category_id);
	var city = $('.search_city_or_zipcode').val();
	if (city !== '') {
		refreshSpecialtiesBox({id: city_select_code}, modality_code, '#id_modality3');
	} else {
		$('#id_modality3').val(modality_code).select2();
	}

	var specialty = $('#id_modality3').val();
	if($('#search_results .friends').length === 0 &&
			$('#search_results .message').length === 0 &&
				(city || specialty)) {
		$('#healers_form').trigger('changed');
	}

	if (is_concierge_found) {
		concierge_popup();
	}
	if (remote_sessions) {
		$('#id_search_city_or_zipcode').val('Phone, Online, Skype, or Distance Sessions');
	}
});