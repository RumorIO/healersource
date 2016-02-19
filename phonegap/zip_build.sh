#!/usr/bin/env bash

# set up path variables
source config.sh
phonegap_app_www_path="$phonegap_app_prod_path/www"

tar -zcvf "$phonegap_app_prod_path/build.tar.gz" "$phonegap_app_www_path/"
