import argparse
import os
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim
from rich import print
from rich.progress import track

parser = argparse.ArgumentParser()
parser.add_argument("path")
args = parser.parse_args()

target_dir = Path(args.path)

if not target_dir.exists():
    print(f"[red]Target path does not exist! {target_dir}[/red]")
    raise FileNotFoundError("Path does not exists")

geolocator = Nominatim(user_agent="geoapiExercises")


def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
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


def dms_to_dd(exif):
    if "GPSInfo" not in exif.keys():
        return None

    GPSInfo = exif["GPSInfo"]
    dms_lat = GPSInfo["GPSLatitude"]
    dms_long = GPSInfo["GPSLongitude"]

    def get_dd(gps_coords):
        d, m, s = gps_coords
        dd = d + m / 60.0 + s / 3600.0
        return -dd

    return get_dd(dms_lat), get_dd(dms_long)


# Search images recursively and create tags from exif location


def image():
    pass


paths_to_process = []


def recurse(folder):
    files = os.listdir(folder)
    for f in files:
        path = Path(folder, f)
        if path.is_dir():
            recurse(path)
        elif path.is_file():
            if not Path(str(path) + ".txt").exists() and not path.name.endswith(".txt") and not path.name.lower().endswith(".dng"):
                print(f"[yellow]Queued {path}[/yellow]")
                paths_to_process.append(path)
            else:
                print(f"[cyan]Skipping file[/cyan]")


recurse(target_dir)


for p in track(paths_to_process, description="Processing data.."):
    try:
        with Image.open(p) as im:
            print(f"Opening [blue]{p}[/blue]")
            exif = get_exif_data(im)
            if p.name.endswith(".tiff"):
                print(f"[gray]Tiff is not supported yet[/gray]")
            elif exif is None or "GPSInfo" not in exif.keys():
                print(f"[blink red]No gps data in exif[/blink red]")
            else:
                lat, long = dms_to_dd(get_exif_data(im))
                location = geolocator.reverse(str(lat) + "," + str(long))
                print(f"[green]{location}[/green]")
                with open(str(p) + ".txt", "w", encoding="utf-8") as tagfile:
                    tagfile.write(f"{location}")
                    tagfile.close()

    except OSError:
        print(f"[red]Can't open {p}[/red]")
        pass
