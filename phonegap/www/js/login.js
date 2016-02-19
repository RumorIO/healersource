$(function(){
	function initiate_login_on_enter_keypress() {
		$('input').bind('enterKey',function(e){
			login();
		});

		$('input').keyup(function(e){
			if(e.keyCode == 13)
			{
				$(this).trigger('enterKey');
			}
		});
	}

	initiate_login_on_enter_keypress();
	// focus($('#id_email'));
});