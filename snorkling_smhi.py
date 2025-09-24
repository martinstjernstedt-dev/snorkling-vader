import requests
import datetime
import pytz

# Koordinater för Stockevik
LAT = 57.959961
LON = 11.547085

# SMHI väderdata
def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# HaV badplatsdata
def hamta_badplats():
    url = f"https://badplatsen.havochvatten.se/badplatsen/api/detail?id=SE0A21484000000552"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Vindriktning som pil
def wind_direction_arrow(deg):
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    ix = round(deg / 45) % 8
    return arrows[ix]

# Snorklingregler
def snorkling_ok(f):
    try:
        return float(f["t"]) > 0 and float(f["ws"]) < 5 and float(f["gust"]) < 8
    except (TypeError, ValueError):
        return False

# Hjälpfunktion som ersätter None med "?"
def safe_get(params, key):
    value = params.get(key)
    return value if value is not None else "?"

def main():
    tz = pytz.timezone("Europe/Stockholm")

    vader_data = hamta_vader()
    bad_data = hamta_badplats()

    sst = safe_get(bad_data, "vattentemperatur")
    water_quality = safe_get(bad_data, "badvattenklass")

    prognoser = []

    for t in vader_data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(t["validTime"].replace("Z", "+00:00")).astimezone(tz)
        if valid_time.hour == 19 and len(prognoser) < 3:
            params = {p["name"]: p["values"][0] for p in t["parameters"]}
            prognoser.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "t": safe_get(params, "t"),
                "ws": safe_get(params, "ws"),
                "gust": safe_get(params, "gust"),
                "r": safe_get(params, "r"),
                "tcc_mean": safe_get(params, "tcc_mean"),
                "wd": safe_get(params, "wd"),
                "sst": sst,
                "water_quality": water_quality
            })

    for f in prognoser:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        wind_arrow = wind_direction_arrow(f["wd"]) if f["wd"] != "?" else "?"
        msg = (
            f"Väder kl 19:00 den {f['datum']} – {status}\n"
            f"Temp: {f['t']}°C, Vind: {f['ws']} m/s {wind_arrow}, Byar: {f['gust']} m/s\n"
            f"Nederbörd: {f['r']} mm, Molnighet: {f['tcc_mean']} /8\n"
            f"Havstemperatur: {f['sst']}°C, Vattenkvalitet: {f['water_quality']}"
        )
        print(msg)

if __name__ == "__main__":
    main()
