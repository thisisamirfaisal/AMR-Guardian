# 🧬 AMR Guardian
### AI-Powered Antimicrobial Resistance Surveillance for Pakistan

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://amr-guardian-sdwsei69ybewaeeqcvemno.streamlit.app)
[![HuggingFace Space](https://img.shields.io/badge/🤗%20Hugging%20Face-Space-blue)](https://thisisamirfaisal-amr-guardian.hf.space)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Groq](https://img.shields.io/badge/Powered%20by-Groq%20llama--3.3--70b-orange)](https://groq.com)

---

## 🇵🇰 The Problem

Pakistan faces a severe antimicrobial resistance (AMR) crisis:

- **46.7%** average resistance rate across major pathogens
- **84%** of *Klebsiella pneumoniae* resistant to Ceftriaxone (WHO GLASS 2023)
- **87%** of *Streptococcus* resistant to Co-trimoxazole
- No centralized, publicly accessible AMR surveillance platform exists
- Doctors prescribe antibiotics with no real-time local resistance data

> A doctor in Peshawar prescribing Ciprofloxacin has no way to know it's failing against *E. coli* in their city — until their patient doesn't respond to treatment.

**AMR Guardian fixes this.**

---

## 🛡️ What It Does

AMR Guardian is a real-time AMR surveillance platform that:

| Feature | Description |
|---|---|
| 📄 **Lab Report Parser** | Paste or upload any lab culture report — Groq AI extracts organism, antibiotic, and resistance result automatically |
| 📊 **Resistance Dashboard** | Live charts showing resistance rates by organism, antibiotic, and city |
| 🗺️ **Pakistan City Map** | Interactive bubble map showing resistance intensity across Karachi, Lahore, Islamabad, Peshawar, Quetta |
| 📋 **AI Weekly Bulletin** | One-click generation of a clinician-ready AMR bulletin with treatment recommendations — powered by Groq |
| 🔬 **Lab Interpreter Chatbot** | Ask any question about a lab result and get expert clinical guidance |

---

## 🚀 Live Demo

| Platform | Link |
|---|---|
| **Streamlit Cloud** | [Launch App](https://amr-guardian-sdwsei69ybewaeeqcvemno.streamlit.app) |
| **Hugging Face** | [Launch App](https://thisisamirfaisal-amr-guardian.hf.space) |

---

## 🖼️ Screenshots

### Dashboard Overview
> KPI cards showing 300 isolates · 46.7% resistance rate · city breakdown

### AI Weekly Bulletin
> Groq generates a structured 5-section clinical bulletin in under 30 seconds

### Pakistan Resistance Map
> Bubble map coloured by resistance intensity across 5 major cities

---

## 🏗️ Architecture

```
Raw Lab Report (text / CSV)
        │
        ▼
┌───────────────────┐
│  Groq API Parser  │  ← llama-3.3-70b extracts structured JSON
│  (lab_report →    │
│   organism/abx/   │
│   result/city)    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Pandas Pipeline  │  ← computes resistance % per organism/antibiotic/city
│  + CLSI Breakpts  │  ← classifies S / I / R using WHO standards
└────────┬──────────┘
         │
    ┌────┴─────┐
    ▼          ▼
Dashboard   AI Bulletin
(Plotly)    (Groq llama-3.3-70b)
    │          │
    └────┬─────┘
         ▼
   Doctor in Peshawar
   prescribes the right
   antibiotic, first time ✅
```

---

## 🧪 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **AI / GenAI** | Groq API · llama-3.3-70b-versatile (free tier) |
| **Data processing** | Pandas |
| **Visualisation** | Plotly |
| **Deployment** | Streamlit Cloud · Hugging Face Spaces |
| **Dataset** | WHO GLASS Pakistan 2023 · 300 synthetic isolate records |

---

## 📁 Project Structure

```
amr-guardian/
├── app.py                # Main Streamlit application
├── amr_data.csv          # AMR dataset (300 isolate records, 5 cities)
├── requirements.txt      # Python dependencies
└── README.md
```

---

## ⚡ Run Locally

### Prerequisites
- Python 3.9+
- Free Groq API key from [console.groq.com](https://console.groq.com)

### Installation

```bash
git clone https://github.com/thisisamirfaisal/amr-guardian.git
cd amr-guardian
pip install -r requirements.txt
```

### Add your Groq API key

Create a file `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## ☁️ Deploy Your Own

### Streamlit Cloud (recommended)

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo → `app.py`
5. Add `GROQ_API_KEY` in **Advanced Settings → Secrets**
6. Click **Deploy**

### Hugging Face Spaces

1. Create a new Space (Streamlit SDK)
2. Push this repo to the Space
3. Add `GROQ_API_KEY` in **Settings → Variables and Secrets**

---

## 📊 Dataset

The `amr_data.csv` contains **300 synthetic isolate records** designed to mirror
real Pakistani AMR literature (JPMA 2023, WHO GLASS Pakistan 2023).

| Column | Description |
|---|---|
| `city` | Karachi · Lahore · Islamabad · Peshawar · Quetta |
| `organism` | 8 clinically significant pathogens |
| `antibiotic` | 12 commonly used antibiotics in Pakistan |
| `result` | Resistant / Susceptible / Intermediate |
| `date` | Sample collection date (2023) |

**Organisms covered:**
*E. coli · Klebsiella pneumoniae · Staphylococcus aureus · Pseudomonas aeruginosa ·
Salmonella spp. · Streptococcus pneumoniae · MRSA · Acinetobacter spp.*

> ⚠️ This dataset is synthetic and for demonstration purposes only.
> Resistance rates are calibrated to reflect published Pakistani AMR data
> but should not be used for clinical decision-making without real hospital data.

---

## 🎯 Impact

If deployed with real hospital data, AMR Guardian could:

- Alert clinicians when a first-line antibiotic is failing in their city
- Reduce inappropriate antibiotic prescribing in low-resource settings
- Replace expensive commercial AMR surveillance platforms
- Generate weekly bulletins automatically — saving hours of manual reporting
- Support Pakistan's national AMR action plan (WHO GLASS participation)

---

## 👥 Team

Built for the **HEC GenAI Hackathon 2025**

| Role | Responsibility |
|---|---|
| ML / GenAI Lead | Groq API integration · parser · bulletin generator |
| **Biology Specialist** | Dataset · CLSI validation · clinical accuracy · demo script |
| Frontend Developer | Streamlit UI · charts · heatmaps |
| Data Engineer | Pandas pipeline · upload system |
| PM / Presenter | Research brief · pitch deck · coordination |

---

## ⚠️ Disclaimer

AMR Guardian is a **clinical decision support tool only**.
It is not a substitute for professional medical advice, diagnosis, or treatment.
Always consult a qualified infectious disease specialist or clinical microbiologist
for antibiotic prescribing decisions.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <b>Built with 🧬 for Pakistan · WHO GLASS 2023 · Groq llama-3.3-70b</b>
</div>
