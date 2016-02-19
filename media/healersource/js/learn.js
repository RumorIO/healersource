$(function(){
	$('.learn').addClass('selected');

	$.ias({
		history: false,
		container: '.blog_post_list',
		item: '.blog_post',
		pagination: '.blog_pagination',
		next: '.blog_pagination .next',
		base_url: BlogInfiniteUrl,
		loader: '<img src="'+STATIC_URL+'infinite_scroll/images/loader.gif"/>',
		onRenderComplete: function() {
			fb.activate();
		}
	});
});