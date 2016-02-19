from django.conf.urls import patterns, url

from friends_app.forms import ContactsJoinInviteRequestForm
from friends_app.views import (CreateJoinInvitation, ConfirmSentJoinInvitation,
								SendInvite)

urlpatterns = patterns("",
#    url(r"^$", "friends_app.views.friends", name="invitations"),
#    url(r"^contacts/$", "friends_app.views.contacts",  name="invitations_contacts"),

	url(r"^create_join_invitation/$", CreateJoinInvitation.as_view(), name="create_join_invitation"),
	url(r"^confirm_sent_join_invitation/$", ConfirmSentJoinInvitation.as_view(), name="confirm_sent_join_invitation"),
	url(r"^send_invite/$", SendInvite.as_view(), name="send_invite"),

	url(r"^accept/(\w+)/$", "friends_app.views.accept_join", name="friends_accept_join"),
	url(r"^accept/(\w+)/intake_form/$", "friends_app.views.accept_join", name="friends_accept_join_intake", kwargs={"intake_form": True}),
	url(r"^invite/$", "friends_app.views.invite", name="invite_to_join"),
	url(r"^invite/postcard/$",
		"friends_app.views.invite",
		kwargs={"template_name": "friends_app/invite_postcard.html", "form_class": ContactsJoinInviteRequestForm},
		name="invite_postcard"),
	url(r"^invite/postcard_review/$",
		"friends_app.views.invite",
		kwargs={"template_name": "friends_app/invite_postcard.html",
			"form_class": ContactsJoinInviteRequestForm, "is_for_review": True},
		name="invite_postcard_review"),
	url(r"^invite/postcard_ambassador/$",
		"friends_app.views.invite",
		kwargs={"template_name": "friends_app/invite_postcard.html",
			"form_class": ContactsJoinInviteRequestForm, "is_for_ambassador": True},
		name="invite_postcard_ambassador"),
	url(r"^invite/provider/$", "friends_app.views.invite", kwargs={"invite_type": "provider"}, name="invite_healer"),
	url(r"^invite/(?P<emails>[\w@\._-]+)/$", "friends_app.views.invite", name="invite_to_join_emails"),
)
