import re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string

from client_notes.views import render_notes_home
from send_healing.views import render_ghp_home
from account_hs.forms import LoginFormHS
from account_hs.views import render_signup, render_signup_thanks
from about.views import (render_notes_landing, render_book_thanks,
	render_search, render_error_report)
from sync_hs.context_processors import get_facebook_context
from modality.forms import ModalityForm
from clients.forms import RemoteSessionsForm, AboutClientForm
from healers.forms import LocationForm, HealerOptionalInfoForm

from phonegap.utils import get_phonegap_version, template_as_string


class Command(BaseCommand):

	help = 'Render phonegap htmls'

	def handle(self, *args, **options):
		"""First argument is file path."""

		path = args[0]
		app_version = int(args[1])

		def render_page(name, render_function, extra_context={},
						replace_root_links=False, **kwargs):
			context = {
				'STATIC_URL': settings.STATIC_URL[1:],
				'MEDIA_URL': settings.MEDIA_URL[1:],
				'phonegap': True,
				'phonegap_page_name': name,
				'phonegap_version': get_phonegap_version(app_version),
				'app_version': app_version,
			}
			context = dict(context, **extra_context)
			page = render_function(context, **kwargs)
			if replace_root_links:
				page = page.replace('/site_media', 'site_media')
			page = add_security_policy_header(page)

			with open(path + name + '.html', 'w') as f:
				f.write(page.encode('utf-8'))

		def add_security_policy_header(page):
			header = '<meta http-equiv="{}" content="{}">'.format(
				"Content-Security-Policy",
				"default-src *; style-src 'self' https://fonts.googleapis.com https://code.jquery.com 'unsafe-inline'; script-src 'self' https://*.googleapis.com https://*.facebook.net 'unsafe-inline' 'unsafe-eval'")
			page = re.sub('<head>', '<head>\n'+header, page)
			return page

		def render_facebook_signup(ctx):
			ctx.update({
				'facebook_signup': True
			})
			return render_to_string('account/select_type.html', ctx)

		def render_login(ctx):
			ctx.update({
				'skip_last_page_setup': True,
				'login_form': LoginFormHS(),
			})
			return render_to_string('phonegap/login.html', ctx)

		def render_home(ctx):
			ctx['skip_last_page_setup'] = True
			return render_to_string('phonegap/home.html', ctx)

		def increment_version_by_one():
			if app_version == 1:
				path = settings.PHONEGAP_VERSION_FILE_PATH
			else:
				path = settings.PHONEGAP_VERSION2_FILE_PATH
			with open(path, 'r+') as f:
				current_version = int(f.readline())
				f.seek(0)
				f.write(str(current_version + 1))

		# app #2

		def render_login2(ctx):
			ctx.update({
				'skip_last_page_setup': True,
				'login_form': LoginFormHS(),
			})
			return render_to_string('phonegap/login2.html', ctx)

		def render_home2(ctx):
			ctx['skip_last_page_setup'] = True
			return render_to_string('phonegap/home2.html', ctx)

		def render_ghp_screen0(ctx):
			return render_to_string('phonegap/ghp_screen0.html', ctx)

		def render_signup0(ctx):
			return render_to_string('phonegap/signup0.html', ctx)

		def render_my_info(ctx):
			return render_to_string('phonegap/my_info.html', ctx)

		def render_upload_photo(ctx):
			return render_to_string('phonegap/upload_photo.html', ctx)

		def render_crop_photo(ctx):
			return render_to_string('phonegap/crop_photo.html', ctx)

		def render_provider_choice(ctx):
			return render_to_string('phonegap/provider_choice.html', ctx)

		def render_create_profile(ctx):
			return render_to_string('phonegap/create_profile.html', ctx)

		def render_specialties(ctx):
			return render_to_string('phonegap/specialties.html', ctx)

		def render_add_modality(ctx):
			form = ModalityForm()
			ctx['form'] = form
			return render_to_string('phonegap/add_modality.html', ctx)

		def render_location(ctx):
			ctx['remote_sessions_form'] = RemoteSessionsForm()
			ctx['location_form'] = LocationForm(account_setup=True)
			return render_to_string('phonegap/location.html', ctx)

		def render_optional_info(ctx):
			ctx.update({
				'form': HealerOptionalInfoForm(),
				'editing_self': True,
			})
			return render_to_string('phonegap/optional_info.html', ctx)

		def render_write_a_bit(ctx):
			ctx['form'] = AboutClientForm()
			return render_to_string('phonegap/write_a_bit.html', ctx)

		def render_list(ctx):
			ctx['list_version'] = settings.PHONEGAP_LIST_VERSION
			ctx['list_style'] = template_as_string('list.css', True)
			ctx['list_js'] = template_as_string('list.js', True)
			ctx['list_content'] = template_as_string('list_content.html', True)
			return render_to_string('phonegap/list.html', ctx)

		increment_version_by_one()

		render_page('notes', render_notes_home)
		render_page('ghp', render_ghp_home, get_facebook_context())
		render_page('login', render_login)
		render_page('index', render_home)
		render_page('notes_landing', render_notes_landing)
		render_page('signup', render_signup, phonegap=True)
		render_page('facebook_signup', render_facebook_signup)
		render_page('signup_thanks_client', render_signup_thanks, type='client', phonegap=True)
		render_page('signup_thanks_healer', render_signup_thanks, type='healer', phonegap=True)
		render_page('signup_thanks_wellness_center', render_signup_thanks, type='wellness_center', phonegap=True)
		render_page('signup_fb_thanks_client', render_signup_thanks, type='client', email_verification=False, phonegap=True)
		render_page('signup_fb_thanks_healer', render_signup_thanks, type='healer', email_verification=False, phonegap=True)
		render_page('signup_fb_thanks_wellness_center', render_signup_thanks, type='wellness_center', email_verification=False, phonegap=True)
		render_page('book_thanks', render_book_thanks)
		render_page('find_a_provider', render_search, replace_root_links=True)
		render_page('error_report', render_error_report)

		if app_version == 2:
			render_page('login', render_login2)
			render_page('index', render_home2)
			render_page('ghp_screen0', render_ghp_screen0)
			render_page('signup0', render_signup0)
			render_page('my_info', render_my_info)
			render_page('upload_photo', render_upload_photo)
			render_page('crop_photo', render_crop_photo)
			render_page('provider_choice', render_provider_choice)
			render_page('create_profile', render_create_profile)
			render_page('specialties', render_specialties)
			render_page('add_modality', render_add_modality)
			render_page('location', render_location)
			render_page('optional_info', render_optional_info)
			render_page('write_a_bit', render_write_a_bit)
			render_page('list', render_list)
