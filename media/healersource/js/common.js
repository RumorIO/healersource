$(document).ready(function() {
	$("a.link_form").click(function(e) {
			if ($(this).hasClass("empty_link_form")) { return }
			e.preventDefault();
			var remote=$(this).data("remote"),
				method=$(this).data("method") || "GET",
				url=$(this).attr("href");
			method = method.toUpperCase();
			if (method != "POST" && method != "PUT" && method != "PATCH") {
				method = "GET";
			}
			if (!remote || remote != "true") {
				var params = $(this).data("params");
				if (typeof(params) != "undefined") {
					if (params.trim().length > 1) {
						params = JSON.parse(params);
						for(var key in params) {
							$("#common-form").append("<input type='hidden' name='"+key+"' value='"+params[key]+"'  />");
						}
					}
				}
				$("#common-form").attr("action", url);
				$("#common-form").attr("method", method);
				$("#common-form").submit();
			}
		}
	)
});