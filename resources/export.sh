#!/bin/sh
inkscape -w 128 -h 128 logo.svg -o EXPORT_logo.png
inkscape -w 1280 -h 128 tagline.svg -o EXPORT_tagline.png
sizes=(32 64 128)
for size in "${sizes[@]}"
do
    echo "generating icon for $size px"
    time inkscape -w "$size" -h "$size" ../resources/logo.svg -o "EXPORT_$size.png"
done
convert +append EXPORT_logo.png EXPORT_tagline.png EXPORT_github.png
convert EXPORT_logo.png logo.ico
