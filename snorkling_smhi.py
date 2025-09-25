import requests
import datetime
import pytz

# Koordinater för Stockevik (SMHI)
LAT = 57.959961
LON = 11.547085

# SMHI väderdata
def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# HaV badplatsdata för Stockevik
def hamta_stockevik():
    url = "https://badplatsen.havochvatten.se/badplatsen/api/detail?id=SE0A21484000000552"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Vindriktning som pil
def wind_direction_arrow(deg):
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    try:
        ix = round(float(deg) / 45) % 8
        return arrows[ix]
    except (TypeError, ValueError):
        return "?"

# Snorklingregler
def snorkling_ok(f):
    try:
        return float(f["t"]) > 0 and float(f["ws"]) < 5 and float(f["gust"]) < 8
    except (TypeError, ValueError):
        return False

def main():
    tz = pytz.timezone("Europe/Stockholm")

    vader_data = hamta_vader()
    bad_data = hamta_stockevik()

    # Plocka vattentemperatur från första observationen (om finns)
    if "observations" in bad_data and bad_data["observations"]:
        sst = bad_data["observations"][0].get("vattentemperatur", "?")
    else:
        sst = "?"

    # Plocka vattenkvalitet
    water_quality = bad_data.get("properties", {}).get("badvattenklass", "?")

    prognoser = []

    for t in vader_data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(t["validTime"].replace("Z", "+00:00")).astimezone(tz)
        if valid_time.hour == 19 and len(prognoser) < 3:
            params = {p["name"]: p["values"][0] for p in t["parameters"]}
            prognoser.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "t": params.get("t", "?"),
                "ws": params.get("ws", "?"),
                "gust": params.get("gust", "?"),
                "r": params.get("r", "?"),
                "tcc_mean": params.get("tcc_mean", "?"),
                "wd": params.get("wd", "?"),
                "sst": sst,
                "water_quality": water_quality
            })

    for f in prognoser:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        wind_arrow = wind_direction_arrow(f["wd"])
        msg = (
            f"Väder kl 19:00 den {f['datum']} – {status}\n"
            f"Temp: {f['t']}°C, Vind: {f['ws']} m/s {wind_arrow}, Byar: {f['gust']} m/s\n"
            f"Nederbörd: {f['r']} mm, Molnighet: {f['tcc_mean']} /8\n"
            f"Havstemperatur (Stockevik): {f['sst']}°C, Vattenkvalitet: {f['water_quality']}"
        )
        print(msg)

if __name__ == "__main__":
    main()
