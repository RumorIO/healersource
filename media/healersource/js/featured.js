$(function(){
	$('.featured').addClass('selected');

	search_results_infinite_scroll = $.ias({
		history: false,
		container: '.friends',
		item: '.grid_box',
		pagination: '.search_results_pagination',
		next: '.search_results_pagination .next',
		base_url: HealersInfiniteUrl,
		loader: '<img src="'+STATIC_URL+'infinite_scroll/images/loader.gif"/>',
		onRenderComplete: function() {
			fb.activate();
		}
	});
	$('#search_results').bind('updated', function() {
		fb.activate();
	});
	initCitySearchAutocomplete();
});