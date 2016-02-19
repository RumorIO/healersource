from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from mezzanine.core.models import CONTENT_STATUS_PUBLISHED, CONTENT_STATUS_DRAFT
from mezzanine.blog.models import BlogPost as Post
from rest_framework.response import Response

from account_hs.views import UserAuthenticated
from account_hs.authentication import user_authenticated
from healers.models import Healer

from blog_hs.utils import post_quality
from blog_hs.forms import (ImportRssForm, ImportWordpressForm, ImportBloggerForm,
	ImportTumblrForm, BlogForm)


if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None
try:
	from friends.models import Friendship
	friends = True
except ImportError:
	friends = False


def blogs(request, username=None, template_name="blog/blogs.html"):
	blogs = Post.objects\
		.filter(status=CONTENT_STATUS_PUBLISHED)\
		.filter(user__avatar__isnull=False)\
		.filter(user__client__healer__profileVisibility=Healer.VISIBLE_EVERYONE)\
		.select_related()\
		.order_by("-publish_date").distinct()
	user = None
	if username is not None:
		user = get_object_or_404(User, username__iexact=username)
		blogs = blogs.filter(user=user)
	return render_to_response(template_name, {
		"blog_user": user,
		"blogs": blogs,
	}, context_instance=RequestContext(request))


def post(request, username=None, year=None, month=None, slug_id=None, slug=None,
			day=None, template_name="blog/post.html"):
	if not slug and not slug_id:
		raise Http404
	if slug:
		post = get_object_or_404(Post, slug=slug)
	else:
		post = get_object_or_404(Post, id=slug_id)
	#        slug = slug,
	#        publish__year = int(year),
	#        publish__month = int(month),
	#        author__username = username
	#    )
	if not post:
		raise Http404

	if post.status == CONTENT_STATUS_DRAFT and post.user != request.user:
		raise Http404

	return render_to_response(template_name, {
		"post": post,
		}, context_instance=RequestContext(request))


@user_authenticated
def publish_all(request):
	posts = Post.objects.filter(user=request.user, status=CONTENT_STATUS_DRAFT)

	for p in posts:
		if post_quality(p.content):
			p.status = CONTENT_STATUS_PUBLISHED
			p.save()

	return HttpResponseRedirect(reverse('blog_list_yours'))


@login_required
def blog_import(request, import_type=None, template_name="blog/import.html",
		setup=False, extra_context={}):
	error = False
	current_form = None
	rss_form = ImportRssForm()
	wordpress_form = ImportWordpressForm()
	blogger_form = ImportBloggerForm()
	tumblr_form = ImportTumblrForm()
	if import_type == "rss":
		rss_form = ImportRssForm(request.POST or None)
		current_form = rss_form
	elif import_type == "wordpress":
		wordpress_form = ImportWordpressForm(request.POST or None, request.FILES or None)
		current_form = wordpress_form
	elif import_type == "blogger":
		blogger_form = ImportBloggerForm(request.POST or None)
		current_form = blogger_form
	elif import_type == "tumblr":
		tumblr_form = ImportTumblrForm(request.POST or None)
		current_form = tumblr_form

	if current_form:
		if current_form.is_valid():
			error = current_form.save(request)
			if error and type(error) == bool:
				error = "Could not import your blog, please try again."
		else:
			error = current_form.errors

	if import_type and not error:
		if setup:
			return HttpResponseRedirect(reverse("provider_setup", args=[8]))
		else:
			return HttpResponseRedirect(reverse("blog_list_yours"))

	return render_to_response(template_name, dict({
		'error': error,
		'rss_form': rss_form,
		'wordpress_form': wordpress_form,
		'blogger_form': blogger_form,
		'tumblr_form': tumblr_form,
		'setup': setup
	}, **extra_context), context_instance=RequestContext(request))


@user_authenticated
def your_posts(request, template_name="blog/your_posts.html"):
	return render_to_response(template_name, {
		"blogs": Post.objects.filter(user=request.user),
		}, context_instance=RequestContext(request))


