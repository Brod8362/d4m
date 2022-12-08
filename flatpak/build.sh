#!/bin/sh
rm -rf temp_repo
mkdir temp_repo
flatpak-builder "$@" build pw.byakuren.d4m.yml --repo=./temp_repo
flatpak build-bundle ./temp_repo d4m.flatpak pw.byakuren.d4m