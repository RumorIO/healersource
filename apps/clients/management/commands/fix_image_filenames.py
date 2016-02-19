import imghdr
from os import rename

from django.conf import settings
from django.core.management.base import BaseCommand

from avatar.models import Avatar
from util import is_correct_image_file_type


class Command(BaseCommand):

	help = 'Sets up correct extensions for avatars'

	def handle(self, *args, **options):
		def fix_filename(name, type):
			def is_correct_extension(name):
				name = str(name).lower()
				if type == 'jpeg':
					return name.endswith('.jpg') or name.endswith('.jpeg')
				else:
					return name.endswith('.' + type)

			if not is_correct_extension(name):
				return '%s.%s' % (name, type)

		avatars = Avatar.objects.all()
		renamed_files = {}
		for avatar in avatars:
			filename = avatar.avatar
			path = filename.path
			try:
				if filename in renamed_files:
					fixed_filename = renamed_files[filename]
					avatar.avatar = fixed_filename
					avatar.save()

					print 'Duplicated avatar incorrect path "%s". Renamed to "%s"' % (filename,
							fixed_filename)
					continue

				type = imghdr.what(path)
				if is_correct_image_file_type(type, filename):
					fixed_filename = fix_filename(filename, type)
					if fixed_filename is not None:
						avatar.avatar = fixed_filename
						rename(path, avatar.avatar.path)
						avatar.save()
						renamed_files[filename] = fixed_filename
						print 'Incorrect path "%s". Renamed to "%s"' % (filename,
							fixed_filename)
				else:
					print 'Image is not of %s format "%s"' % (', '.join(settings.ALLOWED_IMAGE_UPLOAD_TYPES), path)
			except IOError:
				print 'File "%s" not found' % path
