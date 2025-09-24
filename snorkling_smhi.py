import requests
import datetime
import pytz

# Hämta väderdata från SMHI
def get_smhi_forecast(lat, lon):
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{lon}/lat/{lat}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Vindriktning → pil
def wind_arrow(direction):
    if direction is None:
        return "?"
    arrows = ["↑ N", "↗ NE", "→ E", "↘ SE", "↓ S", "↙ SW", "← W", "↖ NW"]
    idx = int((direction % 360) / 45)
    return arrows[idx]

# Kolla om vädret är bra för snorkling
def snorkling_ok(f):
    t = f["t"] if f["t"] is not None else -99
    ws = f["ws"] if f["ws"] is not None else 99
    wvh = f["wvh"] if f["wvh"] is not None else 99
    gust = f["gust"] if f["gust"] is not None else 99

    return t > 0 and ws < 5 and wvh < 1 and gust < 8

def main():
    lat, lon = 58.25, 11.45  # Lysekil
    tz = pytz.timezone("Europe/Stockholm")
    data = get_smhi_forecast(lat, lon)

    forecast = []
    for t in data["timeSeries"]:
        valid_time = datetime.datetime.fromisoformat(t["validTime"]).astimezone(tz)
        if valid_time.hour == 19:  # Bara kl 19:00
            params = {p["name"]: p["values"][0] for p in t["parameters"]}
            forecast.append({
                "datum": valid_time.strftime("%Y-%m-%d"),
                "time": valid_time.strftime("%H:%M"),
                "t": params.get("t"),
                "ws": params.get("ws"),
                "wd": params.get("wd"),
                "wvh": params.get("swh"),
                "gust": params.get("gust"),
                "cloud": params.get("tcc_mean"),
            })

    for f in forecast:
        status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
        moln = f"{f['cloud']}% molnighet" if f['cloud'] is not None else "okänd molnighet"
        riktning = wind_arrow(f["wd"]) if f["wd"] is not None else "?"

        msg = (
            f"Väder kl {f['time']} den {f['datum']} – {status}\n"
            f"🌡 Temp: {f['t']}°C | "
            f"🌬 Vind: {f['ws']} m/s ({riktning}) | "
            f"🌊 Våg: {f['wvh']} m | "
            f"💨 Byvind: {f['gust']} m/s | "
            f"☁ {moln}"
        )
        print(msg)

if __name__ == "__main__":
    main()
