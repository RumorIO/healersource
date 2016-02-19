from django.conf.urls import patterns, url

urlpatterns = patterns("review.views",
	url(r"^$", "review_list", name="review_list"),
	url(r"^(?P<username>[\w\._-]+)$", "review_list", name="review_list"),
	url(r"^(?P<username>[\w\._-]+)/embed/$", "review_list", name="review_list_embed", kwargs={"template_name": "review/review_embed.html", 'embed': True}),
	url(r"^(?P<username>[\w\._-]+)/popup/$", "review_list", name="review_list_popup", kwargs={"template_name": "review/review_list_content.html"}),
	url(r"^(?P<username>[\w\._-]+)/form/$", "review_form", name="review_form"),
	url(r"^(?P<username>[\w\._-]+)/form/success/$", "review_form_success", name="review_form_success"),
	url(r"^(?P<username>[\w\._-]+)/signup/$", "review_signup", name="review_signup"),
)