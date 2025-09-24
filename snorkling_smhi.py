import requests
import datetime
import pytz

# Koordinater för Skaftö
LAT = 58.316
LON = 11.468

# Ladda väderdata från SMHI
def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Ladda havsdata (våghöjd, riktning, period, sst) från SMHI
def hamta_hav():
    url = f"https://opendata-download-oceanforecast.smhi.se/api/category/oceanography/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Vindriktning som pil
def wind_direction_arrow(deg):
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    ix = round(deg / 45) % 8
    return arrows[ix]

# Snorklingregler (ignorera våghöjd om den saknas)
def snorkling_ok(f):
    try:
        return (
            float(f["t"]) > 0 and
            float(f["ws"]) < 5 and
            float(f["gust"]) < 8
        )
    except (TypeError, ValueError):
        return False

# Hjälpfunktion som ersätter None med "?"
def safe_get(params, key):
    value = params.get(key)
    return value if value is not None else "?"

def main():
    tz = pytz.timezone("Europe/Stockholm")

    vader_data = hamta_vader()
    hav_data = hamta_hav()

    # Bygg havsdata som dict: tid -> {swh, dir, tp, sst}
    hav_dict = {}
    for t in hav_data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(t["validTime"].replace("Z", "+00:00")).astimezone(tz)
        tid_str = valid_time.strftime("%Y-%m-%dT%H:%M")
        params = {p["name"]: p["values"][0] for p in t["parameters"]}
        hav_dict[tid_str] = {
            "swh": safe_get(params, "swh"),
            "dir": safe_get(params, "dir"),
            "tp": safe_get(params, "tp"),
            "sst": safe_get(params, "sst")
        }

    prognoser = []

    for t in vader_data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(t["validTime"].replace("Z", "+00:00")).astimezone(tz)
        if valid_time.hour == 19 and len(prognoser) < 3:
            params = {p["name"]: p["values"][0] for p in t["parameters"]}
            tid_str = valid_time.strftime("%Y-%m-%dT%H:%M")
            hav = hav_dict.get(tid_str, {"swh": "?", "dir": "?", "tp": "?", "sst": "?"})
            prognoser.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "t": safe_get(params, "t"),
                "ws": safe_get(params, "ws"),
                "gust": safe_get(params, "gust"),
                "r": safe_get(params, "r"),
                "wvh": hav["swh"],
                "wave_dir": hav["dir"],
                "wave_tp": hav["tp"],
                "sst": hav["sst"],
                "tcc_mean": safe_get(params, "tcc_mean"),
                "wd": safe_get(params, "wd")
            })

    for f in prognoser:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        wind_arrow = wind_direction_arrow(f["wd"]) if f["wd"] != "?" else "?"
        wave_arrow = wind_direction_arrow(f["wave_dir"]) if f["wave_dir"] != "?" else "?"
        msg = (
            f"Väder kl 19:00 den {f['datum']} – {status} | "
            f"Temp: {f['t']}°C, Vind: {f['ws']} m/s {wind_arrow}, Byar: {f['gust']} m/s, "
            f"Nederbörd: {f['r']} mm, Våghöjd: {f['wvh']} m {wave_arrow}, "
            f"Vågperiod: {f['wave_tp']} s, Havstemperatur: {f['sst']}°C, "
            f"Molnighet: {f['tcc_mean']} /8"
        )
        print(msg)

if __name__ == "__main__":
    main()
