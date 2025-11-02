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
import platform

# -------------------------------
# PAGE CONFIG & THEME
# -------------------------------
st.set_page_config(
    page_title="💖 Heart Health — Ultra Pro+",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for modern UI: glass cards, neon accents, animations
st.markdown(
    """
    <style>
    /* Base */
    :root {
      --accent1: #ff3d81;
      --accent2: #8b5cf6;
      --glass: rgba(255,255,255,0.04);
      --glass-contrast: rgba(255,255,255,0.06);
      --muted: rgba(255,255,255,0.65);
    }
    [data-theme="light"] {
      --bg: #f6f7fb;
      --text: #1f1b2e;
      --glass: rgba(0,0,0,0.03);
      --muted: rgba(0,0,0,0.6);
    }
    [data-theme="dark"] {
      --bg: #050014;
      --text: #eae7f5;
      --glass: rgba(255,255,255,0.03);
      --muted: rgba(255,255,255,0.65);
    }

    /* Body and layout */
    html, body, [data-testid="stAppViewContainer"] {
      background: radial-gradient(1200px 600px at 10% 10%, rgba(139,92,246,0.06), transparent),
                  radial-gradient(1000px 500px at 90% 90%, rgba(255,61,129,0.04), transparent),
                  var(--bg) !important;
      color: var(--text) !important;
      transition: background 0.6s ease, color 0.6s ease;
    }

    /* Glass card */
    .glass {
      background: var(--glass);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 6px 30px rgba(2,6,23,0.12);
      border: 1px solid rgba(255,255,255,0.03);
      backdrop-filter: blur(6px) saturate(140%);
      transition: transform .25s ease, box-shadow .25s ease;
    }
    .glass:hover { transform: translateY(-8px); box-shadow: 0 18px 60px rgba(139,92,246,0.12); }

    /* Header */
    .app-header {
      display:flex; align-items:center; gap:12px; justify-content:space-between;
      width:100%;
    }
    .title {
      display:flex; align-items:center; gap:12px;
    }
    .title h1 { margin:0; font-size:28px; letter-spacing:0.2px; }
    .title .tag { color: var(--muted); font-size:13px; }

    /* Buttons */
    .btn-primary {
      background: linear-gradient(90deg, var(--accent1), var(--accent2));
      color:white; padding:8px 14px; border-radius:10px; border:none; cursor:pointer;
      font-weight:600;
      box-shadow: 0 6px 30px rgba(255,61,129,0.08);
    }

    /* Result heartbeat */
    .heartbeat {
      font-size:56px; text-align:center; animation: heartbeat 1.6s infinite;
      filter: drop-shadow(0 8px 30px rgba(255,61,129,0.18));
    }
    @keyframes heartbeat {
      0% { transform: scale(1); }
      25% { transform: scale(1.25); }
      50% { transform: scale(1); }
      75% { transform: scale(1.15); }
      100% { transform: scale(1); }
    }

    /* small muted */
    .small-muted { color: var(--muted); font-size:0.95rem; }

    /* layout tweaks */
    .top-row { display:flex; gap:18px; align-items:flex-start; margin-bottom:18px; }
    .left-col { flex: 1 1 520px; }
    .right-col { width:360px; }

    /* responsive */
    @media (max-width: 900px) {
      .top-row { flex-direction:column; }
      .right-col { width:100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# HEADER
# -------------------------------
st.markdown(
    f"""
    <div class="app-header">
      <div class="title">
        <h1>💖 HeartEase AI — “Peace of mind in every beat.”</h1>
        <div class="tag small-muted">Your Health Insights · Export & Share with Care</div>
      </div>
      <div>
        <button class="btn-primary" onclick="window.scrollTo(0, document.body.scrollHeight);">Try Demo ↓</button>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# MODEL LOAD
# -------------------------------
MODEL_PATH = "heart_model.pkl"
model = None
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    st.error(f"❌ Failed to load model from {MODEL_PATH}. Error: {e}")

# -------------------------------
# DATABASE SETUP
# -------------------------------
DB_PATH = "predictions.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS predictions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      age INTEGER,
      sex TEXT,
      cp INTEGER,
      trestbps INTEGER,
      chol INTEGER,
      fbs INTEGER,
      restecg INTEGER,
      thalach INTEGER,
      exang INTEGER,
      oldpeak REAL,
      slope INTEGER,
      ca INTEGER,
      thal INTEGER,
      prediction TEXT,
      risk_pct REAL,
      timestamp TEXT
    )
    """
)
conn.commit()

# -------------------------------
# FONT FOR PDF (ensure available)
# -------------------------------
font_path = os.path.join(os.getcwd(), "NotoSans-Regular.ttf")


def ensure_font_available():
    if os.path.exists(font_path):
        return True
    # Try stable GoogleFonts GitHub path
    candidates = [
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
    ]
    for url in candidates:
        try:
            urllib.request.urlretrieve(url, font_path)
            return True
        except Exception:
            continue
    return False


_font_ok = ensure_font_available()
if not _font_ok:
    st.sidebar.warning("⚠️ Unicode font not available — PDF may omit emojis.")

# -------------------------------
# PDF generation (unicode-safe)
# -------------------------------
def make_pdf_report(data, title="Heart Health Report"):
    pdf = FPDF()
    pdf.add_page()

    # Add font
    try:
        if os.path.exists(font_path):
            pdf.add_font("NotoSans", "", font_path, uni=True)
            pdf.set_font("NotoSans", size=14)
        else:
            pdf.set_font("Helvetica", size=14)
    except Exception:
        pdf.set_font("Helvetica", size=14)

    # Title
    pdf.cell(0, 10, txt=title, ln=True, align="C")
    pdf.ln(6)

    # Use smaller font for details
    try:
        if os.path.exists(font_path):
            pdf.set_font("NotoSans", size=12)
        else:
            pdf.set_font("Helvetica", size=12)
    except Exception:
        pdf.set_font("Helvetica", size=12)

    # Safely print each key-value pair
    for k, v in data.items():
        try:
            text = f"{k}: {v}"
            # Ensure text is str and ASCII-safe
            text = str(text).encode("ascii", "ignore").decode("ascii")
            # Break extremely long lines
            if len(text) > 100:
                text = text[:100] + "..."
            pdf.multi_cell(0, 8, text)
        except Exception:
            continue

    # Output as bytes
    try:
        pdf_bytes = pdf.output(dest="S")
        if isinstance(pdf_bytes, (bytes, bytearray)):
            return BytesIO(pdf_bytes)
        else:
            return BytesIO(pdf_bytes.encode("latin-1", "ignore"))
    except Exception as e:
        print("PDF output failed:", e)
        return BytesIO()


# -------------------------------
# Utility: dataframe -> excel bytes
# -------------------------------
def df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    out = BytesIO()
    try:
        # prefer Excel, fallback to CSV
        df.to_excel(out, index=False, engine="openpyxl")
    except Exception:
        out = BytesIO(df.to_csv(index=False).encode("utf-8"))
    out.seek(0)
    return out


# -------------------------------
# UI Layout: Left (form) / Right (info)
# -------------------------------
st.markdown("<div class='top-row'>", unsafe_allow_html=True)
# left column
st.markdown("<div class='left-col'>", unsafe_allow_html=True)
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown("### 🩺 Patient Input")
cols = st.columns(3)
with cols[0]:
    age = st.number_input("Age", min_value=1, max_value=120, value=45)
    sex = st.selectbox("Sex", ["Male", "Female"])
    cp = st.selectbox("Chest Pain Type (0-3)", [0, 1, 2, 3])
with cols[1]:
    trestbps = st.number_input("Resting Blood Pressure (mm Hg)", min_value=50, max_value=240, value=120)
    chol = st.number_input("Cholesterol (mg/dl)", min_value=80, max_value=600, value=220)
    fbs = st.selectbox("Fasting Blood Sugar >120 mg/dl (0/1)", [0, 1])
with cols[2]:
    restecg = st.selectbox("Resting ECG (0-2)", [0, 1, 2])
    thalach = st.number_input("Max Heart Rate Achieved", min_value=60, max_value=250, value=150)
    exang = st.selectbox("Exercise Induced Angina (0/1)", [0, 1])

st.markdown("<br/>", unsafe_allow_html=True)
cols2 = st.columns(3)
with cols2[0]:
    oldpeak = st.slider("Oldpeak (ST depression)", 0.0, 6.0, 1.0)
with cols2[1]:
    slope = st.selectbox("Slope of Peak Exercise ST (0-2)", [0, 1, 2])
with cols2[2]:
    ca = st.selectbox("Number of Major Vessels (0–3)", [0, 1, 2, 3])
thal = st.selectbox("Thalassemia (0–3)", [0, 1, 2, 3])

st.markdown("</div>", unsafe_allow_html=True)  # close glass left
st.markdown("</div>", unsafe_allow_html=True)  # close left-col

# right column
st.markdown("<div class='right-col'>", unsafe_allow_html=True)
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown("### ⚙️ Controls & Export")
st.markdown("<div class='small-muted'>Use the buttons to export or share results after prediction.</div>", unsafe_allow_html=True)
st.markdown("<br/>", unsafe_allow_html=True)

# history toggle on sidebar (but also quick button here)
if st.button("🔍 Analyze My Heart Health", key="analyze_btn"):
    # run prediction
    if model is None:
        st.error("Cannot run prediction because the model failed to load. Place heart_model.pkl in the app folder.")
    else:
        sex_val = 1 if sex == "Male" else 0
        X = np.array([[age, sex_val, cp, trestbps, chol, fbs, restecg,
                       thalach, exang, oldpeak, slope, ca, thal]], dtype=float)

        with st.spinner("Analyzing..."):
            # small fake wait for UX
            import time as _t
            _t.sleep(0.9)

        try:
            prob = float(model.predict_proba(X)[0, 1])
            pred_raw = int(model.predict(X)[0])
        except Exception:
            pred_raw = int(model.predict(X)[0])
            prob = 0.85 if pred_raw == 1 else 0.12

        pred = pred_raw
        risk_pct = int(round(prob * 100))
        result_text = "High risk" if pred == 1 else "Low risk / Healthy"

        # Result card (big)
        col_left, col_right = st.columns([3, 1])
        with col_left:
            st.markdown(
                f"""
                <div class="glass" style="text-align:center;">
                  <div class="heartbeat">💓</div>
                  <h3 style="margin:0;color:{'#ef4444' if risk_pct>=70 else '#f59e0b' if risk_pct>=40 else '#22c55e'}">
                    {'🚨 High Risk' if pred==1 else '💚 Low Risk — Healthy'}
                  </h3>
                  <p>Estimated Risk: <b>{risk_pct}%</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_right:
            # mini export buttons
            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            report_data = {
                "Age": age, "Sex": sex, "Cholesterol": chol, "Blood Pressure": trestbps,
                "Max Heart Rate": thalach, "Risk Percentage (%)": f"{risk_pct}%", "Final Result": result_text,
                "Date of Analysis": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            pdf_bytes = make_pdf_report(report_data)
            st.download_button("📄 Download PDF", pdf_bytes, file_name="heart_report.pdf", mime="application/pdf")
            excel_df = pd.DataFrame([report_data])
            excel_bytes = df_to_excel_bytes(excel_df)
            st.download_button("📥 Download Excel", excel_bytes, file_name="heart_report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            # email form
            with st.expander("📧 Send Report via Email"):
                sender_email = st.text_input("Sender Gmail (for SMTP)", value="")
                sender_pass = st.text_input("App Password", type="password")
                receiver_email = st.text_input("Recipient Email", value="")
                send_btn = st.button("📤 Send Email", key="send_email")
                if send_btn:
                    if not sender_email or not sender_pass or not receiver_email:
                        st.warning("Fill sender email, app password and recipient email.")
                    else:
                        try:
                            # attach pdf_bytes
                            pdf_bytes.seek(0)
                            msg = MIMEMultipart()
                            msg["From"] = sender_email
                            msg["To"] = receiver_email
                            msg["Subject"] = f"Heart Health Report - {datetime.now().strftime('%Y-%m-%d')}"
                            msg.attach(MIMEText(f"Dear user,\n\nPlease find attached your Heart Health Report.\nRisk: {risk_pct}%\n\nRegards", "plain"))
                            attach = MIMEApplication(pdf_bytes.read(), _subtype="pdf")
                            attach.add_header("Content-Disposition", "attachment", filename="heart_report.pdf")
                            msg.attach(attach)
                            # use TLS
                            server = smtplib.SMTP("smtp.gmail.com", 587)
                            server.ehlo()
                            server.starttls()
                            server.login(sender_email, sender_pass)
                            server.send_message(msg)
                            server.quit()
                            st.success("✅ Email sent successfully.")
                        except Exception as e:
                            st.error(f"❌ Failed to send email: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        # store history locally
        history_row = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Age": age,
            "Cholesterol": chol,
            "BP": trestbps,
            "Risk%": risk_pct,
            "Result": "High" if pred else "Low",
        }
        history_path = os.path.join(os.getcwd(), "history.csv")
        if os.path.exists(history_path):
            hist_df = pd.read_csv(history_path)
        else:
            hist_df = pd.DataFrame(columns=["Date", "Age", "Cholesterol", "BP", "Risk%", "Result"])
        hist_df = pd.concat([hist_df, pd.DataFrame([history_row])], ignore_index=True)
        hist_df.to_csv(history_path, index=False)

        # save to sqlite
        cursor.execute(
            """
            INSERT INTO predictions (age, sex, cp, trestbps, chol, fbs, restecg,
                                     thalach, exang, oldpeak, slope, ca, thal,
                                     prediction, risk_pct, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang,
             oldpeak, slope, ca, thal, result_text, risk_pct, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()

st.markdown("</div>", unsafe_allow_html=True)  # close glass right
st.markdown("</div>", unsafe_allow_html=True)  # close right-col
st.markdown("</div>", unsafe_allow_html=True)  # close top-row

# -------------------------------
# SIDEBAR: History & Exports (toggle)
# -------------------------------
with st.sidebar:
    st.markdown("## 📂 History & Exports")
    if st.button("📜 Show History"):
        try:
            hist_df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
            st.dataframe(hist_df.head(200), use_container_width=True)
            st.markdown("### 📤 Export All Records")
            col1, col2 = st.columns(2)
            with col1:
                # export PDF of text (simple)
                pdf_all = make_pdf_report({"Export": "History export (see CSV for full details)"})
                st.download_button("📄 Download All (PDF)", pdf_all, file_name="all_history.pdf", mime="application/pdf")
            with col2:
                excel_all = df_to_excel_bytes(hist_df)
                st.download_button("📊 Download All (Excel)", excel_all, file_name="all_history.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"Could not load history: {e}")

# -------------------------------
# Footer / small note
# -------------------------------
st.markdown(
    """
    <div style="margin-top:18px;display:flex;justify-content:space-between;align-items:center;">
      <div class="small-muted">Built By ❤️ — Anjali Yadav</div>
    </div>
    """,
    unsafe_allow_html=True,
)
