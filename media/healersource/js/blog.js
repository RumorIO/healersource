function changePostStatus(post_id, status) {
	function blog_process(data) {
		if (data) {
			if ('error' in data){
				showError(data.error);
			}
			if ('post_id_with_error' in data) {
				$('#blog_post_status_' + data.post_id_with_error).find('span').toggleClass('selected');
			}
		}
	}
	rest_ajax_post_request_long_timeout(
		[url_change_post_status, post_id, 'status', status], blog_process);
}
