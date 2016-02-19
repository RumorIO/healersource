var embed = true;

function logout() {
	client_id = "";
	$.ajax({
		url:"/logout/",
		async:true
	});
}