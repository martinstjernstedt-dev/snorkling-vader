import requests
from datetime import datetime

# Koordinater (Lysekil)
LAT = 58.2746
LON = 11.4350

def hamta_vader():
    url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{LON}/lat/{LAT}/data.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def bra_for_snorkling(data):
    forecast = data["timeSeries"][0]
    params = {p["name"]: p["values"][0] for p in forecast["parameters"]}

    temp = params["t"]          # °C
    vind = params["ws"]         # m/s
    moln = params["tcc_mean"]   # 0–8

    ok = (temp > 15 and vind < 5 and moln < 6)
    return ok, temp, vind, moln

def main():
    data = hamta_vader()
    ok, temp, vind, moln = bra_for_snorkling(data)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if ok:
        print(f"✅ {now}: Bra snorkeldag! Temp {temp}°C, Vind {vind} m/s, Moln {moln}/8")
    else:
        print(f"❌ {now}: Inte optimalt. Temp {temp}°C, Vind {vind} m/s, Moln {moln}/8")

if __name__ == "__main__":
    main()