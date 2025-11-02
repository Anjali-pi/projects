
import streamlit as st
import numpy as np
import joblib

# ---- PAGE SETTINGS ----
st.set_page_config(page_title="Heart Disease Predictor", page_icon="❤️", layout="wide")

# ---- CUSTOM STYLING ----
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
    }
    h1 {
        text-align: center;
        color: #d62828;
        font-weight: 900;
    }
    .stButton>button {
        background-color: #ff4d4d;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 16px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ff8080;
        color: #fff;
    }
    .result-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3784/3784184.png", width=100)
st.sidebar.title("💖 About This App")
st.sidebar.info("""
This Heart Disease Predictor uses **Machine Learning** to analyze patient data and predict the likelihood of heart disease.

**Developed by:** Anjali Singh Yadav  
**Branch:** CSE (AI)
""")
st.sidebar.markdown("---")
st.sidebar.success("Tip: Fill all fields carefully before prediction.")

# ---- MAIN HEADER ----
st.markdown("<h1>Heart Disease Predictor Using Machine Learning</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---- PATIENT DETAILS ----
st.subheader("🩺 Patient Details")
col1, col2, col3 = st.columns(3)
with col1:
    patient_id = st.text_input("Patient ID")
with col2:
    patient_name = st.text_input("Patient Name")
with col3:
    patient_age = st.number_input("Age", 1, 120, 30)

col1, col2 = st.columns(2)
with col1:
    patient_email = st.text_input("Email")
with col2:
    sex = st.selectbox("Sex", ["Male", "Female"])
    sex = 1 if sex == "Male" else 0

st.markdown("---")

# ---- MEDICAL DETAILS ----
st.subheader("📋 Medical Information")

col1, col2, col3 = st.columns(3)
with col1:
    cp = st.selectbox("Chest Pain Type (0-3)", [0, 1, 2, 3])
    trestbps = st.number_input("Resting Blood Pressure", 90, 200, 120)
    chol = st.number_input("Cholesterol (mg/dl)", 100, 600, 200)
with col2:
    fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dl", [1, 0])
    restecg = st.selectbox("Resting ECG (0-2)", [0, 1, 2])
    thalach = st.number_input("Max Heart Rate", 60, 220, 150)
with col3:
    exang = st.selectbox("Exercise Induced Angina (1=Yes, 0=No)", [1, 0])
    oldpeak = st.number_input("ST Depression", 0.0, 10.0, 1.0)
    slope = st.selectbox("Slope of Peak Exercise ST Segment", [0, 1, 2])

col1, col2 = st.columns(2)
with col1:
    ca = st.selectbox("Major Vessels (0-4)", [0, 1, 2, 3, 4])
with col2:
    thal = st.selectbox("Thalassemia (1=Normal, 2=Fixed defect, 3=Reversible defect)", [1, 2, 3])

st.markdown("---")

# ---- PREDICTION SECTION ----
model = joblib.load("heart_model.pkl")

if st.button("🔍 Predict Heart Disease"):
    features = np.array([[patient_age, sex, cp, trestbps, chol, fbs, restecg,
                          thalach, exang, oldpeak, slope, ca, thal]])
    prediction = model.predict(features)

    if prediction[0] == 1:
        st.markdown(
            f"<div class='result-box' style='background-color:#00404D;'>⚠️ "
            f"<b>{patient_name}</b> (ID: {patient_id}) is likely to have <b>Heart Disease.</b></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='result-box' style='background-color:#85f7ff;'>💖 "
            f"<b>{patient_name}</b> (ID: {patient_id}) is likely *not* to have Heart Disease.</div>",
            unsafe_allow_html=True
        )