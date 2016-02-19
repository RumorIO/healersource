#!/usr/bin/env bash

# set up path variables
source $1
phonegap_app_www_path="$phonegap_app_dev_path/www"

# copy content from phonegap rep and render pages
cp -R ./www $phonegap_app_dev_path

cd $hs_rep_path
$hs_rep_path/manage.py collectstatic --noinput --settings=phonegap_settings
$hs_rep_path/manage.py render_phonegap_pages "$phonegap_app_www_path/" "$version" --settings=phonegap_settings

# copy all of the required media files
cd $phonegap_app_www_path
rm -Rf $phonegap_app_www_path/site_media/

mkdir -p css/images

mkdir -p site_media/static/healersource/js
mkdir -p site_media/static/healersource/img/home/
mkdir -p site_media/static/healersource/img/tour/
mkdir -p site_media/static/healersource/img/pricing/

mkdir -p site_media/static/uni_form
mkdir -p site_media/static/healersource/css/redmond
mkdir -p site_media/static/tinydropdown
mkdir -p site_media/static/floatbox/graphics/white

mkdir -p site_media/static/healersource/img/icons/social
mkdir -p site_media/static/endless_pagination/js
mkdir -p site_media/static/js
mkdir -p site_media/static/css

mkdir -p site_media/media/landing_notes

# libraries
cp "$hs_rep_path/media/uni_form/uni-form.css" "$phonegap_app_www_path/site_media/static/uni_form/uni-form.css"
cp "$hs_rep_path/media/uni_form/uni-form-generic.css" "$phonegap_app_www_path/site_media/static/uni_form/uni-form-generic.css"
cp "$hs_rep_path/site_media/static/healersource/css/redmond/jquery-ui.min.css" "$phonegap_app_www_path/site_media/static/healersource/css/redmond/jquery-ui.min.css"
cp "$hs_rep_path/site_media/static/healersource/js/jquery-ui.min.js" "$phonegap_app_www_path/site_media/static/healersource/js/jquery-ui.min.js"
cp "$hs_rep_path/media/tinydropdown/tinydropdown.css" "$phonegap_app_www_path/site_media/static/tinydropdown/tinydropdown.css"
cp "$hs_rep_path/media/tinydropdown/tinydropdown.js" "$phonegap_app_www_path/site_media/static/tinydropdown/tinydropdown.js"
cp "$hs_rep_path/site_media/static/endless_pagination/js/endless-pagination.js" "$phonegap_app_www_path/site_media/static/endless_pagination/js/endless-pagination.js"
cp -R "$hs_rep_path/media/infinite_scroll/" "$phonegap_app_www_path/site_media/static/infinite_scroll/"
cp -Rf "$hs_rep_path/site_media/static/tinyeditor" "$phonegap_app_www_path/site_media/static"
cp -Rf "$hs_rep_path/media/floatbox/graphics/white/outerClose.png" "$phonegap_app_www_path/js/floatbox/graphics/white/outerClose.png"
cp -Rf "$hs_rep_path/media/floatbox/graphics/white/loader_small.gif" "$phonegap_app_www_path/js/floatbox/graphics/white/loader_small.gif"
cp -Rf "$hs_rep_path/media/floatbox/graphics/white/loader_small.gif" "$phonegap_app_www_path/site_media/static/floatbox/graphics/white/loader_small.gif"
cp -Rf "$hs_rep_path/media/floatbox/graphics/white/loader.gif" "$phonegap_app_www_path/js/floatbox/graphics/white/loader.gif"

cp -Rf "$hs_rep_path/site_media/static/css" "$phonegap_app_www_path/site_media/static"
cp -Rf "$hs_rep_path/site_media/static/js" "$phonegap_app_www_path/site_media/static"

# css files
cp -R "$hs_rep_path/media/healersource/css" "$phonegap_app_www_path/site_media/static/healersource"


