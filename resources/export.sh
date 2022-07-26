#!/bin/sh
inkscape -w 128 -h 128 logo.svg -o EXPORT_logo.png
inkscape -w 1280 -h 128 tagline.svg -o EXPORT_tagline.png
convert +append EXPORT_logo.png EXPORT_tagline.png EXPORT_github.png
convert EXPORT_logo.png logo.ico
