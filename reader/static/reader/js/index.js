$(document).ready(function() {
    $('.register-screen').hide();
    $('#register-link').click(function() {
	$('.login-screen').hide();
	$('.register-screen').show();
    });
    $('#login-link').click(function() {
	$('.login-screen').show();
	$('.register-screen').hide();
    });
    $('.register-screen input[type=password]').change(function() {
	if ($('#register-password').val() === $('#repeat-password').val()) {
	    $('#register-submit').removeClass('disabled');
	} else {
	    $('#register-submit').addClass('disabled');
	}
    });
});