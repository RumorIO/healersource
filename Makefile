
maildebug:
	python -m smtpd -n -c DebuggingServer localhost:1025

tests:
	python ./manage.py test about audit blog_hs clients contacts_hs errors_hs friends_app healers modality review sync_hs --failfast
