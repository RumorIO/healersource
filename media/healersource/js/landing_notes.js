var INTERVAL = 5000;

function rotate_images() {
	var container_class = '.images';
	if($(container_class + ' > div.rotate').length > 1) {
		setInterval(function() {
			rotateItems(container_class, 'fade');
		}, INTERVAL);
	}
}

$(function(){
	function replace_app_links_with_button(){
		var $button_element = $('.start_using_notes_full_btn_container');
		var $button = $button_element.first().clone();
		$button_element.remove();
		$('.dedicated_apps_dlg').after($button);
		$('.dedicated_apps_dlg').remove();
		var start_using_notes_btns = $('.start_using_notes_full_btn_container');
		start_using_notes_btns.show();
		if((start_using_notes_btns.length == 3) && is_mediumscreen())
			start_using_notes_btns[2].remove();
//		$('.footer').next().remove(); // remove additional button
	}

	function enable_app_availability_form_validation(){
		$('#app_availability_form').validate({
			rules: {
				email: {
					required: true,
					email: true
				}
			},
		});
	}

	if (is_mobile_small()){
		$('#dedicated_apps_dlg').appendTo($('.header_left_block')).show();
		$('.features').prepend($('#dedicated_apps_dlg').clone());
		$('.footer').append($('#dedicated_apps_dlg').clone());
	} else if (is_tablet()) {
		$('.dedicated_apps_dlg').clone().insertAfter($('.start_using_notes_full_btn_container'));
	}
	activate_smooth_scrolling();
	if (phonegap) {
		$('.smallscreen_logo').attr('style', 'margin: 0!important');
		$('.smallscreen_logo img').css('border', '0');
		if (is_tablet()){
			replace_app_links_with_button();
		}

		// change learn more link
		$('.start_using_notes_full_btn_container').first().attr('id', 'learn_more');
		$('.learn_more a')[0].href ='#learn_more';
	}

	rotate_images();
	enable_app_availability_form_validation();
	$('.images').click(open_signup_selection_dlg);
});
