function show_contact_us_dlg(){
	var form = $('#contact_us_form');
	hs_dialog($('#contact_us_dlg'), {
		fixed_width: 420,
		title: 'Contact Us',
		title_class: 'nav_inbox',
		buttons: {
			Send: function(){
				if (!form.valid()) {
					return;
				}
				rest_ajax_post_request_long_timeout(url_contact_us, function(){
					hs_dialog('close');
					showSuccess('Thank you for contacting us.');
				}, {data: form.serialize()});
			}
		}
	});
}

jQuery.extend(
	jQuery.expr[ ':' ],
	{ reallyVisible: function (element) { return element.isVisible(); }}
);

jQuery.extend(
	jQuery.expr[ ':' ],
	{ reallyHidden: function (element) { return !element.isVisible(); }}
);

$.fn.random = function() {
	return this.eq(Math.floor(Math.random() * this.length));
}

var Rotation = function() {
	this.id = 0;
	this.counter = 0;
	this.initRotation();
};

Rotation.prototype = {
	initRotation: function() {
		var that = this;
		this.id = setInterval(function(){return that.rotateAvatar();}, 3500);
	},
	rotateAvatar: function(){
		function get_class_name(previous_n) {
			// previous_n - number of previous class names requesting
			previous_n = typeof previous_n !== 'undefined' ? previous_n : 0;
			counter = that.counter - previous_n;
			return 'rotation_' + that.id + '_' + counter;
		}
		var that = this;
		this.counter++;
		$('.' + get_class_name(2)).removeClass('rotation_blocked');
		var old_avatar = $('.avatar_image:reallyVisible').not('.rotation_blocked').random();
		var new_avatar = $('.avatar_image:reallyHidden').last();
		new_avatar.insertAfter(old_avatar).hide();
		new_avatar.addClass(get_class_name());
		new_avatar.addClass('rotation_blocked');
		old_avatar.fadeOut(1500, function(){
			new_avatar.fadeIn(1500);
		});
	}
};

$(function(){
	function enable_contact_us_form_validation(){
		$('#contact_us_form').validate({
			rules: {
				email: {
					required: true,
					email: true
				},
				name: 'required'
			}
		});
	}

	enable_contact_us_form_validation();

	new Rotation();
	setTimeout(function(){new Rotation();}, 1600);
	setTimeout(function(){new Rotation();}, 3800);
});

