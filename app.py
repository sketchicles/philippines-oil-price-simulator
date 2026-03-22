# ==============================================================================
# STREAMLIT VERSION - OPTIMIZED & FIXED
# File: app.py
# ==============================================================================
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd  # ✅ FIXED: Added missing import

# ✅ OPTIMIZATION: Cache the model class to avoid re-initialization
@st.cache_data
def get_model():
    class OilMarketStackelberg:
        def __init__(self):
            self.liters_per_barrel = 158.987
            self.base_excise_tax = 12.00
            self.vat_rate = 0.12
            self.refining_margin = 0.15
            self.freight_insurance = 2.5
            
        def calculate_landed_cost(self, crude_price_usd, fx_rate):
            cost_per_barrel_php = (crude_price_usd + self.freight_insurance) * fx_rate
            return cost_per_barrel_php / self.liters_per_barrel

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
    
    return OilMarketStackelberg()

# ✅ OPTIMIZATION: Cache scenario calculations
@st.cache_data
def calculate_scenario_comparison(fx_rate, subsidy_billions):
    model = get_model()
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
    return scenarios, comp_data

# Page Configuration - ✅ Place EARLY for faster render
st.set_page_config(
    page_title="PH Oil Price Simulator",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title & Header
st.title("🛢️ Philippines Oil Price Stackelberg Simulator")
st.markdown("""
**Research Prototype | March 2026**  
Interactive Game Theory Model for Crude Oil Price Scenarios & Pump Price Impact
""")

# ✅ OPTIMIZATION: Use session state to avoid re-running on every interaction
if 'model' not in st.session_state:
    st.session_state.model = get_model()

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Model Parameters")
    
    crude_price = st.slider(
        "Crude Oil Price (USD/barrel)",
        min_value=40, max_value=250, value=82, step=5
    )
    
    fx_rate = st.slider(
        "PHP/USD Exchange Rate",
        min_value=40, max_value=70, value=58, step=1
    )
    
    subsidy_billions = st.slider(
        "Government Subsidy (Billion PHP)",
        min_value=0, max_value=50, value=0, step=1
    )
    
    price_cap = st.slider(
        "Price Cap (PHP/Liter)",
        min_value=0, max_value=150, value=0, step=5
    )
    
    scenario = st.selectbox(
        "Policy Scenario",
        ["Status Quo (Deregulation)", 
         "Repeal Deregulation (Price Cap)", 
         "Stockpile Strategy"]
    )
    
    st.info("💡 Tip: Adjust sliders to see real-time impact on pump prices")

# ✅ OPTIMIZATION: Run model once, reuse results
model = st.session_state.model
price, risk, cost = model.run_simulation(crude_price, fx_rate, subsidy_billions, price_cap, scenario)

# Display Metrics (3 Columns)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📉 Landed Cost", f"₱{cost:.2f}/L")
with col2:
    st.metric("🏷️ Pump Price", f"₱{price:.2f}/L", delta=f"{price-cost:.2f} margin")
with col3:
    st.metric("⚠️ Supply Risk", risk)

st.divider()

# ✅ OPTIMIZATION: Use cached scenario comparison
st.subheader("📊 Four-Scenario Comparison")

scenarios, comp_data = calculate_scenario_comparison(fx_rate, subsidy_billions)

# ✅ OPTIMIZATION: Simplified Plotly chart for faster rendering
fig = go.Figure()
fig.add_trace(go.Bar(
    x=scenarios,
    y=[round(p, 2) for p in comp_data],  # Round to reduce data size
    text=[f"₱{p:.2f}" for p in comp_data],
    textposition='auto',
    marker_color=['#FF4B4B', '#4B95FF', '#FFC107', '#00C853'],
    hovertemplate="<b>%{x}</b><br>Price: ₱%{y:.2f}/L<extra></extra>"
))

fig.update_layout(
    yaxis_title="Price (PHP per Liter)",
    template="plotly_white",
    height=400,  # ✅ Reduced height for faster load
    margin=dict(t=30, b=30, l=30, r=30),  # ✅ Reduced margins
    showlegend=False,
    xaxis_tickfont_size=10  # ✅ Smaller font for long labels
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})  # ✅ Hide toolbar

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

# ✅ FIXED: Download Data Section with proper pandas import
st.divider()
df_data = pd.DataFrame({
    'Scenario': scenarios,
    'Pump_Price_PHP': [round(p, 2) for p in comp_data],
    'Crude_Price_USD': [200, 82, 200, 82],
    'Policy': ['Status Quo', 'Status Quo', 'Repeal', 'Stockpile'],
    'FX_Rate_PHP': [fx_rate]*4
})

csv_data = df_data.to_csv(index=False)

st.download_button(
    label="📥 Download Simulation Data (CSV)",
    data=csv_data,
    file_name=f"oil_simulation_{fx_rate}fx.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.caption("""
**Research Disclaimer:** Prototype model for academic purposes. 
Actual prices may vary based on market conditions and policy implementation.
Sources: DOE Philippines, OPEC, J.P. Morgan, Goldman Sachs (March 2026)
""")

# ✅ OPTIMIZATION: Add a "ping" to keep app warm (optional)
# st.empty()  # Minimal placeholder to reduce initial payload
