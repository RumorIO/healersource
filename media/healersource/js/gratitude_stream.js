function post_comment(element, post_id){
	var comment_div = $(element).parent();
	var comment = comment_div.find('#comment_text').val();
	if (!comment) {return;}
	rest_ajax_post_request([url_comment, post_id],
		function(data){
			$('#post_' + post_id + '_comments').prepend(data.html);
			comment_div.remove();
		}, {
		comment: comment,
	});
}

$(function(){
	function get_posting_id(element){
		return element.parent().data('id');
	}

	function get_posting_type(element){
		return element.parent().data('type');
	}

	$('#post').click(function(){
		var text = $('#text').val();
		if (!text) {return;}
		rest_ajax_post_request([url_post, 1],
			function(data){
				$('#posts').prepend(data.html);
			}, {
			text: text,
		});
	});

	$('.add_comment').click(function(){
		if ($('#comment_posting').length === 0) {
			var id = get_posting_id($(this));
			var html = '<div id="comment_posting"><textarea id="comment_text"></textarea><input type="button" onclick="post_comment(this, ' + id + ')" value="Post Comment"/></div>';
			$(this).parent().append(html);
		}
	});

	$('.like').click(function(){
		var that = $(this);
		var posting_id = get_posting_id(that);
		var posting_type = get_posting_type(that);
		rest_ajax_post_request([url_like, posting_type, posting_id],
			function(likes){
				$('#posting_' + posting_id + '_likes').html(likes);
				that.remove();
			});
	});

	$('.report').click(function(){
		var that = $(this);
		var posting_id = get_posting_id(that);
		var posting_type = get_posting_type(that);
		rest_ajax_post_request([url_report, posting_type, posting_id],
			function(){
				that.remove();
			});
	});
});
