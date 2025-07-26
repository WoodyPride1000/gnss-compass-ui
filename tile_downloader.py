# tile_downloader.py
import os
import math
import requests
from tqdm import tqdm

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def download_tiles(min_lon, min_lat, max_lon, max_lat, zoom_start, zoom_end, out_dir):
    for zoom in range(zoom_start, zoom_end + 1):
        x_min, y_max = deg2num(min_lat, min_lon, zoom)
        x_max, y_min = deg2num(max_lat, max_lon, zoom)
        for x in tqdm(range(x_min, x_max + 1), desc=f"Zoom {zoom}"):
            for y in range(y_min, y_max + 1):
                url = f"https://cyberjapandata.gsi.go.jp/xyz/std/{zoom}/{x}/{y}.png"
                tile_path = os.path.join(out_dir, str(zoom), str(x))
                os.makedirs(tile_path, exist_ok=True)
                tile_file = os.path.join(tile_path, f"{y}.png")
                if not os.path.exists(tile_file):
                    r = requests.get(url)
                    if r.status_code == 200:
                        with open(tile_file, 'wb') as f:
                            f.write(r.content)

# 使い方（例）:
# download_tiles(139.7, 35.6, 139.9, 35.8, 13, 16, './tiles')
