$(document).ready(function() {

	initCitySearchAutocomplete(undefined, true);

	$.endlessPaginate({
		paginateOnScroll: true,
		onCompleted: function() {
			update_scroll_height();
		}
	});

	$("#id_saved").prop("checked", false);


	$("[name='search_specialities']").change(function(val) {
		if ($(this).val() == null) {
			$(this).closest("form").find("[name='only_my_specialities'][value='']").prop("checked", true);
		} else {
			$(this).closest("form").find("[name='only_my_specialities'][value='False']").prop("checked", true);
		}
	});

	$("[name='near_my_location']").change(function() {
		var $this = $(this).closest('form');
		$this.find("input[name='search_city_or_zipcode']").val('');
		$this.find("input[name='zipcode']").val('');
	});

	$("input[name='accept_location']").change(function() {
		var $this = $(this).closest('form');
		if ($(this).not(":checked")) {
 	       $this.find("input[name='search_city_or_zipcode']").val('');
           $this.find("input[name='zipcode']").val('');
        }
    });


	$("input[name='accept_cost_per_session']").change(function() {
		var $this = $(this).closest('form');
		if ($(this).not(":checked")) {
			$this.find("input[name='cost_per_session']").val("");
		}
	});

	$("input[name='cost_per_session']").keyup(function() {
		var $this = $(this).closest('form');
		if ($(this).val().trim().length > 0) {
			$this.find("input[name='accept_cost_per_session']").prop("checked", true);
		}
	});

	update_scroll_height();

	$('#id_security_verification_1').attr('placeholder','Type the letters above')
});

function update_scroll_height() {
	$(".healing_request").each(function() {
		var $healing_request = $(this);
		var $description = $(this).find('.description');
		if ($description.length) {
			if ($description[0].scrollHeight > 300) {
				$description.addClass("limit-height");
			} else {
				$healing_request.find(".remove-limit-height").hide();
			}
		}
	});
}

