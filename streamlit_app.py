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
        return yf.Ticker(ticker).history(period=periodo)
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

activo_selector = st.sidebar.text_input("Seleccionar activo (ej: SPY, QQQ, AAPL)", "SPY")

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
    sp500 = obtener_precio("^GSPC")
    st.metric("S&P 500", sp500)

with col2:
    nasdaq = obtener_precio("^IXIC")
    st.metric("Nasdaq", nasdaq)

with col3:
    eurostoxx = obtener_precio("^STOXX50E")
    st.metric("EuroStoxx 50", eurostoxx)

col4, col5, col6 = st.columns(3)

with col4:
    nikkei = obtener_precio("^N225")
    st.metric("Nikkei 225", nikkei)

with col5:
    vix = obtener_precio("^VIX")
    st.metric("VIX (Volatilidad)", vix)

with col6:
    hyg = obtener_precio("HYG")
    st.metric("High Yield (HYG)", hyg)

# ============================================================
# BLOQUE 2 — CURVA DE TIPOS REAL
# ============================================================
st.header("📉 Curva de Tipos USA (Real)")

bono_2y = obtener_precio("^IRX")
bono_10y = obtener_precio("^TNX") / 10 if obtener_precio("^TNX") else None

curva = bono_10y - bono_2y if bono_10y and bono_2y else None

st.metric("Pendiente 10y - 2y", f"{curva:.2f}%" if curva else "N/A")

# ============================================================
# BLOQUE 3 — ETFs (incluye UCITS)
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
# BLOQUE 4 — LIQUIDEZ GLOBAL (PROXY PROFESIONAL)
# ============================================================
st.header("🌍 Liquidez Global (Proxy)")

if vix and hyg:
    liquidez_global = (obtener_precio("SPY") / vix) * (hyg / 100)
else:
    liquidez_global = None

st.metric("Índice de Liquidez Global (proxy)", f"{liquidez_global:.2f}" if liquidez_global else "N/A")

# ============================================================
# BLOQUE 5 — RIESGO SISTÉMICO (PROXY PROFESIONAL)
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
# BLOQUE 6 — ESCENARIOS PROBABILÍSTICOS
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
# BLOQUE 7 — PANEL DE SENTIMIENTO (OPCIONAL)
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
# BLOQUE 8 — PANEL DE TENDENCIAS (OPCIONAL)
# ============================================================
if mostrar_tendencias:
    st.header("📈 Panel de Tendencias")

    hist = obtener_hist(activo_selector, "6mo")
    if hist is not None and not hist.empty:
        hist["MA20"] = hist["Close"].rolling(20).mean()
        hist["MA50"] = hist["Close"].rolling(50).mean()

        if mostrar_graficos:
            st.line_chart(hist[["Close", "MA20", "MA50"]])
    else:
        st.write("⚠️ No se pudo obtener el histórico del activo.")

# ============================================================
# BLOQUE 9 — ALERTAS AUTOMÁTICAS (OPCIONAL)
# ============================================================
if mostrar_alertas:
    st.header("🚨 Alertas Automáticas")

    if curva and curva < 0:
        st.write("🔴 Alerta: Curva invertida (riesgo de recesión).")

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
    resumen.append("🔴 La curva de tipos está invertida.")
else:
    resumen.append("🟢 La curva de tipos es normal.")

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
