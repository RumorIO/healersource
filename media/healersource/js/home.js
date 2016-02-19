var PROVIDER_INTERVAL_SHORT = 6000;
var PROVIDER_INTERVAL_LONG = 11000;
var PROVIDER_INTERVAL_CURRENT = PROVIDER_INTERVAL_SHORT;
var CONTENTS_INTERVAL = 10000;
var manually_stopped = false;
var intervals = {};
var rotation_count = {};

function shiftItemLeft(container_class, easing, options_hide, option_show) {
	var first_item = $(container_class + ' > div.rotate:visible').first();
	var prev_item = first_item.prev();
	if (prev_item.length) {
		prev_item = first_item.prev();
	} else {
		prev_item = $(container_class + ' > div.rotate:hidden').last();
	}
	first_item.hide(easing, options_hide, function() {
		prev_item.show(easing, option_show);
		prev_item.trigger('fadein');
	});
}

function startInterval(container_class, delay, easing, options_hide, options_show, count) {
	if(!intervals[container_class]) {
		if($(container_class + ' > div.rotate').length > 1) {
			rotation_count[container_class] = 0;
			var interval = setInterval(function() {
				rotateItems(container_class, easing, options_hide, options_show, count);
			}, delay);
			intervals[container_class] = interval;
		}
	}
}

function stopInterval(container_class) {
	if(intervals[container_class]) {
		clearInterval(intervals[container_class]);
		intervals[container_class] = null;
	}
}

function startProvidersInterval(interval) {
	PROVIDER_INTERVAL_CURRENT = interval;
	startInterval('.providers', interval, 'fade', {}, {});
	$('#arrows_play_pause').html('||');
}

function stopProvidersInterval() {
	stopInterval('.providers');
	$('#arrows_play_pause').html('&#9658;');
}

function startContentsInterval() {
	if(rotation_count['.contents'] == 6)
		return;

	startInterval('.contents', CONTENTS_INTERVAL, 'slide', {direction: 'left'}, {direction: 'right'}, 6);
}

function stopContentsInterval() {
	stopInterval('.contents');
}

function resumeBothIntervals() {
	if(start_intervals) {
//		rotateItems('.providers', 'fade', {}, {});
		startContentsInterval();
		startProvidersInterval(PROVIDER_INTERVAL_CURRENT);
	}
}

function changeContent(id) {
	$('.buttons a').removeClass('selected');
	$('.contents > .content').hide();
	$('#'+id).show();
}

function selectButton(id) {
	$('.buttons a').removeClass('selected');
//    $('.buttons a[href=#tab_'+id+']').addClass('selected');
	$('.buttons .'+id).addClass('selected');
}

$(function() {
	function updateFeaturedProviders(html) {
		if(html) {
			$('.providers > div').after(html);
			fb.activate();
			$('.provider').click(function() {
				stopProvidersInterval();
				stopContentsInterval();
			});
			startProvidersInterval(PROVIDER_INTERVAL_SHORT);
		}
	}

	$('.buttons a').click(function(e) {
        var href = $(this).attr('href');
        if (href.indexOf('/') == -1) {
            var id = href.substr(5);
            changeContent(id);
            selectButton(id);
            e.preventDefault();
        }
	});
	$('.content').on('fadein', function() {
		selectButton($(this).attr('id'));
	});
//	$('.left').click(stopProvidersInterval);
	$('.right').click(function() {
		stopContentsInterval();

		if((PROVIDER_INTERVAL_CURRENT != PROVIDER_INTERVAL_LONG) && !manually_stopped) {
			stopProvidersInterval();
			startProvidersInterval(PROVIDER_INTERVAL_LONG);
		}
	});
	$('.provider').click(function() {
		stopProvidersInterval();
		stopContentsInterval();
	});
	$(window).scroll(function() {
		if($(window).scrollTop()) {
			stopContentsInterval();

			if(PROVIDER_INTERVAL_CURRENT != PROVIDER_INTERVAL_LONG) {
				stopProvidersInterval();
				startProvidersInterval(PROVIDER_INTERVAL_LONG);
			}
		}
	});

	if(window.location.hash) {
		var id = window.location.hash.substr(5);
		if($('#'+id).length) {
			changeContent(id);
			selectButton(id);
			start_intervals = false;
			$('#arrows_container').hide();
		}
	}

	if(start_intervals && !is_smallscreen()) {
		startContentsInterval();
		if(FeaturedProviders.length) {
			rest_ajax_get_request_long_timeout(url_featured_providers, updateFeaturedProviders, {
				featured_providers: JSON.stringify(FeaturedProviders)
			});
		}
	} else {
		$('#arrows_container').hide();
	}

    // var $healers_form = $('#healers_form');
	// var city = $healers_form.find('.search_city_or_zipcode').val();
//	var specialty = $healers_form.find('.modality_input').val();
	// if(city) {
	// 	$('#healers_form').trigger('changed');
	// }

	$('#arrows_play_pause').on('click', function() {
		if ($(this).html() != '||') {
			rotateItems('.providers', 'fade', {}, {});
			startProvidersInterval(PROVIDER_INTERVAL_CURRENT);
			manually_stopped = false;
		} else {
			stopProvidersInterval();
			manually_stopped = true;
		}
		return false;
	});

	$('#arrows_right').on('click', function() {
		stopProvidersInterval();
		rotateItems('.providers', 'fade', {}, {});
		return false;
	});

	$('#arrows_left').on('click', function() {
		stopProvidersInterval();
		shiftItemLeft('.providers', 'fade', {}, {});
		return false;
	});

    $('#quick_links_homepage .cities a').on('click', function(e) {
        var code = $(this).data('code'),
            $ql = $('#quick_links_homepage');
        $ql.find('.highlight_container span').removeClass('selected');
        $(this).parent().toggleClass('selected');

        $ql.find('.quick_links_catmod').hide();
        $ql.find('#cat_' + code).show();
        $ql.find('#mod_' + code).show();

        return e.preventDefault();
    });

    // healing requests
	$("#accordion").accordion({
		collapsible: true,
		heightStyle: 'content'
	});

});
