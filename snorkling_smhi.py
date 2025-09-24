import requests
from datetime import datetime
import pytz

# Koordinater (Lysekil)
LAT = 58.2746
LON = 11.4350

def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def vind_pil(grader):
    if grader is None:
        return "?"
    grader = grader % 360  # säkerställ 0-359
    if 337.5 <= grader or grader < 22.5:
        return "↑"
    elif 22.5 <= grader < 67.5:
        return "↗"
    elif 67.5 <= grader < 112.5:
        return "→"
    elif 112.5 <= grader < 157.5:
        return "↘"
    elif 157.5 <= grader < 202.5:
        return "↓"
    elif 202.5 <= grader < 247.5:
        return "↙"
    elif 247.5 <= grader < 292.5:
        return "←"
    elif 292.5 <= grader < 337.5:
        return "↖"

def forecast_19(data, dagar=3):
    """Hämtar forecast kl 19 svensk tid för kommande 'dagar'"""
    stockholm = pytz.timezone("Europe/Stockholm")
    forecasts = []

    for ts in data["timeSeries"]:
        utc_time = datetime.fromisoformat(ts["validTime"].replace("Z", "+00:00"))
        lokal_tid = utc_time.astimezone(stockholm)

        if lokal_tid.hour == 19:
            params = {p["name"]: p["values"][0] for p in ts["parameters"]}
            forecasts.append({
                "datum": lokal_tid.date(),
                "t": params.get("t"),           # Lufttemperatur
                "ws": params.get("ws"),         # Vind
                "gust": params.get("gust"),     # Vindbyar
                "r": params.get("r"),           # Nederbörd
                "wvh": params.get("wvh"),       # Våghöjd
                "vis": params.get("vis"),       # Sikt
                "tcc": params.get("tcc_mean")   # Molnighet
            })

        if len(forecasts) >= dagar:
            break
    return forecasts

def snorkling_ok(f):
    """Bedömning baserat på t, ws, wvh och gust (vindbyar)"""
    t = f["t"] or 0
    ws = f["ws"] or 0
    wvh = f["wvh"] or 0
    gust = f["gust"] or 0  # Om värdet saknas, sätt 0

    if t > 0 and ws < 5 and wvh < 1 and gust < 8:
        return True
    return False

def main():
    data = hamta_vader()
    forecasts = forecast_19(data, dagar=3)

    for f in forecast:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        moln = f"{f['cloud']}% molnighet" if f['cloud'] is not None else "okänd molnighet"
        riktning = wind_arrow(f["wd"]) if f["wd"] is not None else "?"
        
        msg = (
            f"Väder kl {f['time']} den {f['datum']} – {status}\n"
            f"🌡 Temp: {f['t']}°C | 🌬 Vind: {f['ws']} m/s ({riktning}) | "
            f"🌊 Våg: {f['wvh']} m | 💨 Byvind: {f['gust']} m/s | ☁ {moln}"
        )
        print(msg)

if __name__ == "__main__":
    main()



