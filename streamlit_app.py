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
# DETECTAR SI ES ISIN Y CONVERTIRLO A TICKER (MORNINGSTAR)
# ============================================================
def convertir_isin_a_ticker(isin):
    try:
        url = f"https://www.morningstar.com/equities/{isin}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        ticker_tag = soup.find("span", {"data-test": "security-header-ticker"})
        if ticker_tag:
            return ticker_tag.text.strip().upper()
        return None
    except:
        return None

def resolver_activo(user_input):
    user_input = user_input.strip().upper()
    if len(user_input) == 12 and user_input[:2].isalpha() and user_input[2:].isdigit():
        ticker = convertir_isin_a_ticker(user_input)
        return ticker if ticker else None
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
# RATIO PUT–CALL
# ============================================================
st.header("⚖️ Ratio Put–Call (proxy CBOE)")

def obtener_putcall_yf():
    try:
        data = yf.Ticker("^PCR").history(period="6mo")
        data = data.reset_index()
        data.rename(columns={"Date": "Fecha", "Close": "PutCall"}, inplace=True)
        return data
    except:
        return None

df_pc = obtener_putcall_yf()

if df_pc is not None and not df_pc.empty:
    ultimo_pc = df_pc["PutCall"].iloc[-1]
    st.metric("Put–Call Ratio", f"{ultimo_pc:.2f}")

    if mostrar_graficos:
        st.line_chart(df_pc.set_index("Fecha")["PutCall"])

    if ultimo_pc > 1.2:
        st.write("🔴 Sentimiento bajista (muchos puts)")
    elif ultimo_pc < 0.8:
        st.write("🟢 Sentimiento alcista (muchos calls)")
    else:
        st.write("🟡 Sentimiento neutral")
else:
    ultimo_pc = None
    st.write("⚠️ No se pudo obtener el ratio put–call.")

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
    hist_busqueda = obtener_hist(activo_selector, "5d")

    if precio:
        variacion = None
        if hist_busqueda is not None and len(hist_busqueda) > 1:
            variacion = ((hist_busqueda["Close"].iloc[-1] - hist_busqueda["Close"].iloc[-2]) /
                         hist_busqueda["Close"].iloc[-2]) * 100

        st.metric(f"{activo_selector} (último precio)", f"{precio:.2f}",
                  f"{variacion:.2f}%" if variacion is not None else "N/A")

        if mostrar_graficos and hist_busqueda is not None:
            st.line_chart(hist_busqueda["Close"])
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

    if ultimo_pc is None:
        st.write("⚠️ Put–Call no disponible.")
    elif ultimo_pc > 1.2:
        st.write("🔴 Miedo institucional (put–call alto)")
    elif ultimo_pc < 0.8:
        st.write("🟢 Optimismo institucional (put–call bajo)")
    else:
        st.write("🟡 Sentimiento neutral")

    if vix and vix > 20:
        st.write("🔴 Volatilidad elevada")
    else:
        st.write("🟢 Volatilidad contenida")

# ============================================================
# PANEL DE TENDENCIAS
# ============================================================
if mostrar_tendencias:
    st.header("📈 Panel de Tendencias del Activo")

    ticker = activo_selector if activo_selector else None

    if ticker:
        precio_activo = obtener_precio(ticker)
        if precio_activo:
            st.metric(f"Precio actual de {ticker}", f"{precio_activo:.2f}")
        else:
            st.write(f"⚠️ No se pudo obtener el precio de {ticker}.")

        hist_tend = obtener_hist(ticker, "6mo")

        if hist_tend is not None and not hist_tend.empty:
            hist_tend["MA20"] = hist_tend["Close"].rolling(20).mean()
            hist_tend["MA50"] = hist_tend["Close"].rolling(50).mean()

            if mostrar_graficos:
                st.line_chart(hist_tend[["Close", "MA20", "MA50"]])

            ma20 = hist_tend["MA20"].iloc[-1]
            ma50 = hist_tend["MA50"].iloc[-1]

            if ma20 > ma50:
                st.write(f"🟢 Tendencia alcista en {ticker} (MA20 > MA50).")
            elif ma20 < ma50:
                st.write(f"🔴 Tendencia bajista en {ticker} (MA20 < MA50).")
            else:
                st.write(f"🟡 Tendencia neutral en {ticker}.")
        else:
            st.write(f"⚠️ No se pudo obtener el histórico de {ticker}.")
    else:
        st.write("⚠️ No se ha podido resolver el activo para el panel de tendencias.")

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

# ============================================================
# RESUMEN AUTOMÁTICO
# ============================================================
st.header("🧾 Resumen Automático del Mercado")

resumen = []

if vix and vix > 20:
    resumen.append("🔴 La volatilidad es elevada.")
else:
    resumen.append("🟢 La volatilidad es baja.")

if curva and curva < 0:
    resumen.append("🟠 La pendiente 10y–5y (proxy) es negativa. Señal a vigilar.")
elif curva:
    resumen.append("🟢 La pendiente 10y–5y (proxy) es positiva.")
else:
    resumen.append("⚠️ Curva de tipos no disponible.")

if liquidez_global and liquidez_global < 1:
    resumen.append("🔴 La liquidez global es baja.")
elif liquidez_global and liquidez_global < 2:
    resumen.append("🟡 Liquidez global moderada.")
else:
    resumen.append("🟢 Liquidez global alta.")

if riesgo_sistemico >= 3:
    resumen.append("🔴 Riesgo sistémico elevado.")
elif riesgo_sistemico == 2:
    resumen.append("🟡 Riesgo sistémico moderado.")
else:
    resumen.append("🟢 Riesgo sistémico bajo.")

if ultimo_pc is not None:
    if ultimo_pc > 1.2:
        resumen.append("🔴 Put–call indica miedo.")
    elif ultimo_pc < 0.8:
        resumen.append("🟢 Put–call indica optimismo.")
    else:
        resumen.append("🟡 Put–call neutral.")
else:
    resumen.append("⚠️ Put–call no disponible.")

for r in resumen:
    st.write(r)
