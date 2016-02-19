var items = {};

function set_visibility(id, is_hidden){
	var set_visibility_callback = function(){
		function reload_gallery(){
			var item_list = [];
			for (var i in items) {
				item_list.push(items[i]);
			}
			item_list.sort(function (a, b) {
				return a.data('order') - b.data('order');
			});
 			$('.gallery_box').empty();

			item_list.forEach(function(x){
				if (!x.data('hidden')) {
					$('.gallery_box').append(x.clone());
				}
			});
			fb.activate();
		}
		var text, opacity, hidden;
		if (is_hidden) {
			text = 'Show';
			opacity = '0.5';
			hidden = '1';
			items[id].data('hidden', true);
			$('.gallery-item[data-id=' + id + ']').remove();
		} else{
			text = 'Hide';
			opacity = '1';
			hidden = '0';
			items[id].data('hidden', false);
			reload_gallery();
		}
		$('.visibility[data-id=' + id + ']').html(text).data('hidden', hidden);
		$('.gallery_avatar[data-id=' + id + ']').css('opacity', opacity);
	}
	rest_ajax_post_request_no_timeout([url_gallery, id, 'set_visibility'], set_visibility_callback,
		{is_hidden: is_hidden}
	);
}

$(function() {
	$('.item_order').change(function() {
		var order = $(this).val(),
				gallery_id = $(this).closest('.item').data('item_id');
		$('#change_order_form [name=order]').val(order);
		$('#change_order_form [name=gallery_id]').val(gallery_id);
		$('#change_order_form').submit();
	});
	activate_gallery(true);
	$('.visibility').click(function(){
		set_visibility($(this).data('id'), $(this).data('hidden') != '1');
	});

	$('.gallery-item').each(function(){
		items[$(this).data('id')] = $(this).clone();
	});

	$('.gallery-item[data-hidden=true]').remove();
});
