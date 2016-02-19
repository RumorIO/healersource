function activate_color_select(){
	$('.color_box').css('cursor', 'pointer');
	$('.color_box').click(function() {
		$('.color_box').removeClass('color_box_selected');
		$(this).addClass('color_box_selected');
		$('#id_color').val($(this).attr('color'));
	});
}

$(function () {
	activate_color_select();
});