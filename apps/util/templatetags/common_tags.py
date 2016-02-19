from django import template

register = template.Library()


@register.filter
def starting_letters(value):
	'''
		Sample Input: bhaskar rao
		Its output: BR
	'''
	return "".join([x[0].upper() for x in value.split(" ") if len(x) > 0])
