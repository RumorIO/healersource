def replace_non_ascii(string):
	return "".join([x if ord(x) < 128 else '_' for x in string])
