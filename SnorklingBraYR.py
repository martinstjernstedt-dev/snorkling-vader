import requests
import datetime
import pytz

# Koordinater för Skaftö
LAT = 58.316
LON = 11.468

# Yr kräver User-Agent
HEADERS = {
    "User-Agent": "SnorklingApp/1.0"
}

# Vind- och vågpilar
def wind_direction_arrow(deg):
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    ix = round(deg / 45) % 8
    return arrows[ix]

# Snorklingregler
def snorkling_ok(t):
    try:
        return float(t["t"]) > 0 and float(t["ws"]) < 5 and float(t["gust"]) < 8
    except (TypeError, ValueError):
        return False

# Hjälp: ersätt None med "?"
def safe(val):
    return val if val is not None else "?"

# Hämta väderdata från Yr
def hamta_vader_yr():
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def main():
    tz = pytz.timezone("Europe/Stockholm")
    data = hamta_vader_yr()
    prognoser = []

    for t in data["properties"]["timeseries"]:
        # Fix: hantera Z (UTC)
        valid_time = datetime.datetime.fromisoformat(
            t["time"].replace("Z", "+00:00")
        ).astimezone(tz)

        if valid_time.hour == 19 and len(prognoser) < 3:
            inst = t["data"]["instant"]["details"]
            waves = t["data"].get("waves", {}).get("details", {})
            prognoser.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "t": safe(inst.get("air_temperature")),
                "ws": safe(inst.get("wind_speed")),
                "gust": safe(inst.get("wind_speed_of_gust")),
                "wd": safe(inst.get("wind_from_direction")),
                "r": safe(inst.get("precipitation_amount")),
                "wvh": safe(waves.get("significant_wave_height")),
                "wave_dir": safe(waves.get("wave_from_direction")),
                "wave_tp": safe(waves.get("wave_period"))
            })

    for f in prognoser:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        wind_arrow = "?" if f["wd"] == "?" else wind_direction_arrow(f["wd"])
        wave_arrow = "?" if f["wave_dir"] == "?" else wind_direction_arrow(f["wave_dir"])
        msg = (
            f"Väder kl 19:00 den {f['datum']} – {status}\n"
            f"Temp: {f['t']}°C, Vind: {f['ws']} m/s {wind_arrow}, Byar: {f['gust']} m/s\n"
            f"Nederbörd: {f['r']} mm, Våghöjd: {f['wvh']} m {wave_arrow}, Vågperiod: {f['wave_tp']} s"
        )
        print(msg)

if __name__ == "__main__":
    main()
