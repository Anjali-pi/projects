# app.py
import streamlit as st
import joblib
import numpy as np
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
import sqlite3
from io import BytesIO
from datetime import datetime
import os
import urllib.request

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="💖 Heart Health — Ultra Pro+",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------
# CSS
# ---------------------------------
st.markdown(
    """
    <style>
        .glass { background:rgba(255,255,255,0.05); padding:18px;
                 border-radius:12px; backdrop-filter:blur(6px); }
        .heartbeat { font-size:55px; animation:beat 1.6s infinite; }
        @keyframes beat { 0%{transform:scale(1);}25%{transform:scale(1.2);}
                          50%{transform:scale(1);} }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------
# HEADER
# ---------------------------------
st.markdown("<h1>💖 HeartEase AI — Peace of mind in every beat.</h1>", unsafe_allow_html=True)

# ---------------------------------
# LOAD MODEL
# ---------------------------------
MODEL_PATH = "heart_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
except:
    model = None
    st.error("❌ Could not load model. Put heart_model.pkl in app folder.")

# ---------------------------------
# DATABASE
# ---------------------------------
conn = sqlite3.connect("predictions.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    age INTEGER, sex TEXT, cp INTEGER, trestbps INTEGER, chol INTEGER,
    fbs INTEGER, restecg INTEGER, thalach INTEGER, exang INTEGER,
    oldpeak REAL, slope INTEGER, ca INTEGER, thal INTEGER,
    prediction TEXT, risk_pct REAL, timestamp TEXT
)
""")
conn.commit()

# ---------------------------------
# FONT FOR PDF
# ---------------------------------
font_path = "NotoSans-Regular.ttf"

def ensure_font():
    if os.path.exists(font_path):
        return True
    try:
        urllib.request.urlretrieve(
            "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
            font_path
        )
        return True
    except:
        return False

ensure_font()

# ---------------------------------
# PDF GENERATION
# ---------------------------------
def make_pdf_report(data):
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.add_font("NotoSans", "", font_path, uni=True)
        pdf.set_font("NotoSans", size=14)
    except:
        pdf.set_font("Helvetica", size=14)

    pdf.cell(0, 10, "Heart Health Report", ln=True, align="C")
    pdf.ln(5)

    for k, v in data.items():
        txt = f"{k}: {v}"
        txt = txt.encode("ascii", "ignore").decode()
        pdf.multi_cell(0, 8, txt)

    return BytesIO(pdf.output(dest="S").encode("latin-1", "ignore"))

# ---------------------------------
# EXCEL EXPORT
# ---------------------------------
def df_to_excel_bytes(df):
    out = BytesIO()
    try:
        df.to_excel(out, index=False, engine="openpyxl")
    except:
        out = BytesIO(df.to_csv(index=False).encode())
    out.seek(0)
    return out

# ---------------------------------
# UI FORM
# ---------------------------------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
st.subheader("🩺 Patient Information")

c1, c2, c3 = st.columns(3)
with c1:
    age = st.number_input("Age", 1, 120, 45)
    sex = st.selectbox("Sex", ["Male", "Female"])
    cp = st.selectbox("Chest Pain Type (0-3)", [0,1,2,3])
with c2:
    trestbps = st.number_input("Resting BP", 50, 250, 120)
    chol = st.number_input("Cholesterol", 100, 600, 230)
    fbs = st.selectbox("Fasting Sugar >120 (0/1)", [0,1])
with c3:
    restecg = st.selectbox("Rest ECG (0-2)", [0,1,2])
    thalach = st.number_input("Max Heart Rate", 60, 250, 150)
    exang = st.selectbox("Exercise Angina (0/1)", [0,1])

c4, c5, c6 = st.columns(3)
with c4:
    oldpeak = st.slider("Oldpeak", 0.0, 6.0, 1.0)
with c5:
    slope = st.selectbox("Slope (0-2)", [0,1,2])
with c6:
    ca = st.selectbox("Major Vessels (0-3)", [0,1,2,3])

thal = st.selectbox("Thalassemia (0-3)", [0,1,2,3])

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------
# PREDICTION
# ---------------------------------
if st.button("🔍 Analyze My Heart Health"):

    if model is None:
        st.error("Model not loaded.")
    else:
        sex_val = 1 if sex == "Male" else 0

        X = np.array([[age, sex_val, cp, trestbps, chol, fbs, restecg,
                       thalach, exang, oldpeak, slope, ca, thal]], dtype=float)

        with st.spinner("Analyzing..."):
            import time; time.sleep(1)

        try:
            prob = float(model.predict_proba(X)[0,1])
            pred_raw = int(model.predict(X)[0])
        except:
            pred_raw = 1
            prob = 0.75

        risk_pct = int(prob * 100)
        result_text = "High Risk" if pred_raw == 1 else "Low Risk"

        # Result Card
        st.markdown(
            f"""
            <div class='glass' style='text-align:center;'>
                <div class='heartbeat'>💓</div>
                <h2>{'🚨 High Risk' if pred_raw else '💚 Low Risk'}</h2>
                <p>Risk Percentage: <b>{risk_pct}%</b></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # SAVE TO HISTORY
        cursor.execute("""
            INSERT INTO predictions VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang,
            oldpeak, slope, ca, thal, result_text, risk_pct,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        conn.commit()

        # EXPORT BUTTONS
        st.subheader("📁 Export Report")

        report = {
            "Age": age,
            "Sex": sex,
            "BP": trestbps,
            "Cholesterol": chol,
            "Max HR": thalach,
            "Risk %": f"{risk_pct}%",
            "Result": result_text,
        }

        colA, colB = st.columns(2)
        with colA:
            st.download_button("📄 Download PDF", make_pdf_report(report),
                               file_name="heart_report.pdf", mime="application/pdf")

        with colB:
            st.download_button("📊 Download Excel", df_to_excel_bytes(pd.DataFrame([report])),
                               file_name="heart_report.xlsx")

# ---------------------------------
# SIDEBAR HISTORY
# ---------------------------------
with st.sidebar:
    st.header("📜 History")
    if st.button("Show History"):
        df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
        st.dataframe(df)
        st.download_button("Download History (Excel)",
                           df_to_excel_bytes(df),
                           file_name="all_history.xlsx")

# ---------------------------------
# FOOTER
# ---------------------------------
st.markdown("<p style='text-align:center;'>Built By ❤ — Anjali Yadav</p>",
            unsafe_allow_html=True)
