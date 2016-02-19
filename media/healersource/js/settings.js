var schedule_menu;
var treatment_types_menu;
var vacation_menu;

$(function(){
	activate_settings();
	// loading_icon is not showing up without that line
	$('.loading').show().hide();

	select_current_menu_item($('.settings_menu a'));
});

function activate_settings() {
	if (is_wellness_center) {
		// if (username) {
		// 	$('h1.nav_settings').append('Settings for ' + names[username]);
		// }
		treatment_types_menu = initSubmenu('treatment_types_menu');
		vacation_menu = initSubmenu('vacation_menu');
	}
	schedule_menu = initSubmenu('schedule_menu');
	// $('h1.nav_settings').show();
}
