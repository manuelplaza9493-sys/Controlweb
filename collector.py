import os
import time
import json
from datetime import datetime
import requests

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "224011768fed4370b5bb6e19de465c98")

# LISTA COMPLETA DE 80 ACTIVOS (COINCIDE EXACTAMENTE CON LA WEB)
ACTIVOS = [
    # Commodities, Cripto & Monedas (10)
    "BTC/USD", "ETH/USD", "SOL/USD", "PAXG/USD", "USO", "BNO", "SLV", "EUR/USD", "USD/ARS", "XAU/USD",
    
    # Argentina Top 20 (ADRs Wall Street)
    "GGAL", "BMA", "YPF", "PAM", "MELI", "GLOB", "VIST", "TX", "CRES", "EDN",
    "TGS", "BBAR", "TEO", "CEPU", "IRS", "SUPV", "BIOX", "LOMA", "DESP", "CAAP",
    
    # Tecnología Top 10
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NFLX", "ADBE", "CRM", "ORCL",
    
    # IA & Semiconductores Top 10
    "NVDA", "AMD", "TSM", "AVGO", "ASML", "QCOM", "INTC", "ARM", "PLTR", "MU",
    
    # Minería & Litio Top 10
    "BHP", "RIO", "VALE", "FCX", "ALB", "SCCO", "NEM", "GOLD", "SQM", "ALTM",
    
    # Real Estate Top 10
    "PLD", "AMT", "EQIX", "PSA", "O", "SPG", "WELL", "DLR", "CCI", "CBRE",
    
    # Alimentos & Consumo Top 10
    "KO", "PEP", "PG", "MDLZ", "PM", "MO", "CL", "KMB", "HSY", "GIS",
    
    # Automotriz Top 10
    "TM", "F", "GM", "STLA", "HMC", "RACE", "MBGYY", "VWAGY", "RIVN"
]

def cargar_json(nombre_archivo, default):
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def guardar_json(nombre_archivo, datos):
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

def main():
    precios_actuales = cargar_json("precios.json", {})
    historial = cargar_json("historial.json", {})
    fecha_hoy = datetime.utcnow().strftime("%Y-%m-%d")

    # Dividir los activos en lotes de 8 para respetar el límite de 8 req/min de Twelve Data
    tamano_lote = 8
    lotes = [ACTIVOS[i:i + tamano_lote] for i in range(0, len(ACTIVOS), tamano_lote)]

    print(f"Iniciando recolección de {len(ACTIVOS)} activos en {len(lotes)} lotes...")

    for idx, lote in enumerate(lotes):
        simbolos_str = ",".join(lote)
        url = f"https://api.twelvedata.com/price?symbol={simbolos_str}&apikey={API_KEY}"
        
        try:
            print(f"Consultando Lote {idx + 1}/{len(lotes)}: {lote}")
            res = requests.get(url, timeout=20)
            data = res.json()

            for ticker in lote:
                precio = None
                # Si el lote trajo un solo activo o múltiples
                if len(lote) == 1 and "price" in data:
                    precio = data.get("price")
                elif ticker in data and "price" in data[ticker]:
                    precio = data[ticker].get("price")

                if precio:
                    try:
                        p_float = float(precio)
                        precios_actuales[ticker] = p_float

                        # Guardar en historial
                        if ticker not in historial:
                            historial[ticker] = []

                        # Evitar duplicar la fecha de hoy
                        historial[ticker] = [h for h in historial[ticker] if h.get("fecha") != fecha_hoy]
                        historial[ticker].append({"fecha": fecha_hoy, "precio": p_float})

                        # Mantener solo los últimos 30 días
                        if len(historial[ticker]) > 30:
                            historial[ticker] = historial[ticker][-30:]

                    except ValueError:
                        pass
                else:
                    print(f"  [Aviso] No se obtuvo precio para {ticker}")

        except Exception as e:
            print(f"Error consultando lote {idx + 1}: {e}")

        # Guardado progresivo tras cada lote
        guardar_json("precios.json", precios_actuales)
        guardar_json("historial.json", historial)

        # Pausa obligatoria entre lotes si quedan lotes pendientes (Twelve Data free tier)
        if idx < len(lotes) - 1:
            print("Esperando 65 segundos para respetar el límite de Twelve Data...")
            time.sleep(65)

    print("Recolección completada con éxito. Archivos actualizados.")

if __name__ == "__main__":
    main()
