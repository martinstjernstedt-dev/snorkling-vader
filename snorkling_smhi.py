import requests
import datetime
import pytz

# Koordinater för Lysekil (byt om du vill ha annan plats)
LAT = 58.2746
LON = 11.435

# Ladda väderdata från SMHI
def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Vindriktning som pil
def wind_direction_arrow(deg):
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    ix = round(deg / 45) % 8
    return arrows[ix]

# Regler för snorkling
def snorkling_ok(f):
    if f["t"] is None or f["ws"] is None or f["gust"] is None:
        return False

    # Om wvh saknas, låtsas att den är "snorkelvänlig"
    wvh_ok = True if f["wvh"] is None else f["wvh"] < 1

    return f["t"] > 0 and f["ws"] < 5 and f["gust"] < 8 and wvh_ok
    
def main():
    data = hamta_vader()
    tz = pytz.timezone("Europe/Stockholm")

    prognoser = []

    for t in data["timeSeries"]:
        # Fix: hantera Z (UTC)
        valid_time = datetime.datetime.fromisoformat(
            t["validTime"].replace("Z", "+00:00")
        ).astimezone(tz)

        if valid_time.hour == 19 and len(prognoser) < 3:
            # Hämta parametrar
            params = {p["name"]: p["values"][0] for p in t["parameters"]}
            prognoser.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "t": params.get("t"),
                "ws": params.get("ws"),
                "gust": params.get("gust"),
                "r": params.get("r"),
                "wvh": params.get("wvh"),
                "vis": params.get("vis"),
                "tcc_mean": params.get("tcc_mean"),
                "wd": params.get("wd")
            })

    for f in prognoser:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        wind_arrow = wind_direction_arrow(f["wd"]) if f["wd"] is not None else "?"
        msg = (
            f"Väder kl 19:00 den {f['datum']} – {status} | "
            f"Temp: {f['t']}°C, Vind: {f['ws']} m/s {wind_arrow}, Byar: {f['gust']} m/s, "
            f"Nederbörd: {f['r']} mm, Våghöjd: {f['wvh']} m, "
            f"Molnighet: {f['tcc_mean']} /8"
        )
        print(msg)

if __name__ == "__main__":
    main()

