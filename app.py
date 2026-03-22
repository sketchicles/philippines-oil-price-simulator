# ==============================================================================
# STREAMLIT VERSION - For Web Deployment
# Save this as: app.py
# ==============================================================================
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="PH Oil Price Simulator",
    page_icon="🛢️",
    layout="wide"
)

# Title & Header
st.title("🛢️ Philippines Oil Price Stackelberg Simulator")
st.markdown("""
**Research Prototype | March 2026**  
Interactive Game Theory Model for Crude Oil Price Scenarios & Pump Price Impact
""")

# Sidebar Controls
st.sidebar.header("⚙️ Model Parameters")

crude_price = st.sidebar.slider(
    "Crude Oil Price (USD/barrel)",
    min_value=40, max_value=250, value=82, step=5
)

fx_rate = st.sidebar.slider(
    "PHP/USD Exchange Rate",
    min_value=40, max_value=70, value=58, step=1
)

subsidy_billions = st.sidebar.slider(
    "Government Subsidy (Billion PHP)",
    min_value=0, max_value=50, value=0, step=1
)

price_cap = st.sidebar.slider(
    "Price Cap (PHP/Liter)",
    min_value=0, max_value=150, value=0, step=5
)

scenario = st.sidebar.selectbox(
    "Policy Scenario",
    ["Status Quo (Deregulation)", 
     "Repeal Deregulation (Price Cap)", 
     "Stockpile Strategy"]
)

# Model Class
class OilMarketStackelberg:
    def __init__(self):
        self.liters_per_barrel = 158.987
        self.base_excise_tax = 12.00
        self.vat_rate = 0.12
        self.refining_margin = 0.15
        self.freight_insurance = 2.5
        
    def calculate_landed_cost(self, crude_price_usd, fx_rate):
        cost_per_barrel_php = (crude_price_usd + self.freight_insurance) * fx_rate
        cost_per_liter = cost_per_barrel_php / self.liters_per_barrel
        return cost_per_liter

    def follower_response(self, cost_per_liter, scenario, subsidy_amount, price_cap):
        base_price = cost_per_liter * (1 + self.refining_margin) + self.base_excise_tax
        price_with_tax = base_price / (1 - self.vat_rate)
        
        if scenario == "Status Quo (Deregulation)":
            strategic_markup = 2.0
            final_price = price_with_tax + strategic_markup
            subsidy_effect = 0
        elif scenario == "Repeal Deregulation (Price Cap)":
            if price_cap > 0:
                final_price = min(price_with_tax, price_cap)
            else:
                final_price = price_with_tax
            subsidy_effect = subsidy_amount / 1000
        elif scenario == "Stockpile Strategy":
            strategic_markup = 0.5
            final_price = price_with_tax + strategic_markup
            subsidy_effect = 0
        else:
            final_price = price_with_tax
            subsidy_effect = 0

        return max(0, final_price - subsidy_effect)

    def run_simulation(self, crude_price, fx_rate, subsidy_billions, price_cap, scenario):
        cost = self.calculate_landed_cost(crude_price, fx_rate)
        pump_price = self.follower_response(cost, scenario, subsidy_billions, price_cap)
        
        supply_risk = "LOW"
        if scenario == "Repeal Deregulation (Price Cap)" and price_cap > 0:
            if price_cap < (cost * (1 + self.refining_margin)):
                supply_risk = "🔴 HIGH (Shortage Likely)"
            elif price_cap < pump_price:
                supply_risk = "🟡 MODERATE"
        
        return pump_price, supply_risk, cost

# Run Model
model = OilMarketStackelberg()
price, risk, cost = model.run_simulation(crude_price, fx_rate, subsidy_billions, price_cap, scenario)

# Display Metrics (3 Columns)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📉 Landed Cost", f"₱{cost:.2f}/L")
with col2:
    st.metric("🏷️ Pump Price", f"₱{price:.2f}/L")
with col3:
    st.metric("⚠️ Supply Risk", risk)

st.divider()

# Scenario Comparison Chart
st.subheader("📊 Four-Scenario Comparison")

scenarios = [
    "1. $200/bbl + Status Quo",
    "2. <$200/bbl + Status Quo",
    "3. $200/bbl + Repeal",
    "4. <$200/bbl + Stockpile"
]

comp_data = [
    model.run_simulation(200, fx_rate, 0, 0, "Status Quo (Deregulation)")[0],
    model.run_simulation(82, fx_rate, 0, 0, "Status Quo (Deregulation)")[0],
    model.run_simulation(200, fx_rate, subsidy_billions, 90, "Repeal Deregulation (Price Cap)")[0],
    model.run_simulation(82, fx_rate, subsidy_billions, 0, "Stockpile Strategy")[0]
]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=scenarios,
    y=comp_data,
    text=[f"₱{p:.2f}" for p in comp_data],
    textposition='auto',
    marker_color=['#FF4B4B', '#4B95FF', '#FFC107', '#00C853'],
))

fig.update_layout(
    yaxis_title="Price (PHP per Liter)",
    template="plotly_white",
    height=400,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Additional Analysis
st.divider()
st.subheader("🔍 Game Theory Insights")

col_a, col_b = st.columns(2)
with col_a:
    st.info("""
    **Leader (Government)**
    - Sets policy first (price caps, subsidies)
    - Commits to strategy before firms respond
    - Risk: Credibility of enforcement
    """)
with col_b:
    st.success("""
    **Followers (Oil Companies)**
    - Observe policy, then set prices
    - Maximize profit within constraints
    - Risk: Supply reduction if caps too low
    """)

# Download Data
st.divider()
csv_data = pd.DataFrame({
    'Scenario': scenarios,
    'Pump_Price_PHP': comp_data,
    'Crude_Price_USD': [200, 82, 200, 82],
    'Policy': ['Status Quo', 'Status Quo', 'Repeal', 'Stockpile']
}).to_csv(index=False)

st.download_button(
    label="📥 Download Simulation Data (CSV)",
    data=csv_data,
    file_name="oil_price_simulation.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.caption("""
**Research Disclaimer:** This is a prototype model for academic purposes. 
Actual prices may vary based on market conditions, geopolitical events, and policy implementation.
Data sources: DOE Philippines, OPEC, J.P. Morgan, Goldman Sachs (March 2026)
""")

# Add to sidebar in app.py
with st.sidebar:
    st.subheader("🌐 Live Data")
    if st.checkbox("Use live crude price (Alpha Vantage API)"):
        # Note: Requires free API key from https://www.alphavantage.co/support/#api-key
        api_key = st.text_input("Alpha Vantage API Key", type="password")
        if api_key:
            import requests
            try:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=BRENT&apikey={api_key}"
                response = requests.get(url, timeout=5)
                data = response.json()
                live_price = float(data["Global Quote"]["05. price"])
                crude_price = st.slider("Crude Oil Price (USD/barrel)", 
                                       min_value=40, max_value=250, 
                                       value=live_price, step=0.5,
                                       help=f"Live Brent: ${live_price}")
                st.success(f"✅ Live price loaded: ${live_price}")
            except:
                st.warning("⚠️ Could not fetch live data. Using manual input.")
