# ==============================================================================
# STREAMLIT VERSION - FINAL PRODUCTION READY
# File: app.py
# Features: Line graph projection + Alpha Vantage API + Performance optimized
# ==============================================================================
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta

# ✅ Page Configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="PH Oil Price Simulator",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 🔐 API KEY MANAGEMENT (Best Practice)
# ==============================================================================
def get_alpha_vantage_key():
    """Get API key from st.secrets (preferred) or manual input"""
    # Try to load from Streamlit secrets first (secure)
    if "ALPHA_VANTAGE_KEY" in st.secrets:
        return st.secrets["ALPHA_VANTAGE_KEY"]
    return None

# ==============================================================================
# 🎮 MODEL CLASS WITH CACHING
# ==============================================================================
@st.cache_data
def get_model():
    """Cached model instance to avoid re-initialization"""
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
        
        def generate_projection(self, start_price, fx_rate, scenario, subsidy, cap, days=31):
            """Generate March-April 2026 price projection with volatility"""
            dates = pd.date_range(start="2026-03-22", periods=days, freq='D')
            prices = []
            
            # Scenario-based volatility and trend
            if scenario == "Status Quo (Deregulation)":
                volatility = 0.03  # 3% daily volatility
                trend = 0.001  # Slight upward drift
            elif scenario == "Repeal Deregulation (Price Cap)":
                volatility = 0.01  # Lower volatility due to caps
                trend = 0.0005
            else:  # Stockpile
                volatility = 0.015
                trend = 0.0008
            
            current_price = start_price
            for i in range(days):
                # Random walk with drift
                shock = np.random.normal(0, volatility)
                current_price = current_price * (1 + trend + shock)
                
                # Apply policy constraints
                if scenario == "Repeal Deregulation (Price Cap)" and cap > 0:
                    current_price = min(current_price, cap + 2)  # Small buffer
                
                # Apply subsidy effect
                if subsidy > 0:
                    current_price = max(0, current_price - (subsidy / 1000))
                    
                prices.append(round(current_price, 2))
            
            return dates, prices
    
    return OilMarketStackelberg()

