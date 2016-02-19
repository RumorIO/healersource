from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from collections import OrderedDict

from account_hs.authentication import user_authenticated
from healers.models import Healer, is_my_client
from healers.views import friend_process
from clients.models import Client

from review.models import Review
from review.forms import ReviewForm


def review_list(request, username=None, template_name="review/review_list.html", embed=False):
	if username:
		healer = get_object_or_404(Healer, user__username__iexact=username)
	else:
		if request.user.is_authenticated():
			healer = get_object_or_404(Healer, user=request.user)
		else:
			raise Http404
	if request.user != healer.user and healer.review_permission == Healer.VISIBLE_DISABLED:
		raise Http404

	reviews = healer.reviews.all().order_by('-date')
	reviews_by_rating = {5: [], 4: [], 3: [], 2: [], 1: []}
	for review in reviews:
		reviews_by_rating[review.rating].append(review)

	reviews_by_rating = OrderedDict(sorted(reviews_by_rating.items(), key=lambda x: x[0], reverse=True))

	return render_to_response(template_name,
		{
			"healer": healer,
			"reviews": reviews_by_rating,
			"review_active_id": request.GET.get('id', 0),
			"tab_id": request.GET.get('tab_id', -1),
			"is_review_permission": healer.is_review_permission(request.user),
			"review_exist": healer.reviews.filter(reviewer__user=request.user).count() if request.user.is_authenticated() else False,
			'embed': embed,
		},
		context_instance=RequestContext(request))


def review_signup(request, username):
	healer = get_object_or_404(Healer, user__username__iexact=username)

	request.session['message'] = 'You have to Sign Up before leaving a review for %s' % healer.user.client
	request.session['signup_next'] = reverse('review_form', args=[username])
	request.session['signup_healer'] = username
	return redirect(reverse('signup'))


@user_authenticated
def review_form(request, username, template_name="review/review_form.html"):
	healer = get_object_or_404(Healer, user__username__iexact=username)
	if not healer.is_review_permission(request.user):
		raise Http404

	reviewer = get_object_or_404(Client, user=request.user)
	try:
		review = Review.objects.filter(healer=healer, reviewer=reviewer)[0]
		notify = False
		title = 'Edit My Review for '
	except IndexError:
		review = None
		notify = True
		title = 'Write a Review for '
	title += str(healer.user.client)
	prev_rating = review.rating if review else None

	fb = request.GET.get('fb', False)
	if fb:
		template_name = "review/review_fb_form.html"

	form = ReviewForm(request.POST or None, instance=review)
	if form.is_valid():
		review = form.save(commit=False)
		review.healer = healer
		review.reviewer = reviewer
		review.save()
		if notify:
			review.notify()
		healer.update_rating(review.rating, prev_rating)
		if healer.review_permission == Healer.VISIBLE_EVERYONE and not is_my_client(healer.user, request.user):
			friend_process(request, 'clients', healer.user.id, 'invite')

		return redirect(reverse('review_form_success', args=[healer.user.username]) + ('?fb=1' if fb else ''))

	return render_to_response(template_name,
		{
			"title": title,
			"healer": healer,
			"form": form,
			"fb": fb
		},
		context_instance=RequestContext(request))


@user_authenticated
def review_form_success(request, username, template_name="review/review_form.html"):
	healer = get_object_or_404(Healer, user__username__iexact=username)
	if not healer.is_review_permission(request.user):
		raise Http404

	if request.GET.get('fb', False):
		template_name = "review/review_fb_form.html"

	return render_to_response(template_name,
		{
			"title": "Review",
			"healer": healer,
			"success": True
		},
		context_instance=RequestContext(request))
