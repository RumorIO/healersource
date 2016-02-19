from dashboard.backends import db as db_backend


class SettingStore(object):
	#TODO: caching and global store for future use
	backend_module = db_backend

	def __getattr__(self, item):
		if item == item.upper():
			return self.backend_module.getsetting(item)
		else:
			raise AttributeError

	def __setattr__(self, key, value):
		if key == key.upper():
			self.backend_module.setsetting(key, value)
		else:
			raise AttributeError

	#def __iter__(self):
	#	for key in self.settings.keys():
	#		yield key, getattr(self, key)

	#def __len__(self):
	#	return len(self.settings)

	#def clear_trash(self):
	#	exclude_keys = list(self.settings)
	#	self.backend_module.exclude_clear(exclude_keys)
