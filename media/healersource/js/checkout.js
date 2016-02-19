function stripe_checkout(data, panel_label, closed_callback, email, stripe_checkout_callback, amount, description, key){
	panel_label = typeof panel_label !== 'undefined' ? panel_label : 'Checkout';
	email = typeof email !== 'undefined' ? email : false;
	amount = typeof amount !== 'undefined' ? amount : false;
	description = typeof description !== 'undefined' ? description : false;
	key = typeof key !== 'undefined' ? key : stripe_public_key;
	stripe_checkout_callback = typeof stripe_checkout_callback !== 'undefined' ? stripe_checkout_callback : checkout_callback;
	settings = {
		key: key,
		panelLabel: panel_label,
		name: 'Healersource',
		token: function(res) {
			stripe_checkout_callback(res.id, data);
		},
		image: static_url + 'healersource/img/hs_logo_stripe.png',
		closed: closed_callback,
	};
	if (email) {
		settings.email = email;
	}
	if (amount) {
		settings.amount = parseInt(amount * 100);
	}
	if (description) {
		settings.description = description;
	}

	StripeCheckout.open(settings);
}
