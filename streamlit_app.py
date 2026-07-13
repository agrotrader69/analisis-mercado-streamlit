import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(page_title="Análisis de Mercado Profesional", layout="wide")
st.title("📈 Panel Profesional de Análisis de Mercado")
st.write("Panel profesional con indicadores, liquidez, riesgo sistémico, sentimiento y escenarios.")

# ============================================================
# FUNCIONES DE DATOS
# ============================================================
def obtener_precio(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        return float(data["Close"].iloc[-1])
    except:
        return None

def obtener_hist(ticker, periodo="6mo"):
    try:
        data = yf.Ticker(ticker).history(period=periodo)
        if data is None or data.empty:
            return None
        return data
    except:
        return None

# ============================================================
# DETECTAR SI ES ISIN Y CONVERTIRLO A TICKER
# ============================================================
def convertir_isin_a_ticker(isin):
    """
    Convierte un ISIN a ticker usando Morningstar.
    """
    try:
        url = f"https://www.morningstar.com/equities/{isin}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        # Morningstar muestra el ticker en un span con data-test="security-header-ticker"
        ticker_tag = soup.find("span", {"data-test": "security-header-ticker"})
        if ticker_tag:
            return ticker_tag.text.strip()
        return None
    except:
        return None

def resolver_activo(user_input):
    """
    Detecta si el usuario ha escrito un ISIN o un ticker.
    Si es ISIN, lo convierte a ticker.
    """
    user_input = user_input.strip().upper()

    # Detectar ISIN (2 letras + 10 números)
    if len(user_input) == 12 and user_input[:2].isalpha() and user_input[2:].isdigit():
        ticker = convertir_isin_a_ticker(user_input)
        return ticker if ticker else None

    # Si no es ISIN, es ticker
    return user_input

# ============================================================
# MENÚ LATERAL
# ============================================================
st.sidebar.header("⚙️ Opciones del Panel")

mostrar_graficos = st.sidebar.checkbox("Mostrar gráficos", value=False)
mostrar_sentimiento = st.sidebar.checkbox("Mostrar panel de sentimiento", value=True)
mostrar_tendencias = st.sidebar.checkbox("Mostrar panel de tendencias", value=False)
mostrar_alertas = st.sidebar.checkbox("Mostrar alertas automáticas", value=True)

activo_selector_raw = st.sidebar.text_input("Buscar activo (Ticker o ISIN)", "SPY")
activo_selector = resolver_activo(activo_selector_raw)

# ============================================================
# INDICADORES REALES DEL MERCADO
# ============================================================
st.header("📡 Indicadores en Tiempo Real")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("S&P 500", obtener_precio("^GSPC"))

with col2:
    st.metric("Nasdaq", obtener_precio("^IXIC"))

with col3:
    st.metric("EuroStoxx 50", obtener_precio("^STOXX50E"))

col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Nikkei 225", obtener_precio("^N225"))

with col5:
    vix = obtener_precio("^VIX")
    st.metric("VIX (Volatilidad)", vix)

with col6:
    hyg = obtener_precio("HYG")
    st.metric("High Yield (HYG)", hyg)

# ============================================================
# ACTIVO BUSCADO (TICKER O ISIN)
# ============================================================
st.subheader("🔍 Activo buscado")

if activo_selector:
    precio = obtener_precio(activo_selector)
    hist = obtener_hist(activo_selector, "5d")

    if precio:
        variacion = None
        if hist is not None and len(hist) > 1:
            variacion = ((hist["Close"].iloc[-1] - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2]) * 100

        st.metric(f"{activo_selector} (último precio)", f"{precio:.2f}",
                  f"{variacion:.2f}%" if variacion else "N/A")

        if mostrar_graficos and hist is not None:
            st.line_chart(hist["Close"])
    else:
        st.write(f"⚠️ No se encontró información para '{activo_selector_raw}'.")
else:
    st.write("Introduce un ticker o ISIN en el panel lateral para ver su precio.")

# ============================================================
# CURVA DE TIPOS (PROXY 10y–5y)
# ============================================================
st.header("📉 Curva de Tipos USA (Proxy 10y–5y)")

bono_10y_raw = obtener_precio("^TNX")
bono_5y_raw = obtener_precio("^FVX")

if bono_10y_raw is not None and bono_5y_raw is not None:
    bono_10y = bono_10y_raw / 10.0
    bono_5y = bono_5y_raw / 10.0
    curva = bono_10y - bono_5y
    st.metric("Pendiente 10y - 5y (proxy)", f"{curva:.2f}%")
else:
    curva = None
    st.metric("Pendiente 10y - 5y (proxy)", "N/A")

# ============================================================
# ETFs GLOBALes
# ============================================================
st.header("📊 ETFs Globales y UCITS")

colA, colB, colC = st.columns(3)

with colA:
    st.metric("SPY (S&P 500)", obtener_precio("SPY"))

with colB:
    st.metric("QQQ (Nasdaq)", obtener_precio("QQQ"))

with colC:
    st.metric("MSCI World UCITS (EUNL.DE)", obtener_precio("EUNL.DE"))

colD, colE, colF = st.columns(3)

with colD:
    st.metric("S&P 500 UCITS (VUSA.L)", obtener_precio("VUSA.L"))

with colE:
    st.metric("Emerging Markets UCITS (VFEM.L)", obtener_precio("VFEM.L"))

with colF:
    st.metric("TLT (Bonos Largo Plazo)", obtener_precio("TLT"))

# ============================================================
# LIQUIDEZ GLOBAL
# ============================================================
st.header("🌍 Liquidez Global (Proxy)")

if vix and hyg:
    liquidez_global = (obtener_precio("SPY") / vix) * (hyg / 100)
else:
    liquidez_global = None

st.metric("Índice de Liquidez Global (proxy)", f"{liquidez_global:.2f}" if liquidez_global else "N/A")

# ============================================================
# RIESGO SISTÉMICO
# ============================================================
st.header("⚠️ Riesgo Sistémico (Proxy)")

riesgo_sistemico = 0
if vix:
    riesgo_sistemico += (vix / 20)
if curva and curva < 0:
    riesgo_sistemico += 1
if hyg and hyg < 80:
    riesgo_sistemico += 1

st.metric("Índice de Riesgo Sistémico (proxy)", f"{riesgo_sistemico:.2f}")

# ============================================================
# ESCENARIOS
# ============================================================
st.header("📊 Escenarios Probabilísticos Automáticos")

prob_recesion = max(0, min(100,
    (30 if curva and curva < 0 else 5) +
    (15 if vix and vix > 20 else 0) +
    (10 if liquidez_global and liquidez_global < 1 else 0)
))

prob_expansion = 100 - prob_recesion

st.subheader(f"Probabilidad de Recesión: {prob_recesion}%")
st.subheader(f"Probabilidad de Expansión: {prob_expansion}%")

# ============================================================
# PANEL DE SENTIMIENTO
# ============================================================
if mostrar_sentimiento:
    st.header("💬 Panel de Sentimiento del Mercado")

    if ultimo_pc and ultimo_pc > 1.2:
        st.write("🔴 Miedo institucional (put–call alto)")
    elif ultimo_pc and ultimo_pc < 0.8:
        st.write("🟢 Optimismo institucional (put–call bajo)")
    else:
        st.write("🟡 Sentimiento neutral")

    if vix and vix > 20:
        st.write("🔴 Volatilidad elevada")
    else:
        st.write("🟢 Volatilidad contenida")

# ============================================================
# ALERTAS AUTOMÁTICAS
# ============================================================
if mostrar_alertas:
    st.header("🚨 Alertas Automáticas")

    if curva and curva < 0:
        st.write("🟠 Aviso: Pendiente 10y–5y negativa (proxy). Interpretar con cautela.")

    if vix and vix > 20:
        st.write("🔴 Alerta: Volatilidad elevada.")

    if liquidez_global and liquidez_global < 1:
        st.write("🔴 Alerta: Liquidez global baja.")
