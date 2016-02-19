from django.conf.urls import patterns, url

from phonegap.views import (UpdateProfile, SavePhoto, GetAvatarLink,
	GetModalities, AddModality, SaveLocation, LocationExists, OptionalInfo,
	WriteABit, GetCircleList, FacebookAssociateUser, GetReceivedHealingList,
	GetListUpdate)

urlpatterns = patterns("",
	url(r"^update_profile_ajax/$", UpdateProfile.as_view(), name="update_profile_ajax"),
	url(r"^save_photo_ajax/$", SavePhoto.as_view(), name="save_photo_ajax"),
	url(r"^get_avatar_link_ajax/$", GetAvatarLink.as_view(), name="get_avatar_link_ajax"),
	url(r"^get_modalities_ajax/$", GetModalities.as_view(), name="get_modalities_ajax"),
	url(r"^add_modality_ajax/$", AddModality.as_view(), name="add_modality_ajax"),
	url(r"^save_location_ajax/$", SaveLocation.as_view(), name="save_location_ajax"),
	url(r"^location_exists_ajax/$", LocationExists.as_view(), name="location_exists_ajax"),
	url(r"^optional_info_ajax/$", OptionalInfo.as_view(), name="optional_info_ajax"),
	url(r"^write_a_bit_ajax/$", WriteABit.as_view(), name="write_a_bit_ajax"),
	url(r"^get_circle_list_ajax/$", GetCircleList.as_view(), name="get_circle_list_ajax"),
	url(r"^get_received_healing_list/$", GetReceivedHealingList.as_view(), name="get_received_healing_list"),
	url(r"^facebook_associate_user_ajax/$", FacebookAssociateUser.as_view(), name="facebook_associate_user_ajax"),
	url(r"^get_list_update/$", GetListUpdate.as_view(), name="get_list_update"),
)
