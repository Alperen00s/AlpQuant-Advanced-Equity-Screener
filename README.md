# AlpQuant | Advanced Equity Screener

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)

AlpQuant is a professional-grade quantitative financial terminal tailored for the Borsa Istanbul (BIST) market. It empowers investors and financial analysts to screen equities using a sophisticated blend of fundamental metrics and technical indicators, generating automated PDF research reports for streamlined decision-making.

## 🚀 Live Demo
**Access the web application here:** [AlpQuant Terminal](https://your-app-link.streamlit.app) *(Replace with your actual Streamlit Cloud link)*

## ✨ Key Features
* **Comprehensive Market Screening:** Filter the BIST 100, BIST 30, and BIST Islamic indexes using strict fundamental metrics (P/E, P/B, PEG, ROE, Dividend Yield).
* **Algorithmic Technical Analysis:** Identify market trends using MACD bullish crossovers, RSI, Bollinger Bands, and Simple Moving Averages (Golden Cross).
* **Islamic Finance Compliance:** Built-in exact filtering for the BIST Katılım 30 and Katılım All indexes, automatically excluding non-compliant equities and reflecting real-time index rebalancing.
* **Automated PDF Tear Sheets:** Generate one-click, institutional-quality equity research reports featuring clean 2-column financial profiles, algorithmic price action charts, and a glossary of terms.
* **Robust Data Architecture:** Utilizes parallel processing for rapid data scraping and isolated API requests to ensure terminal stability during data provider downtimes.

## 🛠️ Tech Stack
* **Language:** Python
* **Frontend UI:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Market Data API:** yfinance
* **Data Visualization:** Plotly
* **Report Generation:** FPDF

## 💻 Local Installation
To run AlpQuant on your local machine, follow these steps:

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/AlpQuant.git](https://github.com/yourusername/AlpQuant.git)