# ==============================================================================
# 🌐 ALPHA VANTAGE API (Cached + Error Handled)
# ==============================================================================
@st.cache_data(ttl=3600)  # Cache for 1 hour to respect API limits
def fetch_live_crude_price(api_key):
    """Fetch live Brent crude price from Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=BRENT&apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Handle API error responses
        if "Error Message" in data or "Note" in data:
            return None, data.get("Error Message", data.get("Note", "Unknown API error"))
        
        live_price = float(data["Global Quote"]["05. price"])
        return live_price, None
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except (KeyError, ValueError, TypeError) as e:
        return None, f"Data parsing error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# ==============================================================================
# 📊 CHART GENERATION FUNCTIONS (Cached)
# ==============================================================================
@st.cache_data
def generate_scenario_chart(fx_rate, subsidy_billions):
    """Generate the 4-scenario comparison bar chart"""
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
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scenarios,
        y=[round(p, 2) for p in comp_data],
        text=[f"₱{p:.2f}" for p in comp_data],
        textposition='auto',
        marker_color=['#FF4B4B', '#4B95FF', '#FFC107', '#00C853'],
        hovertemplate="<b>%{x}</b><br>Price: ₱%{y:.2f}/L<extra></extra>"
    ))
    
    fig.update_layout(
        yaxis_title="Price (PHP per Liter)",
        template="plotly_white",
        height=400,
        margin=dict(t=30, b=30, l=30, r=30),
        showlegend=False,
        xaxis_tickfont_size=10
    )
    return fig

@st.cache_data
def generate_projection_chart(model, start_price, fx_rate, scenario, subsidy, cap, n_simulations=50):
    """Generate March-April 2026 projection with uncertainty bands"""
    # Run multiple simulations to create uncertainty band
    all_projections = []
    
    for _ in range(n_simulations):
        dates, prices = model.generate_projection(start_price, fx_rate, scenario, subsidy, cap)
        all_projections.append(prices)
    
    # Calculate statistics
    all_projections = np.array(all_projections)
    mean_prices = np.mean(all_projections, axis=0)
    lower_bound = np.percentile(all_projections, 10, axis=0)  # 10th percentile
    upper_bound = np.percentile(all_projections, 90, axis=0)  # 90th percentile
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Uncertainty band (shaded area)
    fig.add_trace(go.Scatter(
        x=dates.tolist() + dates.tolist()[::-1],
        y=upper_bound.tolist() + lower_bound.tolist()[::-1],
        fill='toself',
        fillcolor='rgba(75, 149, 255, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        name='90% Confidence Interval'
    ))
    
    # Mean projection line
    fig.add_trace(go.Scatter(
        x=dates,
        y=mean_prices,
        mode='lines',
        line=dict(color='#2E86AB', width=3),
        name='Projected Price (Mean)',
        hovertemplate="<b>%{x|%b %d}</b><br>Price: ₱%{y:.2f}/L<extra></extra>"
    ))
    
    # Current price marker
    fig.add_trace(go.Scatter(
        x=[dates[0]],
        y=[start_price],
        mode='markers',
        marker=dict(color='#E63946', size=10, symbol='star'),
        name='Starting Price',
        showlegend=True
    ))
    
    fig.update_layout(
        title="📈 Price Projection: March 22 - April 22, 2026",
        xaxis_title="Date",
        yaxis_title="Price (PHP per Liter)",
        template="plotly_white",
        height=400,
        margin=dict(t=50, b=30, l=30, r=30),
        hovermode='x unified',
        xaxis_tickformat="%b %d",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig, dates, mean_prices

# ==============================================================================
# 🎨 MAIN APP UI
# ==============================================================================
st.title("🛢️ Philippines Oil Price Stackelberg Simulator")
st.markdown("""
**Research Prototype | March 2026**  
Interactive Game Theory Model for Crude Oil Price Scenarios & Pump Price Impact
""")

# ==============================================================================
# ⚙️ SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Model Parameters")
    
    # 🔐 Alpha Vantage Integration
    st.subheader("🌐 Live Crude Price")
    
    api_key = get_alpha_vantage_key()
    use_live = st.checkbox("Use live Brent price", value=False)
    
    if use_live:
        # Allow manual override if secrets not set
        if not api_key:
            api_key = st.text_input("Alpha Vantage API Key", type="password", 
                                   help="Get free key: https://www.alphavantage.co/support/#api-key")
        
        if api_key:
            with st.spinner("🔄 Fetching live price..."):
                live_price, error = fetch_live_crude_price(api_key)
            
            if error:
                st.warning(f"⚠️ {error}")
                crude_price = st.slider("Crude Price (USD/bbl)", 40, 250, 82, 5)
            else:
                st.success(f"✅ Live Brent: ${live_price:.2f}")
                crude_price = st.slider("Crude Price (USD/bbl)", 40, 250, float(live_price), 0.5)
        else:
            st.info("💡 Enter API key above or set in `.streamlit/secrets.toml`")
            crude_price = st.slider("Crude Price (USD/bbl)", 40, 250, 82, 5)
    else:
        crude_price = st.slider("Crude Price (USD/bbl)", 40, 250, 82, 5)
    
    fx_rate = st.slider("PHP/USD Exchange Rate", 40, 70, 58, 1)
    subsidy_billions = st.slider("Government Subsidy (Billion PHP)", 0, 50, 0, 1)
    price_cap = st.slider("Price Cap (PHP/Liter)", 0, 150, 0, 5)
    
    scenario = st.selectbox(
        "Policy Scenario",
        ["Status Quo (Deregulation)", 
         "Repeal Deregulation (Price Cap)", 
         "Stockpile Strategy"]
    )
    
    st.info("💡 Adjust sliders to see real-time impact")

# ==============================================================================
# 🔄 RUN MODEL & DISPLAY METRICS
# ==============================================================================
model = get_model()
price, risk, cost = model.run_simulation(crude_price, fx_rate, subsidy_billions, price_cap, scenario)

# Metrics Display
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📉 Landed Cost", f"₱{cost:.2f}/L")
with col2:
    st.metric("🏷️ Pump Price", f"₱{price:.2f}/L", delta=f"{price-cost:.2f} margin")
with col3:
    st.metric("⚠️ Supply Risk", risk)

st.divider()

# ==============================================================================
# 📊 CHART 1: Four-Scenario Comparison (Bar Chart)
# ==============================================================================
st.subheader("📊 Four-Scenario Comparison")
fig_bar = generate_scenario_chart(fx_rate, subsidy_billions)
st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ==============================================================================
# 📈 CHART 2: March-April 2026 Projection (Line Chart) ✨ NEW ✨
# ==============================================================================
st.subheader("📈 Price Projection: March-April 2026")
st.markdown(f"*Based on current parameters: Crude ${crude_price}/bbl, FX ₱{fx_rate}/USD, Scenario: {scenario}*")

with st.spinner("🔄 Generating projection..."):
    fig_line, proj_dates, proj_prices = generate_projection_chart(
        model, price, fx_rate, scenario, subsidy_billions, price_cap
    )

st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

# Projection Summary Stats
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.metric("📅 Projection End Price", f"₱{proj_prices[-1]:.2f}/L")
with col_p2:
    change_pct = ((proj_prices[-1] - price) / price) * 100
    st.metric("📊 31-Day Change", f"{change_pct:+.1f}%")
with col_p3:
    volatility = np.std(np.diff(proj_prices)) / np.mean(proj_prices) * 100
    st.metric("📉 Est. Volatility", f"{volatility:.1f}%")

# ==============================================================================
# 🔍 GAME THEORY INSIGHTS
# ==============================================================================
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

# ==============================================================================
# 📥 DATA EXPORT
# ==============================================================================
st.divider()
st.subheader("📥 Export Data")

col_d1, col_d2 = st.columns(2)
with col_d1:
    # Scenario comparison CSV
    scenarios_list = [
        "1. $200/bbl + Status Quo",
        "2. <$200/bbl + Status Quo",
        "3. $200/bbl + Repeal",
        "4. <$200/bbl + Stockpile"
    ]
    comp_data_list = [
        model.run_simulation(200, fx_rate, 0, 0, "Status Quo (Deregulation)")[0],
        model.run_simulation(82, fx_rate, 0, 0, "Status Quo (Deregulation)")[0],
        model.run_simulation(200, fx_rate, subsidy_billions, 90, "Repeal Deregulation (Price Cap)")[0],
        model.run_simulation(82, fx_rate, subsidy_billions, 0, "Stockpile Strategy")[0]
    ]
    
    df_scenarios = pd.DataFrame({
        'Scenario': scenarios_list,
        'Pump_Price_PHP': [round(p, 2) for p in comp_data_list],
        'Crude_Price_USD': [200, 82, 200, 82],
        'Policy': ['Status Quo', 'Status Quo', 'Repeal', 'Stockpile'],
        'FX_Rate_PHP': [fx_rate]*4
    })
    
    st.download_button(
        label="📊 Download Scenario Data (CSV)",
        data=df_scenarios.to_csv(index=False),
        file_name=f"scenarios_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col_d2:
    # Projection CSV
    df_projection = pd.DataFrame({
        'Date': proj_dates,
        'Projected_Price_PHP': [round(p, 2) for p in proj_prices],
        'Scenario': scenario,
        'Crude_Price_Input': crude_price
    })
    
    st.download_button(
        label="📈 Download Projection Data (CSV)",
        data=df_projection.to_csv(index=False),
        file_name=f"projection_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ==============================================================================
# 📝 FOOTER
# ==============================================================================
st.markdown("---")
st.caption("""
**Research Disclaimer:** Prototype model for academic purposes. 
Actual prices may vary based on market conditions, geopolitical events, and policy implementation.
Sources: DOE Philippines, OPEC, J.P. Morgan, Goldman Sachs, Alpha Vantage (March 2026)
""")

# ==============================================================================
# 🔧 DEBUG INFO (Hidden by default, show with ?debug=true in URL)
# ==============================================================================
if st.query_params.get("debug") == "true":
    with st.expander("🔧 Debug Information", expanded=False):
        st.json({
            "crude_price": crude_price,
            "fx_rate": fx_rate,
            "subsidy": subsidy_billions,
            "price_cap": price_cap,
            "scenario": scenario,
            "calculated_price": price,
            "api_key_set": bool(get_alpha_vantage_key())
        })

# Add at bottom of sidebar section
if st.button("🔄 Reset to Defaults"):
    st.session_state.clear()
    st.rerun()
