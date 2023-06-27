"""
Copyright: Matheus Victor @ 2023

Search jpegs recursively and tags them based on exif coordinates
The coordinates are reverse coded with Geopy Nominatim so they are human readable

Install dependencies:
poetry install

Usage:
poetry run python tag.py path-to-folder

TODO: add support for raw images
TODO: add support for videos
"""


import argparse
import os
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim
from rich import print
from rich.progress import track
from typing import Tuple


def get_exif_data(image) -> dict[str, dict]:
    """
    Returns a dictionary from the exif data of an PIL Image.

    :param image: PIL Image
    :type image: PIL Image
    :return: Dictionary with the decoded exif data as dict[str, dict]
    :rtype: dict[str, dict]
    """
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
    except:
        raise ValueError("Error")
    return exif_data


def dms_to_dd(exif: dict) -> Tuple[float, float]:
    """
    Converts the coordinates from dms to dd

    :param exif: the exif dict
    :type exif: dict
    :return: A tuple of the dd coordinates
    :rtype: Tuple(float, float)
    """
    if "GPSInfo" not in exif.keys():
        raise ValueError("No GPS Info in exif")

    gps_info = exif["GPSInfo"]
    dms_lat = gps_info["GPSLatitude"]
    dms_long = gps_info["GPSLongitude"]

    def get_dd(gps_coords):
        d, m, s = gps_coords
        dd = d + m / 60.0 + s / 3600.0
        return -dd

    return get_dd(dms_lat), get_dd(dms_long)


class TAGGER:
    GEOLOCATOR = Nominatim(user_agent="geoapiExercises")

    def __init__(self):
        self.paths_to_process: list[Path] = []

    def recurse(self, folder: Path) -> None:
        """
        Find the files and add jpeg images to queue recursively.

        :param folder: path to images folder
        :type folder: Path
        :return: None
        """
        files = os.listdir(folder)
        for f in files:
            path = Path(folder, f)
            if path.is_dir():
                self.recurse(path)
            elif path.is_file():
                if not Path(str(path) + ".txt").exists() and (
                    path.name.endswith(".jpg") or path.name.endswith(".jpeg")
                ):
                    print(f"[yellow]Queued: {path}[/yellow]")
                    self.paths_to_process.append(path)
                else:
                    print(f"[cyan]Skipping: {path}[/cyan]")

    def write_tags(self):
        """
        Write tags to a text file next to the image based on gps coordinates.

        This function is slow and requires internet access due to `Geopy`.

        :return: None
        """
        paths: list[Path] = self.paths_to_process

        for file_path in track(paths, description="Processing images.."):
            try:
                with Image.open(file_path) as image:
                    print(f"Opening: [blue]{file_path}[/blue]")
                    exif = get_exif_data(image)
                    if file_path.name.endswith(".tiff"):
                        print(f"[gray]Tiff is not supported yet[/gray]")
                    elif exif is None or "GPSInfo" not in exif.keys():
                        print(f"[blink red]No gps data in exif[/blink red]")
                    else:
                        lat, long = dms_to_dd(get_exif_data(image))
                        location = self.GEOLOCATOR.reverse(str(lat) + "," + str(long))
                        print(f"[green]{location}[/green]")
                        with open(
                            str(file_path) + ".txt", "w", encoding="utf-8"
                        ) as tagfile:
                            tagfile.write(f"{location}")
                            tagfile.close()

            except OSError:
                print(f"[red]Can't open {file_path}[/red]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()

    target_dir = Path(args.path)

    if not target_dir.exists():
        print(f"[red]Target path does not exist! {target_dir}[/red]")
        raise FileNotFoundError("Path does not exists")

    tagger = TAGGER()
    tagger.recurse(target_dir)
    tagger.write_tags()
