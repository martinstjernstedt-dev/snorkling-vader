import requests
import datetime
import pytz

# Koordinater för Lysekil
LAT = 58.316
LON = 11.468

# Ladda väderdata från SMHI
def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Ladda havsdata (våghöjd) från SMHI
def hamta_vagdata():
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
        wvh_ok = True if f["wvh"] == "?" else float(f["wvh"]) < 1
        return (
            float(f["t"]) > 0 and
            float(f["ws"]) < 5 and
            float(f["gust"]) < 8 and
            wvh_ok
        )
    except (TypeError, ValueError):
        return False

# Hjälpfunktion som ersätter None med "?"
def safe_get(params, key):
    value = params.get(key)
    return value if value is not None else "?"

def main():
    tz = pytz.timezone("Europe/Stockholm")

    # Hämta väder och havsdata
    vader_data = hamta_vader()
    vag_data = hamta_vagdata()

    prognoser = []

    # Bygg upp vågdata som en dict: tid -> wvh
    vag_dict = {}
    for t in vag_data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(
            t["validTime"].replace("Z", "+00:00")
        ).astimezone(tz)
        params = {p["name"]: p["values"][0] for p in t["parameters"]}
        vag_dict[valid_time.strftime("%Y-%m-%dT%H:%M")] = safe_get(params, "swh")

    # Bygg väderprognos med våghöjd
    for t in vader_data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(
            t["validTime"].replace("Z", "+00:00")
        ).astimezone(tz)

        if valid_time.hour == 19 and len(prognoser) < 3:
            params = {p["name"]: p["values"][0] for p in t["parameters"]}
            tid_str = valid_time.strftime("%Y-%m-%dT%H:%M")
            wvh = vag_dict.get(tid_str, "?")  # hämta våghöjd eller "?"
            prognoser.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "t": safe_get(params, "t"),
                "ws": safe_get(params, "ws"),
                "gust": safe_get(params, "gust"),
                "r": safe_get(params, "r"),
                "wvh": wvh,
                "tcc_mean": safe_get(params, "tcc_mean"),
                "wd": safe_get(params, "wd")
            })

    # Skriv ut prognoser
    for f in prognoser:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        wind_arrow = wind_direction_arrow(f["wd"]) if f["wd"] != "?" else "?"
        msg = (
            f"Väder kl 19:00 den {f['datum']} – {status} | "
            f"Tem
