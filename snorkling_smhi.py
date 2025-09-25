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

# Ladda badplatsdata från HaV för Stockevik
def hamta_stockevik():
    url = "https://badplatsen.havochvatten.se/badplatsen/api/feature"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    # filtrera fram Stockevik
    stockevik = [f for f in data if "Stockevik" in f.get("name", "")]
    return stockevik

# Vindriktning som pil
def wind_direction_arrow(deg):
    if deg == "?" or deg is None:
        return "?"
    try:
        deg = float(deg)
    except ValueError:
        return "?"
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

def main():
    tz = pytz.timezone("Europe/Stockholm")

    # Hämta väder
    vader_data = hamta_vader()
    print("✅ Hämtade väderdata från SMHI")

    # Hämta badplatsdata
    bad_data = hamta_stockevik()
    print("✅ Hämtade badplatsdata från HaV:", len(bad_data))

    # Plocka ut info från Stockevik
    if isinstance(bad_data, list) and bad_data:
        bad_data = bad_data[0]
        print("Badplats:", bad_data.get("name", "?"))
    else:
        bad_data = {}

    if "observations" in bad_data and bad_data["observations"]:
        sst = bad_data["observations"][0].get("vattentemperatur", "?")
        sst_tid = bad_data["observations"][0].get("observationstid", "")
    else:
        sst = "?"
        sst_tid = ""
        print("⚠️ Ingen vattentemperatur hittades för Stockevik")

    water_quality = bad_data.get("properties", {}).get("badvattenklass", "?")

    # Bygg prognoslista
    prognoser = []
    for t in vader_data.get("timeSeries", []):
        valid_time = datetime.datetime.fromisoformat(
            t["validTime"].replace("Z", "+00:00")
        ).astimezone(tz)
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
                "sst_tid": sst_tid,
                "water_quality": water_quality
            })

    # Utskrift
    if not prognoser:
        print("⚠️ Hittade inga prognoser kl 19!")
    else:
        for f in prognoser:
            status = "✅ Bra för snorkling" if snorkling_ok(f) else "❌ Inte optimalt"
            wind_arrow = wind_direction_arrow(f["wd"])
            msg = (
                f"Väder kl 19:00 den {f['datum']} – {status}\n"
                f"Temp: {f['t']}°C, Vind: {f['ws']} m/s {wind_arrow}, Byar: {f['gust']} m/s\n"
                f"Nederbörd: {f['r']} mm, Molnighet: {f['tcc_mean']} /8\n"
                f"Havstemperatur (Stockevik): {f['sst']}°C (mätt {f['sst_tid']}), "
                f"Vattenkvalitet: {f['water_quality']}"
            )
            print(msg)

if __name__ == "__main__":
    main()
