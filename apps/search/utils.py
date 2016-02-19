from modality.models import Modality, ModalityCategory
from search.models import HealerSearchHistory

def add_to_healer_search_history(query, user, zipcode=None):
	if user:
		if user.is_superuser or user.is_staff:
			return
	keys = ['city', 'modality_id', 'modality_category_id']
	for key in keys:
		if key not in query:
			query[key] = None
	if query['city'] or query['modality_id'] or query['modality_category_id']:
		try:
			modality = Modality.objects_approved.get(
				id = query['modality_id']) if query['modality_id'] else None

		except Modality.DoesNotExist:
			#TODO Log for invalid modality id
			return

		try:
			modality_category = ModalityCategory.objects.get(
				id = query['modality_category_id']) if query['modality_category_id'] else None
		except ModalityCategory.DoesNotExist:
			#TODO Log for invalid modality category id
			return

		# if zipcode:
		# 	city_search_count_instance, _ = CitySearchCount.objects.get_or_create(zipcode=zipcode)
		# 	city_search_count_instance.increment_count() #increment search count for searched city


		user_id = user.id if user.is_authenticated() else None

		HealerSearchHistory.objects.create(
			zipcode=zipcode, modality_id=query['modality_id'],
			modality_category_id=query['modality_category_id'], user_id=user_id)