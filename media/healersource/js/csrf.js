$(function() {
	var csrftoken = $.cookie('csrftoken');
	localStorage.setItem('csrftoken', csrftoken);
	$.ajaxSetup({
		crossDomain: false, // obviates need for sameOrigin test
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type)) {
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			}
		}
	});
});
