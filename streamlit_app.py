import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Configuración general
st.set_page_config(page_title="Análisis de Mercado Profesional", layout="wide")
st.title("📈 Panel Profesional de Análisis de Mercado")
st.write("Datos reales, señales institucionales, liquidez global, riesgo sistémico y escenarios automáticos.")

# ============================================================
# FUNCIÓN GENERAL PARA OBTENER DATOS
# ============================================================
def obtener_precio(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        return data["Close"].iloc[-1]
    except:
        return None

def obtener_hist(ticker, periodo="6mo"):
    try:
        return yf.Ticker(ticker).history(period=periodo)
    except:
        return None

# ============================================================
# BLOQUE — PUT/CALL REAL DESDE CBOE (SCRAPING)
# ============================================================
st.header("⚖️ Ratio Put–Call (Real desde CBOE)")

def obtener_putcall_cboe():
    url = "https://www.cboe.com/us/options/market_statistics/pc_ratio/"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table")
    if table is None:
        raise Exception("No se encontró la tabla en CBOE.")

    rows = table.find_all("tr")

    fechas = []
    valores = []

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        fecha = cols[0].text.strip()
        valor = cols[1].text.strip()

        try:
            valor_float = float(valor)
        except:
            continue

        fechas.append(fecha)
        valores.append(valor_float)

    df = pd.DataFrame({"Fecha": fechas, "PutCall": valores})
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df = df.sort_values("Fecha")

    return df

try:
    df_pc = obtener_putcall_cboe()
    ultimo_pc = df_pc["PutCall"].iloc[-1]

    st.metric("Put–Call Ratio (CBOE)", f"{ultimo_pc:.2f}")

    st.line_chart(df_pc.set_index("Fecha")["PutCall"])

    if ultimo_pc > 1.2:
        st.write("🔴 Sentimiento bajista (muchos puts)")
    elif ultimo_pc < 0.8:
        st.write("🟢 Sentimiento alcista (muchos calls)")
    else:
        st.write("🟡 Sentimiento neutral")

except Exception as e:
    st.write("⚠️ No se pudo obtener el Put–Call real desde CBOE.")
    st.write(e)

# ============================================================
# BLOQUE 1 — INDICADORES REALES DEL MERCADO
# ============================================================
st.header("📡 Indicadores en Tiempo Real")

col1, col2, col3 = st.columns(3)

with col1:
    sp500 = obtener_precio("^GSPC")
    st.metric("S&P 500", f"{sp500:.2f}")

with col2:
    nasdaq = obtener_precio("^IXIC")
    st.metric("Nasdaq", f"{nasdaq:.2f}")

with col3:
    eurostoxx = obtener_precicio("^STOXX50E")
    st.metric("EuroStoxx 50", f"{eurostoxx:.2f}")

col4, col5, col6 = st.columns(3)

with col4:
    nikkei = obtener_precio("^N225")
    st.metric("Nikkei 225", f"{nikkei:.2f}")

with col5:
    vix = obtener_precio("^VIX")
    st.metric("VIX (Volatilidad)", f"{vix:.2f}")

with col6:
    hyg = obtener_precio("HYG")
    st.metric("High Yield (HYG)", f"{hyg:.2f}")

# ============================================================
# BLOQUE 2 — CURVA DE TIPOS REAL
# ============================================================
st.header("📉 Curva de Tipos USA (Real)")

bono_2y = obtener_precio("^IRX")
bono_10y = obtener_precio("^TNX") / 10

curva = bono_10y - bono_2y

st.metric("Pendiente 10y - 2y", f"{curva:.2f}%")

# ============================================================
# BLOQUE 3 — ETFs (incluye UCITS)
# ============================================================
st.header("📊 ETFs Globales y UCITS")

colA, colB, colC = st.columns(3)

with colA:
    st.metric("SPY (S&P 500)", f"{obtener_precio('SPY'):.2f}")

with colB:
    st.metric("QQQ (Nasdaq)", f"{obtener_precio('QQQ'):.2f}")

with colC:
    st.metric("MSCI World UCITS (EUNL.DE)", f"{obtener_precio('EUNL.DE'):.2f}")

colD, colE, colF = st.columns(3)

with colD:
    st.metric("S&P 500 UCITS (VUSA.L)", f"{obtener_precio('VUSA.L'):.2f}")

with colE:
    st.metric("Emerging Markets UCITS (VFEM.L)", f"{obtener_precio('VFEM.L'):.2f}")

with colF:
    st.metric("TLT (Bonos Largo Plazo)", f"{obtener_precio('TLT'):.2f}")

# ============================================================
# BLOQUE 4 — LIQUIDEZ GLOBAL (PROXY PROFESIONAL)
# ============================================================
st.header("🌍 Liquidez Global (Proxy)")

liquidez_global = (obtener_precio("SPY") / vix) * (hyg / 100)

st.metric("Índice de Liquidez Global (proxy)", f"{liquidez_global:.2f}")

if liquidez_global < 1:
    st.write("🔴 Liquidez global baja")
elif liquidez_global < 2:
    st.write("🟡 Liquidez global moderada")
else:
    st.write("🟢 Liquidez global alta")

# ============================================================
# BLOQUE 5 — RIESGO SISTÉMICO (PROXY PROFESIONAL)
# ============================================================
st.header("⚠️ Riesgo Sistémico (Proxy)")

riesgo_sistemico = (vix / 20) + (1 if curva < 0 else 0) + (1 if hyg < 80 else 0)

st.metric("Índice de Riesgo Sistémico (proxy)", f"{riesgo_sistemico:.2f}")

if riesgo_sistemico >= 3:
    st.write("🔴 Riesgo sistémico elevado")
elif riesgo_sistemico == 2:
    st.write("🟡 Riesgo sistémico moderado")
else:
    st.write("🟢 Riesgo sistémico bajo")

# ============================================================
# BLOQUE 6 — ESCENARIOS PROBABILÍSTICOS
# ============================================================
st.header("📊 Escenarios Probabilísticos Automáticos")

prob_recesion = max(0, min(100, (30 if curva < 0 else 5) + (15 if vix > 20 else 0) + (10 if liquidez_global < 1 else 0)))
prob_expansion = max(0, min(100, 70 - prob_recesion))

st.subheader(f"Probabilidad de Recesión: {prob_recesion}%")
st.subheader(f"Probabilidad de Expansión: {prob_expansion}%")

# ============================================================
# BLOQUE 7 — PANEL DE RESUMEN AUTOMÁTICO
# ============================================================
st.header("🧾 Resumen Automático del Mercado")

resumen = []

# Volatilidad
if vix > 20:
    resumen.append("🔴 La volatilidad es elevada, el mercado está nervioso.")
else:
    resumen.append("🟢 La volatilidad es baja, el mercado está estable.")

# Curva de tipos
if curva < 0:
    resumen.append("🔴 La curva de tipos está invertida, señal clásica de recesión.")
else:
    resumen.append("🟢 La curva de tipos es normal, entorno más saludable.")

# Liquidez global
if liquidez_global < 1:
    resumen.append("🔴 La liquidez global es baja, riesgo de caídas.")
elif liquidez_global < 2:
    resumen.append("🟡 La liquidez global es moderada.")
else:
    resumen.append("🟢 La liquidez global es alta, soporte para subidas.")

# Riesgo sistémico
if riesgo_sistemico >= 3:
    resumen.append("🔴 El riesgo sistémico es elevado, precaución.")
elif riesgo_sistemico == 2:
    resumen.append("🟡 El riesgo sistémico es moderado.")
else:
    resumen.append("🟢 El riesgo sistémico es bajo.")

# Put–call
if ultimo_pc > 1.2:
    resumen.append("🔴 El ratio put–call indica miedo en el mercado.")
elif ultimo_pc < 0.8:
    resumen.append("🟢 El ratio put–call indica optimismo.")
else:
    resumen.append("🟡 El ratio put–call indica neutralidad.")

for r in resumen:
    st.write(r)
