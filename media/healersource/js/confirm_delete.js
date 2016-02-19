function confirm_delete() {
	if (confirm('Are you really really really really really sure? ' +
			'You can always reactivate your account later - just contact us.')) {
		window.location.href = url_delete_account;
	}
}