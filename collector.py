import os
import json
import time
import requests
from datetime import datetime

API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "224011768fed4370b5bb6e19de465c98")

TICKERS = [
    # Monedas y Cripto
    "USD/ARS", "EUR/USD", "BTC/USD", "ETH/USD", "SOL/USD",
    # ADRs Argentina principales
    "GGAL", "YPF", "BMA", "PAM", "MELI", "GLOB", "VIST", "TX",
    # Tech / USA
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "PLTR"
]

def obtener_precios_e_historial():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    # Cargar historial previo si existe
    historial = {}
    if os.path.exists("historial.json"):
        try:
            with open("historial.json", "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    precios_hoy = {}

    for i, ticker in enumerate(TICKERS):
        url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={API_KEY}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            if "price" in data and data["price"]:
                precio = float(data["price"])
                precios_hoy[ticker] = precio

                if ticker not in historial:
                    historial[ticker] = []

                # Evitar duplicados del mismo día
                historial[ticker] = [r for r in historial[ticker] if r.get("fecha") != fecha_hoy]
                historial[ticker].append({"fecha": fecha_hoy, "precio": precio})
                # Mantener ventana de 30 días
                historial[ticker] = historial[ticker][-30:]
                print(f"[{i+1}/{len(TICKERS)}] OK: {ticker} -> {precio}")
            else:
                print(f"[{i+1}/{len(TICKERS)}] Error con {ticker}: {data.get('message', 'Sin precio')}")
        except Exception as e:
            print(f"Error conectando a {ticker}: {e}")

        # Respetar rate limit (8 calls/min -> 8 seg por llamada)
        time.sleep(8)

    with open("precios.json", "w", encoding="utf-8") as f:
        json.dump(precios_hoy, f, indent=2)

    with open("historial.json", "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2)

    print("Actualización completada exitosamente.")

if __name__ == "__main__":
    obtener_precios_e_historial()
