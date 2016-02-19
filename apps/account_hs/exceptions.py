class ResetPasswordSeveralEmailsNotVerified(Exception):
	pass


class EmailConfirmationExpiredError(Exception):
	def __init__(self, confirmation):
		self.confirmation = confirmation

	def __str__(self):
		return u'Expired key for ' + str(self.confirmation)
