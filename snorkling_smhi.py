# HaV badplatsdata för Stockevik
def hamta_stockevik():
    url = "https://badplatsen.havochvatten.se/badplatsen/api/detail?id=SE0A21484000000552"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def main():
    tz = pytz.timezone("Europe/Stockholm")

    vader_data = hamta_vader()
    bad_data = hamta_stockevik()

    # bad_data är en lista -> ta första elementet
    if isinstance(bad_data, list) and bad_data:
        bad_data = bad_data[0]

    # Plocka vattentemperatur från första observationen (om finns)
    if "observations" in bad_data and bad_data["observations"]:
        sst = bad_data["observations"][0].get("vattentemperatur", "?")
        sst_tid = bad_data["observations"][0].get("observationstid", "")
    else:
        sst = "?"
        sst_tid = ""

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
                "sst_tid": sst_tid,
                "water_quality": water_quality
            })

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
