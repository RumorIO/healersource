function newClientSuccess(client) {}

function newClientFailure(timeout_id, msg) {
	if(typeof msg == 'undefined') {
		hs_dialog('#new_client_dialog', 'open');
	} else {
		showResult(msg);
	}
}