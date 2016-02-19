var intervals = {};
function rotateItems(container_class, delay) {
	var first_item = $(container_class + ' > div:visible').first();
	var next_item = $(container_class + ' > div:visible + div:hidden').first();
	if(next_item.length) {
		next_item = next_item.first();
	} else {
		next_item = $(container_class + ' > div:hidden').first();
	}
	first_item.fadeOut(function() {
		next_item.fadeIn();
		first_item.appendTo($(container_class));
	});
}
function startIntervals() {
	var interval;
	if(!intervals['.featured_articles']) {
		if($('.featured_articles > div').length > 3) {
			interval = setInterval(function() {rotateItems('.featured_articles', 8000);}, 8000);
			intervals['.featured_articles'] = interval;
		}
	}
	if(!intervals['.videos_rotate_container']) {
		if($('.videos_rotate_container > div').length > 2) {
			interval = setInterval(function() {rotateItems('.videos_rotate_container', 6000);}, 6000);
			intervals['.videos_rotate_container'] = interval;
		}
	}
}
function stopIntervals() {
	for(var key in intervals) {
		if(intervals[key]) {
			clearInterval(intervals[key]);
			intervals[key] = null;
		}
	}
}
$(function() {
	startIntervals();
});