cp -R "$hs_rep_path/media/healersource/css/redmond/images/ui-bg_inset-hard_100_fcfdfd_1x100.png" "$phonegap_app_www_path/css/images/ui-bg_inset-hard_100_fcfdfd_1x100.png"
cp -R "$hs_rep_path/media/healersource/css/redmond/images/ui-bg_glass_75_d0e5f5_1x400.png" "$phonegap_app_www_path/css/images/ui-bg_glass_75_d0e5f5_1x400.png"
# cp "$hs_rep_path/media/healersource/css/hs.css" "$phonegap_app_www_path/site_media/static/healersource/css/hs.css"
# cp "$hs_rep_path/media/healersource/css/home.css" "$phonegap_app_www_path/site_media/static/healersource/css/home.css"
# cp "$hs_rep_path/media/healersource/css/healer-weekcalendar.css" "$phonegap_app_www_path/site_media/static/healersource/css/healer-weekcalendar.css"
# cp "$hs_rep_path/media/healersource/css/healer.css" "$phonegap_app_www_path/site_media/static/healersource/css/healer.css"
# cp "$hs_rep_path/media/healersource/css/search_results.css" "$phonegap_app_www_path/site_media/static/healersource/css/search_results.css"
# cp "$hs_rep_path/media/healersource/css/notes.css" "$phonegap_app_www_path/site_media/static/healersource/css/notes.css"
# cp "$hs_rep_path/media/healersource/css/send_healing.css" "$phonegap_app_www_path/site_media/static/healersource/css/send_healing.css"
# cp "$hs_rep_path/media/healersource/css/landing.css" "$phonegap_app_www_path/site_media/static/healersource/css/landing.css"

# js files
cp -R "$hs_rep_path/media/healersource/js" "$phonegap_app_www_path/site_media/static/healersource"

# cp "$hs_rep_path/media/healersource/js/util.js" "$phonegap_app_www_path/site_media/static/healersource/js/util.js"
# cp "$hs_rep_path/media/healersource/js/jquery.placeholder.js" "$phonegap_app_www_path/site_media/static/healersource/js/jquery.placeholder.js"
# cp "$hs_rep_path/media/healersource/js/jquery.ui.autocomplete.html.js" "$phonegap_app_www_path/site_media/static/healersource/js/jquery.ui.autocomplete.html.js"
# cp "$hs_rep_path/media/healersource/js/jquery.cookie.js" "$phonegap_app_www_path/site_media/static/healersource/js/jquery.cookie.js"
# cp "$hs_rep_path/media/healersource/js/csrf.js" "$phonegap_app_www_path/site_media/static/healersource/js/csrf.js"
# cp "$hs_rep_path/media/healersource/js/respond.src.js" "$phonegap_app_www_path/site_media/static/healersource/js/respond.src.js"
# cp "$hs_rep_path/media/healersource/js/invite.js" "$phonegap_app_www_path/site_media/static/healersource/js/invite.js"
# cp "$hs_rep_path/media/healersource/js/jquery.touchSwipe.min.js" "$phonegap_app_www_path/site_media/static/healersource/js/jquery.touchSwipe.min.js"
# cp "$hs_rep_path/media/healersource/js/notes.js" "$phonegap_app_www_path/site_media/static/healersource/js/notes.js"
# cp "$hs_rep_path/media/healersource/js/new_client_dialog_autocomplete.js" "$phonegap_app_www_path/site_media/static/healersource/js/new_client_dialog_autocomplete.js"
# cp "$hs_rep_path/media/healersource/js/new_client.js" "$phonegap_app_www_path/site_media/static/healersource/js/new_client.js"
# cp "$hs_rep_path/media/healersource/js/signup.js" "$phonegap_app_www_path/site_media/static/healersource/js/signup.js"
# cp "$hs_rep_path/media/healersource/js/send_healing.js" "$phonegap_app_www_path/site_media/static/healersource/js/send_healing.js"
# cp "$hs_rep_path/media/healersource/js/landing_notes.js" "$phonegap_app_www_path/site_media/static/healersource/js/landing_notes.js"
# cp "$hs_rep_path/media/healersource/js/signup_thanks.js" "$phonegap_app_www_path/site_media/static/healersource/js/signup_thanks.js"

# image dirs
cp -R "$hs_rep_path/media/healersource/img/notes" "$phonegap_app_www_path/site_media/static/healersource/img"
cp -R "$hs_rep_path/media/healersource/img/landing" "$phonegap_app_www_path/site_media/static/healersource/img"
cp -R "$hs_rep_path/media/healersource/img/nav_bar" "$phonegap_app_www_path/site_media/static/healersource/img"
cp -R "$hs_rep_path/media/healersource/img/nav_top" "$phonegap_app_www_path/site_media/static/healersource/img"
cp -R "$hs_rep_path/media/healersource/img/icons" "$phonegap_app_www_path/site_media/static/healersource/img"
cp -Rf "$hs_rep_path/site_media/media/landing_notes" "$phonegap_app_www_path/site_media/media"

