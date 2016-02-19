from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from about.views import SearchAjax, CitySelectCode, FeaturedProviders, GeoSpecialties, ContactUs


urlpatterns = patterns(
	'about.views.homepage',
	url(r'^$', 'front_page', name='front_page'),
	url(r'^home/$', 'homepage', name='home'),
)

urlpatterns += patterns(
	'about.views',
	url(r'^wcenter/', 'wcenter', name='wellness_center_list'),
	url(r'^concierge/(?P<username>[\w\._-]+)/thanks', 'concierge_thanks', name='concierge_thanks'),

	url(r'^search_ajax', SearchAjax.as_view(), name='search_ajax'),
	url(r'^city_select_code', CitySelectCode.as_view(), name='search_city_select_code'),
	url(r'^featured_providers', FeaturedProviders.as_view(), name='featured_providers'),
	url(r'^geo_specialties', GeoSpecialties.as_view(), name='geo_specialties'),
	url(r'^contact_us', ContactUs.as_view(), name='contact_us'),
	url(r"^report_error/$", "error_report", name="report_error"),

	url(r'^search/infinite/grid/', 'search', {'template_name': 'about/search/results_grid.html'},
		name='search_infinite_grid'),

	url(r'^learn/blog/infinite/', 'learn', name='learn_blog_infinite', kwargs={'only_posts': True}),
	url(r"^featured/$", "featured", name="featured"),
	url(r"^learn/$", "learn", name="learn"),
	url(r"^pricing/$", "pricing", name="pricing"),
	url(r'^tour/$', 'tour', name='tour'),
	url(r'^what_next/$', 'what_next', name='what_next'),
	url(r'^search/(?P<modality>[0-9]+)$', 'search', name='search_modality'),
	url(r'^stats/$', 'search', {'all': 'True'}, name='stats'),
	url(r'^all/healers$', 'all_users', {'healers_only': 'True'}, name='all_healers'),
	url(r'^all/boston$', 'all_users', {'healers_only': 'True', 'boston': 'True'}, name='all_boston'),
	url(r'^all/users$', 'all_users', name='all_users'),

	url(r'^search/$', 'search', name='search_results'),
	url(r'^search/(?P<city>[&\w\s_\-]+)_(?P<state>[\w]{2})/$', 'search', name='search_seo_city2'),
	url(r'^search/(?P<city>[&\w\s_\-]+)/$', 'search', name='search_seo_city'),
	url(r'^search/(?P<city>[&\w\s_\-]+)_(?P<state>[\w]{2})/(?P<specialty>[&\w\W\s_\-]+)/$', 'search', name='search_seo_city_specialty2'),
	url(r'^search/(?P<city>[&\w\s_\-]+)/(?P<specialty>[&\w\W\s_\-]+)/$', 'search', name='search_seo_city_specialty'),

)

urlpatterns += patterns(
	'',
	url(r'^robots\.txt$',
		TemplateView.as_view(template_name='about/robots.txt'),
		name='robots'),

	url(r'^terms_of_service/$',
		TemplateView.as_view(template_name='about/terms.html'),
		name='terms'),

	url(r'^hipaa/$',
		TemplateView.as_view(template_name='about/hipaa.html'),
		name='hipaa'),

	url(r'^hipaa_content/$',
		TemplateView.as_view(template_name='about/hipaa_content.html'),
		name='hipaa_content'),

	url(r'^privacy/$',
		TemplateView.as_view(template_name='about/privacy.html'),
		name='privacy'),

	url(r'^bad_browser/$',
		TemplateView.as_view(template_name='about/bad_browser.html'),
		name='bad_browser'),

	url(r'^schedule_spa/$',
		TemplateView.as_view(template_name='about/schedule_promo_wcenter.html'),
		name='schedule_promo_wcenter'),

	url(r'^partners/$',
		TemplateView.as_view(template_name='about/partners.html'),
		name='partners'),

)


#	url(r'^waitinglist_success/$', direct_to_template, {
#        'template': 'waitinglist/success.html',
#    }, name='waitinglist_success'),
#    url(r'^$', direct_to_template, {
#        'template': 'homepage.html',
#    }, name='home'),
#    url(r'^about/', include('about.urls')),

#    url(r"^$", direct_to_template, {"template": "about/about.html"}, name="about"),
#    url(r"^terms/$", TemplateView.as_view(template_name="about/terms.html"), name="terms"),
#    url(r"^privacy/$", TemplateView.as_view(template_name="about/privacy.html"), name="privacy"),
#    url(r"^dmca/$", direct_to_template, {"template": "about/dmca.html"}, name="dmca"),
#    url(r"^what_next/$", login_required(direct_to_template), {"template": "about/what_next.html"}, name="what_next"),
#    url(r"^what_next/$", "about.views.what_next", name="what_next"),
