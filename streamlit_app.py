import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuración general
st.set_page_config(page_title="Análisis de Mercado Profesional", layout="wide")
st.title("📈 Panel Profesional de Análisis de Mercado")
st.write("Panel profesional con indicadores, liquidez, riesgo sistémico, sentimiento y escenarios.")

# ============================================================
# FUNCIÓN GENERAL PARA OBTENER DATOS
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
# MENÚ LATERAL
# ============================================================
st.sidebar.header("⚙️ Opciones del Panel")

mostrar_graficos = st.sidebar.checkbox("Mostrar gráficos", value=False)
mostrar_sentimiento = st.sidebar.checkbox("Mostrar panel de sentimiento", value=True)
mostrar_tendencias = st.sidebar.checkbox("Mostrar panel de tendencias", value=False)
mostrar_alertas = st.sidebar.checkbox("Mostrar alertas automáticas", value=True)

activo_selector = st.sidebar.text_input("Buscar activo (ej: SPY, QQQ, AAPL)", "SPY")

# ============================================================
# BLOQUE — RATIO PUT–CALL (vía yfinance)
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
# BLOQUE 1 — INDICADORES REALES DEL MERCADO
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
# BLOQUE 2 — CURVA DE TIPOS (PROXY 10y–5y)
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
    st.write("⚠️ No se pudo obtener la curva de tipos (proxy).")

# ============================================================
# BLOQUE 3 — ETFs Globales
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
# BLOQUE 4 — LIQUIDEZ GLOBAL
# ============================================================
st.header("🌍 Liquidez Global (Proxy)")

if vix and hyg:
    liquidez_global = (obtener_precio("SPY") / vix) * (hyg / 100)
else:
    liquidez_global = None

st.metric("Índice de Liquidez Global (proxy)", f"{liquidez_global:.2f}" if liquidez_global else "N/A")

# ============================================================
# BLOQUE 5 — RIESGO SISTÉMICO
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
# BLOQUE 6 — ESCENARIOS
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
# BLOQUE 7 — PANEL DE SENTIMIENTO
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
# BLOQUE 8 — PANEL DE TENDENCIAS
# ============================================================
if mostrar_tendencias:
    st.header("📈 Panel de Tendencias")

    hist = obtener_hist(activo_selector, "6mo")
    if hist is not None:
        hist["MA20"] = hist["Close"].rolling(20).mean()
        hist["MA50"] = hist["Close"].rolling(50).mean()

        if mostrar_graficos:
            st.line_chart(hist[["Close", "MA20", "MA50"]])
    else:
        st.write("⚠️ No se pudo obtener el histórico del activo.")

# ============================================================
# BLOQUE 9 — ALERTAS AUTOMÁTICAS
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
# BLOQUE 10 — RESUMEN AUTOMÁTICO
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
