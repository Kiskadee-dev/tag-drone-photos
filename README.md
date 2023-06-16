# tag-drone-photos
This repository provides a recursive tagging solution for folders containing drone images (and any other JPEG files). 

The tags are assigned based on the Exif coordinates of the images and are saved in a human-readable file. 

They are also reverse coded using Geopy for enhanced readability.

Perfect to use with *Hydrus Network* or other tag-focused gallery to organize your images based on location.

# Install dependencies:
poetry install

# Usage:
poetry run python tag.py path-to-folder