@user_authenticated
def destroy(request, id):
	post = Post.objects.get(pk=id)
	title = post.title
	if post.user != request.user:
		messages.add_message(request, messages.ERROR,
			ugettext("You can't delete posts that aren't yours")
		)
		return HttpResponseRedirect(reverse("blog_list_yours"))

	#    if request.method == "POST" and request.POST["action"] == "delete":
	post.delete()
	messages.add_message(request, messages.SUCCESS,
		ugettext("Successfully deleted post '%s'") % title
	)
	return HttpResponseRedirect(reverse("blog_list_yours"))
#    else:
#        return HttpResponseRedirect(reverse("blog_list_yours"))

#return render_to_response(context_instance=RequestContext(request))


@user_authenticated
def new(request, form_class=BlogForm, template_name="blog/new.html"):
	if request.method == "POST":
		if request.POST["action"] == "create":
			blog_form = form_class(request.user, request.POST)
			if blog_form.is_valid():
				blog = blog_form.save(commit=False)
				blog.user = request.user
				if getattr(settings, 'BEHIND_PROXY', False):
					blog.creator_ip = request.META["HTTP_X_FORWARDED_FOR"]
				else:
					blog.creator_ip = request.META['REMOTE_ADDR']
				blog.save()
				# @@@ should message be different if published?
				messages.add_message(request, messages.SUCCESS,
					ugettext("Successfully saved post '%s'") % blog.title
				)
				if notification:
					if blog.status == CONTENT_STATUS_PUBLISHED:  # published
						if friends:  # @@@ might be worth having a shortcut for sending to all friends
							notification.send((x['friend'] for x in Friendship.objects.friends_for_user(blog.author)), "blog_friend_post", {"post": blog})

				return HttpResponseRedirect(reverse("blog_list_yours"))
		else:
			blog_form = form_class()
	else:
		blog_form = form_class()

	return render_to_response(template_name, {
		"blog_form": blog_form
	}, context_instance=RequestContext(request))


@user_authenticated
def edit(request, id, form_class=BlogForm, template_name="blog/edit.html"):
	post = get_object_or_404(Post, id=id)

	if request.method == "POST":
		if post.user != request.user:
			messages.add_message(request, messages.ERROR,
				ugettext("You can't edit posts that aren't yours")
			)
			return HttpResponseRedirect(reverse("blog_list_yours"))
		if request.POST["action"] == "update":
			blog_form = form_class(request.user, request.POST, instance=post)
			if blog_form.is_valid():
				blog = blog_form.save(commit=False)
				blog.save()
				messages.add_message(request, messages.SUCCESS,
					ugettext("Successfully updated post '%s'") % blog.title
				)
				if notification:
					if blog.status == CONTENT_STATUS_PUBLISHED:  # published
						if friends:  # @@@ might be worth having a shortcut for sending to all friends
							notification.send((x['friend'] for x in Friendship.objects.friends_for_user(blog.author)), "blog_friend_post", {"post": blog})

				return HttpResponseRedirect(reverse("blog_list_yours"))
		else:
			blog_form = form_class(instance=post)
	else:
		blog_form = form_class(instance=post)

	return render_to_response(template_name, {
		"blog_form": blog_form,
		"post": post,
		}, context_instance=RequestContext(request))


class ChangePostStatus(UserAuthenticated):
	def post(self, request, post_id, status_id, format=None):
		status_id = int(status_id)
		post = get_object_or_404(Post, id=post_id)
		if post.user != request.user:
			return Response({'error': 'You are not an owner!'})
		else:
			post.status = status_id
			if status_id == CONTENT_STATUS_PUBLISHED:
				if post_quality(post.content):
					post.save()
					return Response()
				else:
					return Response({
						'error': 'Your blog post must be at least 400 characters long to be published.',
						'post_id_with_error': post.pk
					})
			else:
				post.save()
				return Response()
