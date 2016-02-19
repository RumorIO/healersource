$(function(){
	$('#clients_visible_to_providers').click(function(){
		var url;
		if ($(this).is(':checked')){
			url = url_enable_clients_visible_to_providers;
		} else {
			url = url_disable_clients_visible_to_providers;
		}
		window.location.href = url;
	});
});