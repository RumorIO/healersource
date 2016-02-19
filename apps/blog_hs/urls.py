from django.conf.urls import patterns, url

from blog_hs.forms import *
from blog_hs.views import ChangePostStatus


urlpatterns = patterns("",
	# blog post
	url(r"^post/(?P<username>[\w\._-]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<slug_id>[0-9]+)/$", "blog_hs.views.post", name="blog_post"),

	url(r"^post_popup/(?P<username>[\w\._-]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<slug_id>[0-9]+)/$", "blog_hs.views.post", {'template_name': 'blog/post_content.html'}, name="blog_post_popup"),
	# required in mezzanine import and comments
	url(r"^post/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>.*)/$", "blog_hs.views.post", name="blog_post_detail_day"),

	# all blog posts
	url(r"^$", "blog_hs.views.blogs", name="blog_list_all"),

	# blog post for user
	url(r"^posts/(?P<username>[\w\._-]+)/$", "blog_hs.views.blogs", name="blog_list_user"),

	# your posts
	url(r"^your_posts/$", "blog_hs.views.your_posts", name="blog_list_yours"),

	# new blog post
	url(r"^new/$", "blog_hs.views.new", name="blog_new"),

	# edit blog post
	url(r"^edit/(\d+)/$", "blog_hs.views.edit", name="blog_edit"),

	# publish all posts
	url(r"publish/$", "blog_hs.views.publish_all", name="blog_publish_all"),

	#destory blog post
	url(r"^destroy/(\d+)/$", "blog_hs.views.destroy", name="blog_destroy"),

	#import posts
	url(r"import/$", "blog_hs.views.blog_import", name="blog_import"),
	url(r"import/(?P<import_type>\w+)/$", "blog_hs.views.blog_import", name="blog_import"),

	# ajax validation
	(r"^validate/$", "ajax_validation.views.validate", {
		"form_class": BlogForm,
		"callback": lambda request, *args, **kwargs: {"user": request.user}
		}, "blog_form_validate"),

	url("^comment/$", "mezzanine.generic.views.comment", name="comment"),
	url(r"^post/$", 'util.views.page_not_found', name="blog_change_post"),
	url(r"^post/(?P<post_id>[0-9]+)/status/(?P<status_id>1|2)/$", ChangePostStatus.as_view(), name="blog_change_post_status"),
)