# individual images

cp "$hs_rep_path/media/healersource/img/ambassador.png" "$phonegap_app_www_path/site_media/static/healersource/img/ambassador.png"
cp "$hs_rep_path/media/healersource/img/tweet_btn.png" "$phonegap_app_www_path/site_media/static/healersource/img/tweet_btn.png"
cp "$hs_rep_path/media/healersource/img/fb_share_btn.png" "$phonegap_app_www_path/site_media/static/healersource/img/fb_share_btn.png"
cp "$hs_rep_path/media/healersource/img/hs_logo.png" "$phonegap_app_www_path/site_media/static/healersource/img/hs_logo.png"
cp "$hs_rep_path/media/healersource/img/user.png" "$phonegap_app_www_path/site_media/static/healersource/img/user.png"
cp "$hs_rep_path/media/healersource/img/hand.png" "$phonegap_app_www_path/site_media/static/healersource/img/hand.png"
cp "$hs_rep_path/media/healersource/img/wellness_center.png" "$phonegap_app_www_path/site_media/static/healersource/img/wellness_center.png"
cp "$hs_rep_path/media/healersource/img/checkmark.png" "$phonegap_app_www_path/site_media/static/healersource/img/checkmark.png"
cp "$hs_rep_path/media/healersource/img/delete.png" "$phonegap_app_www_path/site_media/static/healersource/img/delete.png"
cp "$hs_rep_path/media/healersource/img/red-heart.png" "$phonegap_app_www_path/site_media/static/healersource/img/red-heart.png"
cp "$hs_rep_path/media/healersource/img/group-thumbs-up.jpg" "$phonegap_app_www_path/site_media/static/healersource/img/group-thumbs-up.jpg"
cp "$hs_rep_path/media/healersource/img/icons/social/fb_invite_your_friends.png" "$phonegap_app_www_path/site_media/static/healersource/img/icons/social/fb_invite_your_friends.png"
cp "$hs_rep_path/media/healersource/img/icons/social/google.png" "$phonegap_app_www_path/site_media/static/healersource/img/icons/social/google.png"
cp "$hs_rep_path/media/healersource/img/icons/social/facebook.png" "$phonegap_app_www_path/site_media/static/healersource/img/icons/social/facebook.png"
cp "$hs_rep_path/media/healersource/img/icons/icon_earth.png" "$phonegap_app_www_path/site_media/static/healersource/img/icons/icon_earth.png"
cp "$hs_rep_path/media/healersource/img/home/logo.png" "$phonegap_app_www_path/site_media/static/healersource/img/home/logo.png"
cp "$hs_rep_path/media/healersource/img/home/panel_icon_login.png" "$phonegap_app_www_path/site_media/static/healersource/img/home/panel_icon_login.png"
cp "$hs_rep_path/media/healersource/img/home/panel_icon_signup.png" "$phonegap_app_www_path/site_media/static/healersource/img/home/panel_icon_signup.png"
cp "$hs_rep_path/media/healersource/img/home/signup_celebration.png" "$phonegap_app_www_path/site_media/static/healersource/img/home/signup_celebration.png"
cp "$hs_rep_path/media/healersource/img/tour/intake.gif" "$phonegap_app_www_path/site_media/static/healersource/img/tour/intake.gif"
cp "$hs_rep_path/media/healersource/img/pricing/francesca.jpg" "$phonegap_app_www_path/site_media/static/healersource/img/pricing/francesca.jpg"
cp "$hs_rep_path/media/healersource/img/pricing/francesca-sm.jpg" "$phonegap_app_www_path/site_media/static/healersource/img/pricing/francesca-sm.jpg"

cp -Rf $phonegap_app_www_path $phonegap_app_prod_path
cp -Rf $phonegap_app_dev_path/config_prod.xml $phonegap_app_prod_path/config.xml
cp $phonegap_app_prod_path/www/js/phonegap_config_prod.js $phonegap_app_prod_path/www/js/phonegap_config.js

export LC_CTYPE=C
export LANG=C
find $phonegap_app_prod_path/www -type f -exec sed -i '' "s/$2/www.healersource.com/g" {} \;
