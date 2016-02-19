//DO NOT REMOVE. TEMPRORARILY COMMENTED OUT FUNCTIONALITY
// function activate_how_did_you_find_buttons(){
// 	$('#how-you-find-us span').click(function(){
// 		$button = $(this);
// 		rest_ajax_post_request(url_ajax_update_link_source, function(){
// 			$button.parent().html('Thanks for you answer!');
// 		}, {link_source: $button.data('link-source'),
// 			email: email});
// 	});
// }

$(function(){
	// activate_how_did_you_find_buttons();
	$('.email').html(email);
});