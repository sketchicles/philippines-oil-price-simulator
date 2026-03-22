# philippines-oil-price-simulator


---

## 📄 README.md 

```markdown
# 🛢️ Philippines Oil Price Stackelberg Simulator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://philippines-oil-price-simulator.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **Interactive Game Theory Model for Crude Oil Price Scenarios & Pump Price Impact in the Philippines**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Four Scenario Analysis](#four-scenario-analysis)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Model Parameters](#model-parameters)
- [Data Sources](#data-sources)
- [Limitations](#limitations)
- [Citation](#citation)
- [License](#license)

---

## 🔬 Overview

This research prototype applies **Stackelberg Game Theory** to analyze how crude oil prices hitting $200/barrel would affect average pump prices in the Philippines under four different policy scenarios.

### Research Question
> How would crude oil at $200/barrel affect Philippine pump prices under different government policy responses?

### Key Findings

| Scenario | Crude Price | Policy | Predicted Pump Price |
|----------|-------------|--------|---------------------|
| 1. Status Quo | $200/bbl | Deregulation | ₱120–145/L (+85–110%) |
| 2. Status Quo | $75–90/bbl | Deregulation | ₱75–85/L (+15–25%) |
| 3. Repeal Act | $200/bbl | Price Cap | ₱85–100/L (+30–50%) |
| 4. Stockpile | $75–90/bbl | Inventory Buffer | ₱70–80/L (+5–15%) |

---

## ✨ Features

- 🎮 **Interactive Sliders:** Adjust crude price, FX rate, subsidy, and price cap in real-time
- 📊 **Four-Scenario Comparison:** Bar chart comparing all policy scenarios
- 📈 **Price Projection:** March-April 2026 forecast with 90% confidence bands
- 🌐 **Live Data:** Alpha Vantage API integration for real-time Brent crude prices
- 📥 **Export Options:** Download charts as PNG and data as CSV
- 📱 **Mobile Responsive:** Works on desktop, tablet, and mobile devices
- 🔄 **Dual Platform:** Available on Streamlit Cloud and Google Colab

---

## 🎮 Game Theory Framework
