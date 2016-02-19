#!/usr/bin/env bash

cordova create $1 com.healersource.www Healersource
cd $1
cordova platform add ios
cordova platform add android

wget https://github.com/Wizcorp/phonegap-facebook-plugin/archive/master.zip
unzip master.zip
cordova -d plugin add phonegap-facebook-plugin-master --variable APP_ID="$2" --variable APP_NAME="$3"
rm master.zip
rm -R phonegap-facebook-plugin-master

cordova plugin add https://github.com/apache/cordova-plugin-network-information.git
cordova plugin add cordova-plugin-google-analytics@0.7.1
cordova plugin add org.apache.cordova.device
cordova plugin add cordova-plugin-camera
cordova plugin add org.apache.cordova.file
cordova plugin add org.apache.cordova.file-transfer

keytool -genkey -v -keystore healersource.keystore -alias hs -keyalg RSA -keysize 2048 -validity 10000
