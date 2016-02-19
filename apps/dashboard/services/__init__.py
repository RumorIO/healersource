"""
!!!DAMMIT CIRCULAR IMPORTS!!!

import pkgutil
MAIL_PROCESSOR_DEFAULT = 'default'


def get_processors():
	modpath = '%s/%s' % (__path__[0], 'mailprocessors')
	processors = ()
	for importer, modname, ispkg in pkgutil.iter_modules([modpath]):
		if not ispkg:
			m = importer.find_module(modname)
			m = m.load_module(modname)
			proc = getattr(m, 'PROCESSOR')
			processors += (proc,)
	print(processors)
	return processors


MAIL_PROCESSORS = get_processors()
"""
