# coding=utf-8
from bs4 import BeautifulSoup


def post_quality(body):
	body = BeautifulSoup(body)
	if len(body.get_text()) > 400:
		return True
	return False
