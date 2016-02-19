function confirm_appointment_delete(id, start) {
	if (confirm('Are you sure you want to delete this appointment?')) {
		window.location.href = url_appointment_delete + id + '/' + start + '/?redirect=' + current_url;
	}
}