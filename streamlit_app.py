import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import re
import streamlit.components.v1 as components
from difflib import get_close_matches
import datetime
import warnings
# Suppress Streamlit cache coroutine warnings (non-fatal)
warnings.filterwarnings("ignore", message="coroutine 'expire_cache' was never awaited")

# Reduce noisy gRPC/Google library logs
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GRPC_TRACE", "")

import matplotlib
matplotlib.use('Agg') 

# ------------------------------
# Page Config (Must be first!)
# ------------------------------
st.set_page_config(page_title="Indian Herbal Industry Dashboard", layout="wide")

# =====================
# GEMINI SETUP
# =====================
try:
    import google.generativeai as genai
    genai_available = True
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        if api_key == "YOUR_ACTUAL_API_KEY_HERE":
            genai_available = False
            gemini_model = None
            st.sidebar.warning("🔑 Please update your Gemini API key in .streamlit/secrets.toml")
        else:
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            st.sidebar.success(f"✅ Gemini configured (Key: ...{api_key[-4:]})")
    else:
        genai_available = False
        gemini_model = None
        st.sidebar.warning("⚠️ GEMINI_API_KEY not found in secrets.toml")
except ImportError as ie:
    genai_available = False
    gemini_model = None
    st.sidebar.error(f"❌ Import error: {str(ie)}")
except Exception as e:
    genai_available = False
    gemini_model = None
    st.sidebar.error(f"❌ Gemini setup error: {str(e)}")

# ------------------------------
# Load Data
# ------------------------------
@st.cache_data
def load_data():
    """Load and cache data for better performance"""
    if not os.path.exists("Top_6_Indian_Herbal_Companies_Comparison.csv"):
        st.error("Data file missing. Please upload 'Top_6_Indian_Herbal_Companies_Comparison.csv'.")
        st.stop()
    return pd.read_csv("Top_6_Indian_Herbal_Companies_Comparison.csv")

data = load_data()

# Load ingredient supplier peers (detailed) for FY2024 view
def load_peers():
    path = "ingredient_competitors_detailed.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            st.write(f"DEBUG: Loaded peers CSV with {len(df)} rows") 
            return df
        except Exception as e:
            st.error(f"Error loading peers CSV: {e}")
            return pd.DataFrame()
    else:
        st.error(f"Peers CSV not found at: {path}")
    return pd.DataFrame()

peers_df = load_peers()

# ------------------------------
# Utility Functions
# ------------------------------
@st.cache_data
def load_and_process_data():
    """Load and cache the data processing to improve performance"""
    data = pd.read_csv("Top_6_Indian_Herbal_Companies_Comparison.csv")
    return data

@st.cache_data
def get_company_chart_data(company_name):
    """Generate realistic chart data based on company profiles"""
    company_profiles = {
        "Himalaya Wellness Company": {
            "category_dist": {"Supplements": 40, "Personal Care": 35, "Baby Care": 15, "Animal Care": 10},
            "revenue_trend": [3200, 3400, 3600, 3760], 
            "radar_values": [85, 78, 82, 90, 75], 
            "growth_rate": 5.5,
            "market_share": 12.5,
            "rnd_investment": 3.2
        },
        "Dabur India Ltd.": {
            "category_dist": {"Health Supplements": 45, "Personal Care": 30, "Foods & Beverages": 20, "Home Care": 5},
            "revenue_trend": [10500, 11200, 11800, 12563],
            "radar_values": [80, 95, 98, 95, 70],
            "growth_rate": 3.6,
            "market_share": 28.5,
            "rnd_investment": 4.2
        },
        "Arjuna Natural Extracts Ltd.": {
            "category_dist": {"Botanical Extracts": 60, "Curcumin": 25, "Omega-3": 10, "Other Extracts": 5},
            "revenue_trend": [320, 345, 360, 370],
            "radar_values": [95, 45, 35, 60, 90],
            "growth_rate": 2.8,
            "market_share": 8.2,
            "rnd_investment": 6.5
        },
        "Baidyanath Group": {
            "category_dist": {"Ayurvedic Medicines": 50, "Supplements": 30, "Personal Care": 15, "Foods": 5},
            "revenue_trend": [480, 510, 525, 536],
            "radar_values": [70, 85, 55, 75, 65],
            "growth_rate": 4.2,
            "market_share": 11.8,
            "rnd_investment": 2.8
        },
        "Patanjali Ayurved": {
            "category_dist": {"Foods & Beverages": 40, "Personal Care": 35, "Health Supplements": 20, "Home Care": 5},
            "revenue_trend": [8200, 8800, 9100, 9335],
            "radar_values": [65, 90, 88, 85, 60],
            "growth_rate": 2.6,
            "market_share": 21.2,
            "rnd_investment": 1.8
        },
        "Zandu (Emami-owned)": {
            "category_dist": {"Health Supplements": 45, "Ayurvedic Medicines": 35, "Personal Care": 15, "Others": 5},
            "revenue_trend": [1100, 1180, 1220, 1262],
            "radar_values": [75, 70, 68, 70, 70],
            "growth_rate": 3.4,
            "market_share": 9.8,
            "rnd_investment": 3.1
        }
    }
    return company_profiles.get(company_name, company_profiles["Himalaya Wellness Company"])

@st.cache_data
def get_ingredient_company_data(company_name):
    """Generate realistic chart data for ingredient supplier companies"""
    ingredient_profiles = {
        "OmniActive Health Technologies": {
            "category_dist": {"Carotenoids": 45, "Curcumin": 25, "Plant Extracts": 20, "Custom Blends": 10},
            "revenue_trend": [580, 650, 700, 750], 
            "radar_values": [95, 85, 75, 88, 92],  
            "growth_rate": 14.3,
            "market_share": 8.5,
            "rnd_investment": 8.2,
            "patents": 15,
            "global_presence": 25
        },
        "Sabinsa Corporation": {
            "category_dist": {"Curcumin": 35, "Ashwagandha": 25, "Probiotics": 20, "Other Extracts": 20},
            "revenue_trend": [480, 550, 590, 620],
            "radar_values": [90, 95, 70, 85, 88],
            "growth_rate": 11.2,
            "market_share": 7.2,
            "rnd_investment": 7.5,
            "patents": 80,
            "global_presence": 30
        },
        "Indena S.p.A.": {
            "category_dist": {"Standardized Extracts": 50, "APIs": 30, "CDMO Services": 15, "Research": 5},
            "revenue_trend": [600, 650, 700, 750], 
            "radar_values": [98, 88, 72, 90, 95],
            "growth_rate": 9.5,
            "market_share": 12.5,
            "rnd_investment": 12.0,
            "patents": 100,
            "global_presence": 45
        },
        "Synthite Industries Ltd.": {
            "category_dist": {"Spice Extracts": 40, "Natural Colors": 25, "Flavors": 20, "Nutraceuticals": 15},
            "revenue_trend": [650, 720, 780, 850],
            "radar_values": [85, 92, 82, 75, 88],
            "growth_rate": 16.8,
            "market_share": 9.8,
            "rnd_investment": 6.5,
            "patents": 25,
            "global_presence": 35
        },
        "PLT Health Solutions": {
            "category_dist": {"Branded Botanicals": 60, "Custom Formulations": 25, "Consulting": 10, "R&D": 5},
            "revenue_trend": [280, 320, 360, 375], 
            "radar_values": [88, 75, 45, 70, 90],
            "growth_rate": 13.5,
            "market_share": 4.2,
            "rnd_investment": 9.8,
            "patents": 20,
            "global_presence": 15
        },
        "AIDP": {
            "category_dist": {"Ingredient Distribution": 45, "Custom Blends": 30, "Branded Ingredients": 20, "Consulting": 5},
            "revenue_trend": [420, 480, 520, 540],  
            "radar_values": [70, 85, 52, 80, 75],
            "growth_rate": 10.2,
            "market_share": 6.2,
            "rnd_investment": 4.5,
            "patents": 15,
            "global_presence": 20
        },
        "Layn Natural Ingredients": {
            "category_dist": {"Botanical Extracts": 50, "Natural Sweeteners": 25, "Flavors": 15, "Colors": 10},
            "revenue_trend": [1800, 2100, 2300, 2500], 
            "radar_values": [82, 90, 92, 85, 80],
            "growth_rate": 8.7,
            "market_share": 15.2,
            "rnd_investment": 5.8,
            "patents": 45,
            "global_presence": 40
        },
        "Euromed S.A.": {
            "category_dist": {"Botanical Extracts": 70, "Standardized Compounds": 20, "Research Services": 7, "Consulting": 3},
            "revenue_trend": [320, 360, 400, 425], 
            "radar_values": [92, 80, 48, 75, 85],
            "growth_rate": 6.2,
            "market_share": 5.8,
            "rnd_investment": 11.5,
            "patents": 35,
            "global_presence": 25
        },
        "Givaudan (Nutrition & Health)": {
            "category_dist": {"Nutritional Ingredients": 40, "Flavors": 35, "Health Actives": 20, "Custom Solutions": 5},
            "revenue_trend": [4800, 5200, 5600, 6150], 
            "radar_values": [95, 98, 98, 95, 90],
            "growth_rate": 9.8,
            "market_share": 25.8,
            "rnd_investment": 8.5,
            "patents": 200,
            "global_presence": 60
        },
        "Kappa Bioscience": {
            "category_dist": {"Vitamin K2": 60, "Carotenoids": 25, "Custom Actives": 10, "Research": 5},
            "revenue_trend": [580, 650, 720, 790], 
            "radar_values": [90, 70, 75, 65, 95],
            "growth_rate": 9.7,
            "market_share": 3.2,
            "rnd_investment": 12.8,
            "patents": 25,
            "global_presence": 20
        },
        "Arjuna Natural Extracts Ltd.": {
            "category_dist": {"BCM-95 Curcumin": 40, "Amla Extracts": 25, "Omega-3": 20, "Other Extracts": 15},
            "revenue_trend": [320, 345, 380, 410],
            "radar_values": [95, 45, 35, 60, 90],
            "growth_rate": 8.0,
            "market_share": 4.8,
            "rnd_investment": 6.5,
            "patents": 8,
            "global_presence": 25
        }
    }
    return ingredient_profiles.get(company_name, ingredient_profiles["OmniActive Health Technologies"])

def load_logo(company):
    try:
        return f"images/{company.lower().replace(' ', '_')}.png"
    except:
        return None

# Utility function to parse revenue (handles INR, crore, cr, USD, etc.)
def parse_revenue(val):
    if pd.isna(val): return 0
    val = str(val).replace(",", "").replace(" ", "")
    # Handle INR crore
    if "₹" in val and ("cr" in val or "Cr" in val):
        num = re.search(r"[\d.]+", val)
        return float(num.group()) if num else 0
    # Handle USD (rough conversion)
    if "$" in val:
        num = re.search(r"[\d.]+", val)
        usd = float(num.group()) if num else 0
        return usd * 83 / 10**7  # Convert to crore INR (approx)
    # Handle just numbers
    num = re.search(r"[\d.]+", val)
    return float(num.group()) if num else 0

def parse_products(val):
    if pd.isna(val): return 0
    m = re.search(r"(\d+)", str(val))
    return int(m.group(1)) if m else 0

def parse_growth(val):
    if pd.isna(val): return 0
    m = re.search(r"([+-]?\d+\.?\d*)%", str(val))
    return float(m.group(1)) if m else 0
# ------------------------------
# Sidebar – Updated Version
# ------------------------------
st.sidebar.title("🌿 Herbal Dashboard Assistant")

# Ensure default company is set
company_names = data["Company Name"].unique().tolist()
if "company" not in st.session_state:
    st.session_state.company = company_names[0]

# Add ingredient supplier selector and navigation
if not peers_df.empty:
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🏭 Ingredient Supplier Analysis")
    
    # Get list of ingredient suppliers for selection
    ingredient_companies = peers_df['Company Name'].tolist()
    
    if "ingredient_company" not in st.session_state:
        st.session_state.ingredient_company = ingredient_companies[0]
    
    selected_ingredient_company = st.sidebar.selectbox(
        "🔬 Select Ingredient Supplier",
        options=ingredient_companies,
        index=ingredient_companies.index(st.session_state.ingredient_company) if st.session_state.ingredient_company in ingredient_companies else 0,
        help="Choose an ingredient supplier for detailed analysis"
    )
    st.session_state.ingredient_company = selected_ingredient_company
    
    # Toggle for detailed ingredient analysis
    show_ingredient_analysis = st.sidebar.checkbox("📊 Show Detailed Ingredient Analysis", value=False)

# Company Selector
selected_company = st.sidebar.selectbox(
    "🔍 Select a Herbal Company",
    options=company_names,
    index=company_names.index(st.session_state.company),
    help="Choose a company to view its dashboard"
)
st.session_state.company = selected_company

st.sidebar.markdown("---")

# Gemini Chat Section
st.sidebar.markdown("#### 🤖 Ask Pharmabot")

user_input = st.sidebar.text_input(
    "Ask about the Indian herbal industry:",
    key="gemini_input",
    placeholder="e.g. What is the market share of Himalaya?"
)

# Toggle: restrict model to dataset-only responses
dataset_only = st.sidebar.checkbox(
    "🔒 Use dashboard data only", 
    value=False, 
    help="If checked, Pharmabot will only answer using data from the dashboard CSVs and will reply 'I don't know...' when data is insufficient."
)

# Initialize Gemini session keys
if "last_gemini_input" not in st.session_state:
    st.session_state.last_gemini_input = ""
if "gemini_response_text" not in st.session_state:
    st.session_state.gemini_response_text = ""

def build_context_for_question(user_input: str, data_df: pd.DataFrame, peers_df: pd.DataFrame, max_peers: int = 3) -> str:
    """Build a short context snippet from the main CSV and peers CSV relevant to the user_input."""
    ctx = []
    try:
        # include currently selected company row first
        if "company" in st.session_state and st.session_state.company:
            row = data_df[data_df["Company Name"] == st.session_state.company]
            if not row.empty:
                r = row.iloc[0]
                ctx.append(f"Company: {r['Company Name']}; Revenue: {r.get('Annual Revenue','N/A')}; TopProducts: {r.get('Top 3 Products','')}; Growth: {r.get('Growth Trend','N/A')}")
        
        # fuzzy match other companies mentioned in the query
        company_matches = get_close_matches(user_input.lower(), data_df["Company Name"].str.lower().tolist(), n=2, cutoff=0.4)
        for m in company_matches:
            row = data_df[data_df["Company Name"].str.lower() == m].iloc[0]
            ctx.append(f"Company: {row['Company Name']}; Revenue: {row.get('Annual Revenue','N/A')}; TopProducts: {row.get('Top 3 Products','')}; Growth: {row.get('Growth Trend','N/A')}")
        
        # include up to max_peers from peers_df that match query keywords
        if not peers_df.empty:
            peer_matches = get_close_matches(user_input.lower(), peers_df["Company Name"].str.lower().tolist(), n=max_peers, cutoff=0.3)
            for pm in peer_matches:
                prow = peers_df[peers_df["Company Name"].str.lower() == pm].iloc[0]
                ctx.append(f"Peer: {prow.get('Company Name','')}; Revenue: {prow.get('Annual Revenue','N/A')}; DataStatus: {prow.get('Data Status','N/A')}")
    except Exception:
        pass
    return "\n".join(ctx) if ctx else "No relevant dataset info found."

# Trigger Gemini API call
if user_input and user_input != st.session_state.last_gemini_input:
    debug_info = f"Debug: genai_available={genai_available}, gemini_model={gemini_model is not None}"
    
    if not genai_available:
        st.session_state.gemini_response_text = f"🔧 Gemini AI is not available. Please install google-generativeai package. {debug_info}"
    elif not gemini_model:
        st.session_state.gemini_response_text = f"🔧 Gemini AI is ready but needs API key. Please add GEMINI_API_KEY to .streamlit/secrets.toml file. {debug_info}"
    else:
        context_text = build_context_for_question(user_input, data, peers_df)
        
        # Construct safe prompt
        if dataset_only:
            prompt = f"""
CONTEXT (from dashboard CSVs):
{context_text}

INSTRUCTIONS:
- Use ONLY the information in CONTEXT to answer the question below.
- If the answer is not present in CONTEXT, reply exactly: "I don't know based on the provided data."
- Keep the answer concise (1-3 sentences).

QUESTION:
{user_input}
"""
        else:
            prompt = f"""
CONTEXT (from dashboard CSVs; optional):
{context_text}

INSTRUCTIONS:
- Prefer using the CONTEXT when it is relevant.
- You may supplement with general knowledge, but state clearly when you do so.
- Keep the answer concise (1-3 sentences).

QUESTION:
{user_input}
"""
        
        with st.spinner("Pharmabot is thinking..."):
            try:
                gemini_response = gemini_model.generate_content(prompt)
                resp_text = getattr(gemini_response, "text", None) or str(gemini_response)
                st.session_state.gemini_response_text = resp_text
                
                # Log query for audit
                try:
                    log_line = {
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                        "user_input": user_input,
                        "dataset_only": dataset_only,
                        "context_excerpt": (context_text[:500] + "...") if len(context_text) > 500 else context_text,
                        "response": resp_text[:1000] if len(resp_text) > 1000 else resp_text
                    }
                    with open("gemini_queries.log", "a", encoding="utf-8") as lf:
                        lf.write(str(log_line) + "\n")
                except Exception:
                    pass
                    
            except Exception as e:
                error_details = str(e)
                if "API_KEY" in error_details.upper():
                    st.session_state.gemini_response_text = f"🔑 API Key Error: {error_details}"
                elif "QUOTA" in error_details.upper() or "LIMIT" in error_details.upper():
                    st.session_state.gemini_response_text = f"📊 Quota/Rate Limit: {error_details}"
                elif "NETWORK" in error_details.upper() or "CONNECTION" in error_details.upper():
                    st.session_state.gemini_response_text = f"🌐 Connection Error: {error_details}"
                else:
                    st.session_state.gemini_response_text = f"⚠️ Gemini Error: {error_details}"

    st.session_state.last_gemini_input = user_input

# Display Gemini response
if user_input:
    st.sidebar.markdown("##### 💬 Response:")
    st.sidebar.write(st.session_state.gemini_response_text)

st.sidebar.markdown("---")
st.sidebar.caption("📊 Indian Herbal Industry Dashboard • 2025")
# ------------------------------
# Landing Section with Enhanced Metrics
# ------------------------------
st.title("🌿 Indian Herbal Supplement Industry Dashboard")
st.markdown(f"### Company Overview: *{st.session_state.company}*")

company_data = data[data["Company Name"] == st.session_state.company].iloc[0]
chart_data = get_company_chart_data(st.session_state.company)

col1, col2, col3, col4 = st.columns([1, 2, 2, 2])

with col1:
    logo_path = load_logo(st.session_state.company)
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=120)
    else:
        st.markdown("🏢")  # Fallback icon

with col2:
    st.metric("Revenue", company_data["Annual Revenue"])
    st.metric("Growth Rate", f"{chart_data['growth_rate']:.1f}%")

with col3:
    st.metric("Market Share", f"{chart_data['market_share']:.1f}%")
    st.metric("R&D Investment", f"{chart_data['rnd_investment']:.1f}%")

with col4:
    st.markdown(f"*Website:* [{company_data['Website']}]({company_data['Website']})")
    st.markdown(f"*Type:* {company_data['Type']}")
    st.markdown(f"*Top Product:* {company_data['Top 3 Products'].split(',')[0].strip()}")

# ------------------------------
# NEW: Ingredient Supplier Peers (FY2024) - Moved here for visibility
# ------------------------------
st.markdown("---")
st.subheader("🌿 Ingredient Supplier Peers (FY2024)")

if peers_df.empty:
    st.error("⚠️ Peer dataset not found (ingredient_competitors_detailed.csv)")
else:
    # st.success(f"✅ Loaded {len(peers_df)} ingredient supplier peers")
    
    # Show key metrics first
    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
    with col_metrics1:
        verified_count = len(peers_df[peers_df['Data Status'].str.contains('Verified', na=False)])
        st.metric("Verified Companies", verified_count)
    with col_metrics2:
        estimated_count = len(peers_df[peers_df['Data Status'].str.contains('Estimated', na=False)])
        st.metric("Estimated Data", estimated_count)
    with col_metrics3:
        needs_verification = len(peers_df[peers_df['Data Status'].str.contains('Needs Verification', na=False)])
        st.metric("Needs Verification", needs_verification)
    
    # Show the data table
    peer_view_cols = [
        "Company Name", "Website", "Annual Revenue", "Growth Trend", "Data Status"
    ]
    existing_cols = [c for c in peer_view_cols if c in peers_df.columns]
    st.dataframe(peers_df[existing_cols], hide_index=True, use_container_width=True)
    
    # Show the revenue chart if we have data
    def _parse_any_revenue(val: str):
        try:
            return parse_revenue(val)
        except Exception:
            return 0
    
    peers_df["_rev_num"] = peers_df.get("Annual Revenue", "").apply(_parse_any_revenue)
    if peers_df["_rev_num"].sum() > 0:
        fig_peer_rev = px.bar(
            peers_df.sort_values("_rev_num", ascending=False),
            x="Company Name", y="_rev_num",
            labels={"_rev_num": "Revenue (Cr INR approx)", "Company Name": "Company"},
            title="Peer Revenues (FY2024, parsed where available)",
            color="Company Name",
            color_discrete_sequence=px.colors.sequential.Greens
        )
        fig_peer_rev.update_layout(xaxis_tickangle=-30, showlegend=False)
        st.plotly_chart(fig_peer_rev, use_container_width=True)

# ------------------------------
# Individual Ingredient Supplier Analysis
# ------------------------------
if not peers_df.empty and 'show_ingredient_analysis' in locals() and show_ingredient_analysis:
    st.markdown("---")
    st.header(f"🏭 Detailed Analysis: {st.session_state.ingredient_company}")
    
    # Get selected company data
    selected_peer = peers_df[peers_df['Company Name'] == st.session_state.ingredient_company].iloc[0]
    ingredient_chart_data = get_ingredient_company_data(st.session_state.ingredient_company)
    
    # Company Overview Section
    col_overview1, col_overview2, col_overview3, col_overview4 = st.columns(4)
    
    with col_overview1:
        st.metric("Annual Revenue", selected_peer.get("Annual Revenue", "N/A"))
        st.metric("Growth Rate", f"{ingredient_chart_data['growth_rate']:.1f}%")
    
    with col_overview2:
        st.metric("Market Share", f"{ingredient_chart_data['market_share']:.1f}%")
        st.metric("R&D Investment", f"{ingredient_chart_data['rnd_investment']:.1f}%")
    
    with col_overview3:
        st.metric("Patents", f"{ingredient_chart_data['patents']}+")
        st.metric("Global Presence", f"{ingredient_chart_data['global_presence']} countries")
    
    with col_overview4:
        st.markdown(f"**Website:** [{selected_peer.get('Website', 'N/A')}]({selected_peer.get('Website', '#')})")
        st.markdown(f"**Type:** {selected_peer.get('Type', 'N/A')}")
        st.markdown(f"**Rating:** {selected_peer.get('Avg Online Rating', 'N/A')}")
    
    # Charts Section for Ingredient Companies
    st.subheader("📊 Performance Analytics")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Product Portfolio Distribution
        categories = list(ingredient_chart_data["category_dist"].keys())
        values = list(ingredient_chart_data["category_dist"].values())
        fig_portfolio = px.pie(
            names=categories, 
            values=values, 
            title=f"{st.session_state.ingredient_company} - Product Portfolio",
            color_discrete_sequence=px.colors.sequential.Blues
        )
        fig_portfolio.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_portfolio, use_container_width=True)
    
    with col_chart2:
        # Revenue Trend
        years = [2021, 2022, 2023, 2024]
        revenues = ingredient_chart_data["revenue_trend"]
        
        revenue_df = pd.DataFrame({
            'Year': years,
            'Revenue': revenues
        })
        
        fig_revenue = px.bar(
            revenue_df, 
            x='Year', 
            y='Revenue', 
            title=f"{st.session_state.ingredient_company} - Revenue Trend",
            color='Revenue',
            color_continuous_scale='Blues'
        )
        
        # Add value labels
        for i, (year, revenue) in enumerate(zip(years, revenues)):
            fig_revenue.add_annotation(
                x=year, y=revenue,
                text=f"₹{revenue:,.0f} Cr",
                showarrow=False,
                yshift=10,
                font=dict(size=10, color="darkblue")
            )
        
        fig_revenue.update_layout(showlegend=False, coloraxis_showscale=False)
        fig_revenue.update_traces(marker_line_width=2, marker_line_color="darkblue")
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Performance Radar Chart
    st.subheader("🎯 Performance Radar Analysis")
    
    radar_params = ['R&D Investment', 'Product Range', 'Revenue Scale', 'Market Presence', 'Innovation Score']
    radar_values = ingredient_chart_data["radar_values"]
    
    fig_radar = px.line_polar(
        r=radar_values, 
        theta=radar_params, 
        line_close=True,
        title=f"{st.session_state.ingredient_company} - Performance Metrics"
    )
    
    fig_radar.update_traces(
        fill='toself',
        line_color='#1f77b4',
        fillcolor='rgba(31, 119, 180, 0.3)',
        line_width=3,
        marker=dict(size=8, color='#1f77b4')
    )
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, 
                range=[0, 100],
                showticklabels=True,
                ticks="outside",
                tick0=0,
                dtick=20,
                gridcolor="lightgray",
                gridwidth=2
            ),
            angularaxis=dict(
                showticklabels=True,
                tickfont=dict(size=12),
                gridcolor="lightgray"
            ),
            bgcolor="white"
        ),
        showlegend=False,
        width=600,
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Market Analysis
    st.subheader("🌍 Market Analysis")
    
    col_market1, col_market2 = st.columns(2)
    
    with col_market1:
        # Regional Distribution (simulated)
        if 'Regional Sales Distribution' in selected_peer and pd.notna(selected_peer['Regional Sales Distribution']):
            regions_text = selected_peer['Regional Sales Distribution']
        else:
            # Default distribution based on company profile
            region_profiles = {
                "OmniActive Health Technologies": ["Asia 40%", "Americas 35%", "Europe 25%"],
                "Sabinsa Corporation": ["Americas 45%", "Asia 30%", "Europe 25%"],
                "Indena S.p.A.": ["Europe 50%", "Americas 30%", "Asia 20%"],
                "Synthite Industries Ltd.": ["Asia 60%", "Europe 25%", "Americas 15%"],
                "PLT Health Solutions": ["Americas 70%", "Europe 20%", "Asia 10%"],
                "AIDP": ["Americas 80%", "Europe 15%", "Asia 5%"]
            }
            regions_text = "; ".join(region_profiles.get(st.session_state.ingredient_company, ["Global distribution"]))
        
        st.markdown("**Regional Sales Distribution:**")
        st.markdown(regions_text)
        
        # Growth metrics
        st.markdown("**Key Metrics:**")
        st.markdown(f"• Annual Growth: {ingredient_chart_data['growth_rate']:.1f}%")
        st.markdown(f"• Market Share: {ingredient_chart_data['market_share']:.1f}%")
        st.markdown(f"• Global Presence: {ingredient_chart_data['global_presence']} countries")
    
    with col_market2:
        # Competitive Positioning
        st.markdown("**Competitive Positioning:**")
        
        # Create a scatter plot for competitive positioning
        competitors_data = []
        for comp_name in ingredient_companies[:6]:  # Top 6 for comparison
            comp_data = get_ingredient_company_data(comp_name)
            competitors_data.append({
                'Company': comp_name,
                'Innovation': comp_data['radar_values'][4],  # Innovation score
                'Market_Share': comp_data['market_share'],
                'Revenue_Size': max(comp_data['revenue_trend'])
            })
        
        comp_df = pd.DataFrame(competitors_data)
        
        fig_competitive = px.scatter(
            comp_df,
            x='Market_Share',
            y='Innovation',
            size='Revenue_Size',
            color='Company',
            title="Competitive Positioning Matrix",
            labels={
                'Market_Share': 'Market Share (%)',
                'Innovation': 'Innovation Score',
                'Revenue_Size': 'Revenue Size'
            },
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        # Highlight selected company
        selected_point = comp_df[comp_df['Company'] == st.session_state.ingredient_company]
        if not selected_point.empty:
            fig_competitive.add_scatter(
                x=selected_point['Market_Share'],
                y=selected_point['Innovation'],
                mode='markers',
                marker=dict(size=20, symbol='star', color='red', line=dict(width=2, color='darkred')),
                name='Selected Company',
                showlegend=True
            )
        
        fig_competitive.update_layout(height=400)
        st.plotly_chart(fig_competitive, use_container_width=True)
    
    # Product Details
    st.subheader("🧪 Product Portfolio Details")
    
    col_prod1, col_prod2 = st.columns(2)
    
    with col_prod1:
        st.markdown("**Top Products:**")
        top_products = selected_peer.get('Top 3 Products', 'Various specialized ingredients').split(';')
        for i, product in enumerate(top_products[:3], 1):
            st.markdown(f"{i}. {product.strip()}")
        
        st.markdown("**Ingredient Uniqueness:**")
        st.markdown(selected_peer.get('Ingredient Uniqueness', 'Specialized formulations'))
    
    with col_prod2:
        st.markdown("**Health Applications:**")
        health_issues = selected_peer.get('Health Issues Targeted', 'Various wellness applications').split(';')
        for issue in health_issues[:3]:
            st.markdown(f"• {issue.strip()}")
        
        st.markdown("**Form Factors:**")
        st.markdown(selected_peer.get('Form Factors', 'Various formats available'))
    
    # Financial Analysis
    st.subheader("💰 Financial Performance")
    
    col_fin1, col_fin2, col_fin3 = st.columns(3)
    
    with col_fin1:
        st.markdown("**Revenue Analysis:**")
        current_revenue = max(ingredient_chart_data['revenue_trend'])
        prev_revenue = ingredient_chart_data['revenue_trend'][-2]
        growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
        
        st.metric("Current Revenue", f"₹{current_revenue:,.0f} Cr")
        st.metric("YoY Growth", f"{growth:.1f}%", delta=f"{growth:.1f}%")
    
    with col_fin2:
        st.markdown("**Investment Metrics:**")
        st.metric("R&D Investment", f"{ingredient_chart_data['rnd_investment']:.1f}%")
        st.metric("Patents Portfolio", f"{ingredient_chart_data['patents']}+")
    
    with col_fin3:
        st.markdown("**Market Position:**")
        st.metric("Market Share", f"{ingredient_chart_data['market_share']:.1f}%")
        st.metric("Global Reach", f"{ingredient_chart_data['global_presence']} countries")

st.markdown("---")

# ------------------------------
# Charts Section
# ------------------------------
st.subheader("📊 Interactive Charts")

# Get company-specific data
chart_data = get_company_chart_data(st.session_state.company)

col4, col5 = st.columns(2)
with col4:
    # Real pie chart with company-specific distribution
    categories = list(chart_data["category_dist"].keys())
    values = list(chart_data["category_dist"].values())
    fig1 = px.pie(names=categories, values=values, title=f"{st.session_state.company} - Product Portfolio Distribution", 
                  color_discrete_sequence=px.colors.sequential.Greens)
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig1, use_container_width=True, key="pie_chart")

with col5:
    # Interactive revenue trend with company-specific data and colors
    years = [2021, 2022, 2023, 2024]
    revenues = chart_data["revenue_trend"]
    
    # Create DataFrame for proper plotly handling
    import pandas as pd
    revenue_df = pd.DataFrame({
        'Year': years,
        'Revenue': revenues
    })
    
    fig2 = px.bar(revenue_df, x='Year', y='Revenue', 
                  labels={'Year': 'Year', 'Revenue': 'Revenue (₹ Crores)'}, 
                  title=f"{st.session_state.company} - Revenue Trend", 
                  color='Revenue',
                  color_continuous_scale='Greens')
    
    # Add value labels on bars
    for i, (year, revenue) in enumerate(zip(years, revenues)):
        fig2.add_annotation(
            x=year, y=revenue,
            text=f"₹{revenue:,.0f} Cr",
            showarrow=False,
            yshift=10,
            font=dict(size=10, color="darkgreen")
        )
    
    fig2.update_layout(showlegend=False, coloraxis_showscale=False)
    fig2.update_traces(marker_line_width=2, marker_line_color="darkgreen")
    st.plotly_chart(fig2, use_container_width=True, key="bar_chart")

# Bubble chart: Real product analysis based on company data
st.markdown("#### Product Success vs Market Reach Analysis")
st.markdown("""
**Understanding the Bubble Chart:**
- **X-axis (Market Reach):** How widely the product is available across different markets (0-100%)
- **Y-axis (Success Rate):** Customer satisfaction and product performance rating (0-100%)
- **Bubble Size:** Relative sales volume compared to other products
- **Larger bubbles = Higher sales volume**
""")

products = [p.strip() for p in company_data['Top 3 Products'].split(",")]
# Company-specific success and reach data
product_metrics = {
    "Himalaya Wellness Company": {"success": [95, 85, 75], "reach": [90, 70, 60], "sales": [100, 80, 60]},
    "Dabur India Ltd.": {"success": [90, 88, 82], "reach": [95, 85, 75], "sales": [120, 100, 85]},
    "Arjuna Natural Extracts Ltd.": {"success": [98, 85, 70], "reach": [60, 50, 40], "sales": [80, 60, 40]},
    "Baidyanath Group": {"success": [85, 80, 75], "reach": [70, 65, 55], "sales": [70, 60, 50]},
    "Patanjali Ayurved": {"success": [80, 88, 85], "reach": [90, 85, 80], "sales": [110, 95, 80]},
    "Zandu (Emami-owned)": {"success": [85, 82, 78], "reach": [75, 70, 65], "sales": [75, 65, 55]}
}
metrics = product_metrics.get(st.session_state.company, product_metrics["Himalaya Wellness Company"])
success = metrics["success"][:len(products)]
reach = metrics["reach"][:len(products)]
sales_volume = metrics["sales"][:len(products)]

# Create bubble chart with custom colors for each product
custom_colors = ['#228B22', '#32CD32', '#90EE90']  # Different shades of green

# Create DataFrame for proper plotly handling
bubble_df = pd.DataFrame({
    'Product': products,
    'Market_Reach': reach,
    'Success_Rate': success,
    'Sales_Volume': sales_volume
})

fig3 = px.scatter(bubble_df, x='Market_Reach', y='Success_Rate', size='Sales_Volume', color='Product', 
                  labels={'Market_Reach': 'Market Reach (%)', 'Success_Rate': 'Success Rate (%)', 'Sales_Volume': 'Sales Volume'}, 
                  title=f"{st.session_state.company} - Product Performance Matrix", 
                  color_discrete_sequence=custom_colors,
                  hover_name='Product',
                  size_max=60)

# Add quadrant lines to help interpret the chart
fig3.add_hline(y=80, line_dash="dash", line_color="gray", opacity=0.5)
fig3.add_vline(x=70, line_dash="dash", line_color="gray", opacity=0.5)

# Add quadrant labels
fig3.add_annotation(x=85, y=90, text="High Success<br>High Reach", showarrow=False, 
                   font=dict(size=10, color="darkgreen"), bgcolor="rgba(255,255,255,0.8)")
fig3.add_annotation(x=55, y=90, text="High Success<br>Low Reach", showarrow=False, 
                   font=dict(size=10, color="orange"), bgcolor="rgba(255,255,255,0.8)")

fig3.update_layout(showlegend=True, width=None, height=500)
fig3.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))
st.plotly_chart(fig3, use_container_width=True, key="bubble_chart")

# Add interpretation
col_left, col_right = st.columns(2)
with col_left:
    st.markdown("**🎯 Ideal Products:** High Success + High Reach (Top Right)")
with col_right:
    st.markdown("**📈 Growth Opportunity:** High Success + Low Reach (Top Left)")

# Radar chart: Real comparative analysis using company data
st.markdown("#### Comparative Radar Analysis")
st.markdown("**Performance metrics comparison across key business areas (0-100 scale)**")

radar_params = ['R&D Investment', 'Product Range', 'Revenue Scale', 'Market Presence', 'Innovation Score']
radar_values = chart_data["radar_values"]

# Create radar chart with better visibility
fig4 = px.line_polar(r=radar_values, theta=radar_params, line_close=True, 
                     title=f"{st.session_state.company} - Performance Metrics")

# Update with better colors and styling
fig4.update_traces(
    fill='toself',
    line_color='#228B22',  # Dark green line
    fillcolor='rgba(34, 139, 34, 0.3)',  # Semi-transparent green fill
    line_width=3,
    marker=dict(size=8, color='#228B22')
)

fig4.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True, 
            range=[0, 100],
            showticklabels=True,
            ticks="outside",
            tick0=0,
            dtick=20,
            gridcolor="lightgray",
            gridwidth=2
        ),
        angularaxis=dict(
            showticklabels=True,
            tickfont=dict(size=12),
            gridcolor="lightgray"
        ),
        bgcolor="white"
    ),
    showlegend=False,
    width=600,
    height=500,
    font=dict(size=12)
)

st.plotly_chart(fig4, use_container_width=True, key="radar_chart_sim")

# Add explanation for radar chart
st.markdown("""
**📊 Radar Chart Explanation:**
- **Higher values** (towards outer edge) = Better performance
- **R&D Investment:** Research & Development spending as % of revenue
- **Product Range:** Diversity and breadth of product portfolio
- **Revenue Scale:** Company's revenue size compared to industry
- **Market Presence:** Geographic reach and brand recognition
- **Innovation Score:** New product launches and technological advancement
""")

# ------------------------------
# Product-Level Details
# ------------------------------
st.subheader("🔬 Product-Level Details")
products = [p.strip() for p in company_data['Top 3 Products'].split(",")]
ingredients = company_data['Ingredient Uniqueness'].split(';') if ';' in company_data['Ingredient Uniqueness'] else [company_data['Ingredient Uniqueness']]*len(products)
benefits = company_data['Health Issues Targeted'].split(';') if ';' in company_data['Health Issues Targeted'] else [company_data['Health Issues Targeted']]*len(products)
claims = company_data['Scientific Claims'].split(';') if ';' in company_data['Scientific Claims'] else [company_data['Scientific Claims']]*len(products)

for i, prod in enumerate(products):
    with st.expander(f"{prod}"):
        st.markdown(f"*Ingredients:* {ingredients[i] if i < len(ingredients) else ingredients[0]}")
        st.markdown(f"*Benefits/Issues Addressed:* {benefits[i] if i < len(benefits) else benefits[0]}")
        st.markdown(f"*Scientific Claims:* {claims[i] if i < len(claims) else claims[0]}")
        st.markdown(f"*User Reviews Summary:* Simulated positive reviews for {prod}.")

# ------------------------------
# Maps Section (To be expanded with geopandas/plotly mapbox)
# ------------------------------
# st.subheader("🗺 Geographical Presence")
# st.markdown(company_data['Geographical Presence'])
# # Simulated map (India focus)
# import plotly.graph_objects as go
# fig_map = go.Figure(go.Scattergeo(
#     locationmode = 'country names',
#     locations = ['India'],
#     text = [company_data['Company Name']],
#     marker = dict(size = 30, color = 'green', line_width=0)
# ))
# fig_map.update_geos(fitbounds="locations", visible=False)
# fig_map.update_layout(title="Geographical Presence (Simulated)", geo=dict(bgcolor='rgba(0,0,0,0)'))
# st.plotly_chart(fig_map, use_container_width=True, key="geo_map")

# # Simulated heatmap for market concentration
# st.markdown("#### Market Concentration Heatmap (Simulated)")
# fig_heat = go.Figure(data=go.Heatmap(z=[[1, 0.5], [0.7, 0.2]], x=['North', 'South'], y=['East', 'West'], colorscale='Greens'))
# st.plotly_chart(fig_heat, use_container_width=True, key="heatmap")

# ------------------------------
# Sentiment Analysis (Static for Now)
# ------------------------------
st.subheader("🗣 Customer Sentiment")
st.markdown("""
This section summarizes what customers are saying about the company and its products, based on online reviews and product focus. The visuals below are simulated for demonstration purposes.
""")
col6, col7 = st.columns(2)
with col6:
    st.markdown(f"*Average Online Rating:* {company_data['Avg Online Rating']}")
    # st.markdown(f"*Overall Sentiment:* {company_data['Sentiment Analysis']}")
    st.markdown("<span style='font-size: 0.95em; color: #555;'></span>", unsafe_allow_html=True)
    
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        # Prepare text for word cloud
        wc_text = company_data['Health Issues Targeted'] + ' ' + company_data['Top 3 Products']
        
        # Create word cloud
        wordcloud = WordCloud(
            width=400, 
            height=250, 
            background_color='white', 
            colormap='Greens',
            max_words=50,
            relative_scaling=0.5,
            min_font_size=8
        ).generate(wc_text)
        
        # Create matplotlib figure
        fig_wc, ax = plt.subplots(figsize=(5, 3))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        # Display in streamlit
        st.pyplot(fig_wc, use_container_width=True)
        plt.close(fig_wc)  # Close figure to free memory
        
        st.caption("Larger words indicate more frequent mentions in product descriptions and reviews.")
        
    except Exception as e:
        # st.info("📝 Word cloud visualization temporarily unavailable. Showing text summary instead:")
        
        # Create a simple text-based alternative
        st.markdown("**Key Health Issues & Products:**")
        health_issues = company_data['Health Issues Targeted'].split(',')
        products = company_data['Top 3 Products'].split(',')
        
        col_issues, col_products = st.columns(2)
        with col_issues:
            st.markdown("**Health Issues:**")
            for issue in health_issues:
                st.markdown(f"• {issue.strip()}")
        
        with col_products:
            st.markdown("**Top Products:**")
            for product in products:
                st.markdown(f"• {product.strip()}")

# with col7:
#     # Additional sentiment metrics
#     st.markdown("**📊 Sentiment Breakdown**")
    
#     # Create a simple sentiment visualization using plotly
#     sentiment_categories = ['Positive', 'Neutral', 'Negative']
#     sentiment_values = [70, 20, 10]  # Sample values, can be made dynamic
    
#     fig_sentiment = px.pie(
#         values=sentiment_values, 
#         names=sentiment_categories,
#         title="Customer Sentiment Distribution",
#         color_discrete_sequence=['#90EE90', '#FFE4B5', '#FFB6C1']
#     )
#     fig_sentiment.update_traces(textposition='inside', textinfo='percent+label')
#     fig_sentiment.update_layout(height=300)
#     st.plotly_chart(fig_sentiment, use_container_width=True, key="sentiment_pie")

# ------------------------------
# Sentiment Summary Table
# ------------------------------
st.subheader("📊 Sentiment Summary Table")
sentiment_df = data[["Company Name", "Avg Rating", "Sentiment Highlights"]].copy()
sentiment_df = sentiment_df.rename(columns={"Company Name": "Company"})
st.dataframe(sentiment_df, hide_index=True)

# ------------------------------
# OmniActive Comparison
# ------------------------------
st.subheader("🆚 Comparison with OmniActive")
st.markdown(company_data['Compared to OmniActive'])

# ------------------------------
# OmniActive Comparison (Detailed & Visual)
# ------------------------------
st.subheader("🆚 Detailed Comparison with OmniActive")

# Prepare comparison data
comparison_cols = [
    "Company Name", "Type", "Annual Revenue", "Growth Trend", "Product Categories", "No. of Products", "Avg Online Rating", "Patents Filed/Granted", "Regulatory Approvals", "Compared to OmniActive"
]
comparison_df = data[comparison_cols].copy()

# Add OmniActive as a reference row (simulated values)
omniactive_row = {
    "Company Name": "OmniActive Health Technologies",
    "Type": "B2B (nutraceutical ingredients)",
    "Annual Revenue": "~₹600 Cr (2024 est.)",
    "Growth Trend": "+10% YoY (simulated)",
    "Product Categories": "Lutein, Zeaxanthin, Curcumin, Plant Extracts",
    "No. of Products": "20+ ingredients",
    "Avg Online Rating": "N/A (B2B)",
    "Patents Filed/Granted": "30+ global patents",
    "Regulatory Approvals": "US FDA, FSSAI, EU Novel Food, GRAS",
    "Compared to OmniActive": "-"
}
comparison_df = pd.concat([comparison_df, pd.DataFrame([omniactive_row])], ignore_index=True)

# Show table
st.dataframe(comparison_df.set_index("Company Name"))

# Visual: Revenue Comparison (bar chart)
revenues = comparison_df["Annual Revenue"].apply(parse_revenue)
fig_rev = px.bar(
    x=comparison_df["Company Name"],
    y=revenues,
    labels={"x": "Company", "y": "Revenue (Cr INR, approx)"},
    title="Annual Revenue Comparison",
    color=comparison_df["Company Name"],
    color_discrete_sequence=px.colors.sequential.Greens
)
fig_rev.update_layout(xaxis_tickangle=-30)
st.plotly_chart(fig_rev, use_container_width=True, key="rev_bar")

# Visual: Product Count
product_counts = comparison_df["No. of Products"].apply(parse_products)
fig_prod = px.bar(
    x=comparison_df["Company Name"],
    y=product_counts,
    labels={"x": "Company", "y": "# Products (approx)"},
    title="Number of Products/Ingredients",
    color=comparison_df["Company Name"],
    color_discrete_sequence=px.colors.sequential.Greens
)
fig_prod.update_layout(xaxis_tickangle=-30)
# st.plotly_chart(fig_prod, use_container_width=True, key="prod_bar")

# Visual: Growth Trend (numeric, not categorical)
growth_vals = comparison_df["Growth Trend"].apply(parse_growth)
fig_growth = px.bar(
    x=comparison_df["Company Name"],
    y=growth_vals,
    labels={"x": "Company", "y": "Growth % (YoY)"},
    title="Growth Trend (YoY %)",
    color=comparison_df["Company Name"],
    color_discrete_sequence=px.colors.sequential.Greens
)
fig_growth.update_layout(xaxis_tickangle=-30)
# st.plotly_chart(fig_growth, use_container_width=True, key="growth_bar")

# Visual: Patents Filed/Granted (simulated)
def parse_patents(val):
    if pd.isna(val): return 0
    m = re.search(r"(\d+)", str(val))
    return int(m.group(1)) if m else 0
patent_counts = comparison_df["Patents Filed/Granted"].apply(parse_patents)
fig_pat = px.bar(
    x=comparison_df["Company Name"],
    y=patent_counts,
    labels={"x": "Company", "y": "# Patents (approx)"},
    title="Patents Filed/Granted",
    color=comparison_df["Company Name"],
    color_discrete_sequence=px.colors.sequential.Greens
)
fig_pat.update_layout(xaxis_tickangle=-30)
st.plotly_chart(fig_pat, use_container_width=True, key="pat_bar")

# Visual: Regulatory Approvals (count, simulated)
reg_counts = comparison_df["Regulatory Approvals"].apply(lambda x: len(str(x).split(",")) if pd.notna(x) else 0)
fig_reg = px.bar(
    x=comparison_df["Company Name"],
    y=reg_counts,
    labels={"x": "Company", "y": "# Regulatory Approvals (simulated)"},
    title="Regulatory Approvals (Count, Simulated)",
    color=comparison_df["Company Name"],
    color_discrete_sequence=px.colors.sequential.Greens
)
fig_reg.update_layout(xaxis_tickangle=-30)
# st.plotly_chart(fig_reg, use_container_width=True, key="reg_bar")

# Improved Radar Chart: Key Parameters (normalized)
radar_params = ["Revenue", "Product Count", "Growth", "Patents", "Reg Approvals"]
radar_data = pd.DataFrame({
    "Company": comparison_df["Company Name"],
    "Revenue": revenues / (revenues.max() or 1),
    "Product Count": product_counts / (product_counts.max() or 1),
    "Growth": (growth_vals - growth_vals.min()) / ((growth_vals.max() - growth_vals.min()) or 1),
    "Patents": patent_counts / (patent_counts.max() or 1),
    "Reg Approvals": reg_counts / (reg_counts.max() or 1)
})
radar_selected = radar_data[radar_data["Company"] == st.session_state.company]
radar_omni = radar_data[radar_data["Company"] == "OmniActive Health Technologies"]
import plotly.graph_objects as go
fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(r=radar_selected.iloc[0,1:], theta=radar_params, fill='toself', name=st.session_state.company))
fig_radar.add_trace(go.Scatterpolar(r=radar_omni.iloc[0,1:], theta=radar_params, fill='toself', name="OmniActive"))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])), showlegend=True, title="Comparative Radar Analysis (Normalized)")
st.plotly_chart(fig_radar, use_container_width=True, key="radar_chart_comp")

# Improved Geographical Presence Map
import plotly.express as px
country_map = {
    "India": "IND", "USA": "USA", "Europe": "FRA", "Asia": "CHN", "Oceania": "AUS", "Middle East": "ARE", "Russia": "RUS", "Africa": "ZAF", "SAARC": "BGD"
}
def extract_countries(text):
    found = []
    for k, v in country_map.items():
        if k.lower() in text.lower():
            found.append(v)
    return found or ["IND"]
geo_countries = extract_countries(company_data['Geographical Presence'])
fig_geo = px.choropleth(locations=geo_countries, locationmode="ISO-3", color=[1]*len(geo_countries),
                        color_continuous_scale=px.colors.sequential.Greens, title="Geographical Presence (by Country)")
st.plotly_chart(fig_geo, use_container_width=True, key="geo_choropleth")

# ------------------------------
# MARKETING INTELLIGENCE SUITE
# ------------------------------
st.markdown("---")
st.header("📊 Marketing Intelligence Suite")
st.markdown("*Advanced marketing analytics and AI-powered customer engagement tools*")

# Create tabs for different marketing modules
marketing_tab1, marketing_tab2, marketing_tab3 = st.tabs([
    "🎯 Social Media & ORM", 
    "🤖 ML-Powered Marketing", 
    "💬 AI Customer Assistant"
])

# Tab A: Online Reputation Management & Social Media Listening
with marketing_tab1:
    st.subheader("🔍 Online Reputation Management")
    st.markdown("**Integrated with Konnect Insights-style Social Media Listening**")
    
    col_orm1, col_orm2 = st.columns([2, 1])
    
    with col_orm1:
        # Simulated social media metrics for the selected company
        company_social_data = {
            "Himalaya Wellness Company": {
                "mention_volume": 15420,
                "sentiment_positive": 72,
                "sentiment_neutral": 18,
                "sentiment_negative": 10,
                "engagement_rate": 4.2,
                "top_platforms": ["Instagram", "Facebook", "Twitter", "YouTube"],
                "trending_topics": ["Natural ingredients", "Ayurveda", "Baby care", "Immunity"],
                "competitor_mentions": {"Dabur": 8500, "Patanjali": 12000, "Baidyanath": 3200}
            },
            "Dabur India Ltd.": {
                "mention_volume": 28750,
                "sentiment_positive": 68,
                "sentiment_neutral": 22,
                "sentiment_negative": 10,
                "engagement_rate": 5.8,
                "top_platforms": ["Instagram", "Facebook", "YouTube", "Twitter"],
                "trending_topics": ["Chyawanprash", "Hair care", "Real juice", "Ayurveda"],
                "competitor_mentions": {"Himalaya": 6200, "Patanjali": 14500, "Baidyanath": 2800}
            },
            "Patanjali Ayurved": {
                "mention_volume": 32100,
                "sentiment_positive": 65,
                "sentiment_neutral": 25,
                "sentiment_negative": 10,
                "engagement_rate": 6.1,
                "top_platforms": ["YouTube", "Facebook", "Instagram", "Twitter"],
                "trending_topics": ["Yoga", "Natural products", "Swadeshi", "Ramdev"],
                "competitor_mentions": {"Dabur": 9800, "Himalaya": 4500, "Baidyanath": 2200}
            }
        }
        
        # Get data for current company (default to Himalaya if not found)
        social_data = company_social_data.get(st.session_state.company, company_social_data["Himalaya Wellness Company"])
        
        # Display key metrics
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        with col_metric1:
            st.metric("Monthly Mentions", f"{social_data['mention_volume']:,}")
        with col_metric2:
            st.metric("Positive Sentiment", f"{social_data['sentiment_positive']}%", 
                     delta=f"+{social_data['sentiment_positive'] - 65}%")
        with col_metric3:
            st.metric("Engagement Rate", f"{social_data['engagement_rate']}%")
        with col_metric4:
            total_competitor_mentions = sum(social_data['competitor_mentions'].values())
            st.metric("Share of Voice", f"{social_data['mention_volume'] / (social_data['mention_volume'] + total_competitor_mentions) * 100:.1f}%")
        
        # Sentiment Analysis Chart
        sentiment_df = pd.DataFrame({
            'Sentiment': ['Positive', 'Neutral', 'Negative'],
            'Percentage': [social_data['sentiment_positive'], social_data['sentiment_neutral'], social_data['sentiment_negative']],
            'Color': ['#2E8B57', '#FFD700', '#DC143C']
        })
        
        fig_sentiment = px.pie(sentiment_df, values='Percentage', names='Sentiment', 
                              title=f"{st.session_state.company} - Sentiment Distribution",
                              color='Sentiment',
                              color_discrete_map={'Positive': '#2E8B57', 'Neutral': '#FFD700', 'Negative': '#DC143C'})
        st.plotly_chart(fig_sentiment, use_container_width=True)
        
        # Platform Performance
        platform_engagement = [4.5, 3.8, 3.2, 5.1]  # Simulated engagement rates
        platform_df = pd.DataFrame({
            'Platform': social_data['top_platforms'],
            'Engagement_Rate': platform_engagement
        })
        
        fig_platform = px.bar(platform_df, x='Platform', y='Engagement_Rate',
                             title="Platform-wise Engagement Rates",
                             color='Engagement_Rate',
                             color_continuous_scale='Greens')
        st.plotly_chart(fig_platform, use_container_width=True)
    
    with col_orm2:
        st.markdown("**🔥 Trending Topics**")
        for i, topic in enumerate(social_data['trending_topics'][:4], 1):
            st.markdown(f"{i}. **{topic}**")
        
        st.markdown("**⚔️ Competitor Mentions**")
        for comp, mentions in social_data['competitor_mentions'].items():
            st.markdown(f"• **{comp}**: {mentions:,}")
        
        # Crisis Alert Simulation
        st.markdown("**🚨 Alert System**")
        if social_data['sentiment_negative'] > 15:
            st.error("⚠️ High negative sentiment detected")
        elif social_data['sentiment_negative'] > 10:
            st.warning("⚠️ Monitor negative sentiment")
        else:
            st.success("✅ Sentiment within normal range")
    
    # Social Media Listening Integration
    st.markdown("### 📡 Social Media Listening Integration")
    st.info("**Integration with Konnect Insights or similar platforms:**")
    
    col_integration1, col_integration2 = st.columns(2)
    with col_integration1:
        st.markdown("""
        **Real-time Monitoring Features:**
        - Brand mention tracking across 50+ platforms
        - Hashtag performance analysis
        - Influencer identification and reach
        - Crisis detection with automated alerts
        - Competitor benchmarking
        """)
    
    with col_integration2:
        st.markdown("""
        **API Integration Capabilities:**
        - Social media platform APIs (Twitter, Facebook, Instagram)
        - News and blog monitoring
        - Review site tracking (Google, Amazon, etc.)
        - Custom keyword and phrase monitoring
        - Automated sentiment scoring
        """)

# Tab B: ML-Powered Marketing Analytics
with marketing_tab2:
    st.subheader("🎯 ML-Powered Marketing Analytics")
    st.markdown("**Advanced algorithms for customer insights and targeted marketing**")
    
    # Customer Segmentation
    st.markdown("### 👥 Customer Segmentation & Clustering")
    
    # Generate sample customer data for ML demo
    import numpy as np
    np.random.seed(42)
    
    # Simulate customer segments
    n_customers = 1000
    segments = ['Health Enthusiasts', 'Price Conscious', 'Premium Buyers', 'Loyal Customers', 'Occasional Users']
    
    customer_data = pd.DataFrame({
        'Customer_ID': range(1, n_customers + 1),
        'Age': np.random.normal(35, 12, n_customers).astype(int),
        'Annual_Spending': np.random.lognormal(8, 0.5, n_customers).astype(int),
        'Purchase_Frequency': np.random.poisson(8, n_customers),
        'Avg_Order_Value': np.random.lognormal(6, 0.3, n_customers).astype(int),
        'Segment': np.random.choice(segments, n_customers, p=[0.25, 0.20, 0.15, 0.25, 0.15]),
        'Churn_Risk': np.random.choice(['Low', 'Medium', 'High'], n_customers, p=[0.6, 0.3, 0.1])
    })
    
    col_seg1, col_seg2 = st.columns(2)
    
    with col_seg1:
        # Segment distribution
        segment_counts = customer_data['Segment'].value_counts()
        fig_segments = px.pie(values=segment_counts.values, names=segment_counts.index,
                             title="Customer Segment Distribution",
                             color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_segments, use_container_width=True)
    
    with col_seg2:
        # Spending by segment
        segment_spending = customer_data.groupby('Segment')['Annual_Spending'].mean().sort_values(ascending=False)
        fig_spending = px.bar(x=segment_spending.index, y=segment_spending.values,
                             title="Average Annual Spending by Segment",
                             color=segment_spending.values,
                             color_continuous_scale='Greens')
        st.plotly_chart(fig_spending, use_container_width=True)
    
    # Churn Prediction
    st.markdown("### 🔄 Churn Prediction & Retention")
    
    col_churn1, col_churn2, col_churn3 = st.columns(3)
    
    with col_churn1:
        churn_counts = customer_data['Churn_Risk'].value_counts()
        st.metric("Low Risk Customers", f"{churn_counts.get('Low', 0):,}")
        st.metric("Total Customer Base", f"{len(customer_data):,}")
    
    with col_churn2:
        st.metric("Medium Risk", f"{churn_counts.get('Medium', 0):,}")
        retention_rate = (churn_counts.get('Low', 0) + churn_counts.get('Medium', 0)) / len(customer_data) * 100
        st.metric("Retention Rate", f"{retention_rate:.1f}%")
    
    with col_churn3:
        st.metric("High Risk", f"{churn_counts.get('High', 0):,}", delta=f"-{churn_counts.get('High', 0)}")
        st.metric("Churn Rate", f"{churn_counts.get('High', 0) / len(customer_data) * 100:.1f}%")
    
    # ML Model Performance Simulation
    st.markdown("### 🤖 ML Model Performance")
    
    col_ml1, col_ml2 = st.columns(2)
    
    with col_ml1:
        ml_metrics = pd.DataFrame({
            'Model': ['Random Forest', 'XGBoost', 'Logistic Regression', 'Neural Network'],
            'Accuracy': [0.87, 0.89, 0.82, 0.85],
            'Precision': [0.85, 0.88, 0.80, 0.83],
            'Recall': [0.86, 0.87, 0.81, 0.84]
        })
        
        fig_ml = px.bar(ml_metrics, x='Model', y=['Accuracy', 'Precision', 'Recall'],
                       title="ML Model Performance Comparison",
                       barmode='group',
                       color_discrete_sequence=['#2E8B57', '#228B22', '#32CD32'])
        st.plotly_chart(fig_ml, use_container_width=True)
    
    with col_ml2:
        st.markdown("**🎯 Targeting Recommendations:**")
        
        # Simulated targeting insights
        high_value_customers = customer_data[customer_data['Annual_Spending'] > customer_data['Annual_Spending'].quantile(0.8)]
        
        st.markdown(f"• **High-Value Segment**: {len(high_value_customers)} customers ({len(high_value_customers)/len(customer_data)*100:.1f}%)")
        st.markdown(f"• **Average Spending**: ₹{high_value_customers['Annual_Spending'].mean():,.0f}")
        st.markdown(f"• **Recommended Action**: Premium product campaigns")
        
        at_risk_customers = customer_data[customer_data['Churn_Risk'] == 'High']
        st.markdown(f"• **At-Risk Customers**: {len(at_risk_customers)} customers")
        st.markdown(f"• **Recommended Action**: Retention campaigns with discounts")
    
    # Campaign Optimization
    st.markdown("### 📈 Campaign Optimization")
    
    campaign_results = pd.DataFrame({
        'Campaign': ['Email Newsletter', 'Social Media Ads', 'Influencer Collab', 'TV Advertisements', 'Print Media'],
        'Cost_Per_Acquisition': [120, 85, 200, 450, 350],
        'Conversion_Rate': [3.2, 4.8, 6.1, 2.1, 1.8],
        'ROI': [2.8, 4.2, 3.9, 1.9, 1.4]
    })
    
    fig_campaign = px.scatter(campaign_results, x='Cost_Per_Acquisition', y='Conversion_Rate',
                             size='ROI', color='Campaign',
                             title="Campaign Performance Analysis",
                             labels={'Cost_Per_Acquisition': 'Cost per Acquisition (₹)', 
                                   'Conversion_Rate': 'Conversion Rate (%)'},
                             hover_data=['ROI'])
    st.plotly_chart(fig_campaign, use_container_width=True)

# Tab C: AI Customer Assistant
with marketing_tab3:
    st.subheader("🤖 AI Customer Assistant")
    st.markdown("**Enhanced chatbot for customer support and engagement**")
    
    col_chat1, col_chat2 = st.columns([2, 1])
    
    with col_chat1:
        st.markdown("### 💬 Customer Service Chatbot")
        
        # Enhanced chatbot interface
        chat_container = st.container()
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": f"Hello! I'm the {st.session_state.company} customer service assistant. How can I help you today?"}
            ]
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Assistant:** {message['content']}")
        
        # Customer service topics
        st.markdown("**🔍 Quick Help Topics:**")
        help_topics = st.selectbox("Choose a topic:", [
            "Product Information",
            "Order Status",
            "Ingredient Questions", 
            "Dosage Instructions",
            "Side Effects",
            "Return Policy",
            "Store Locator",
            "Bulk Orders"
        ])
        
        if st.button("Get Help", key="help_button"):
            # Simulate AI responses based on topic
            responses = {
                "Product Information": f"I can help you learn about {st.session_state.company}'s products. We specialize in {company_data['Top 3 Products']}. Would you like detailed information about any specific product?",
                "Order Status": "To check your order status, please provide your order number. You can also track orders through our website or mobile app.",
                "Ingredient Questions": f"Our products use high-quality ingredients. {company_data['Ingredient Uniqueness']} All ingredients are sourced responsibly and tested for purity.",
                "Dosage Instructions": "Dosage varies by product and individual needs. Please check the product label or consult with our healthcare team for personalized advice.",
                "Side Effects": "Our products are generally well-tolerated. However, if you experience any adverse reactions, please discontinue use and consult a healthcare professional.",
                "Return Policy": "We offer a 30-day return policy for unopened products. Returns are processed within 5-7 business days of receipt.",
                "Store Locator": "You can find our products at major pharmacies and health stores. Use our store locator on the website to find the nearest retailer.",
                "Bulk Orders": "For bulk orders, please contact our B2B sales team. We offer special pricing for quantities over 100 units."
            }
            
            response = responses.get(help_topics, "I'm here to help! Please let me know what specific information you need.")
            st.session_state.chat_history.append({"role": "user", "content": f"Help with: {help_topics}"})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
        
        # Custom query input
        custom_query = st.text_input("Ask a custom question:", placeholder="e.g., What are the benefits of Ashwagandha?")
        
        if st.button("Ask", key="custom_ask") and custom_query:
            if genai_available and gemini_model:
                # Use Gemini for customer service responses
                customer_service_prompt = f"""
                You are a helpful customer service representative for {st.session_state.company}, an Indian herbal/ayurvedic company.
                
                Company Information:
                - Products: {company_data['Top 3 Products']}
                - Specialization: {company_data['Ingredient Uniqueness']}
                - Health Focus: {company_data['Health Issues Targeted']}
                
                Customer Question: {custom_query}
                
                Provide a helpful, professional response. If the question is about:
                - Products: Reference our actual product line
                - Health: Give general wellness information but recommend consulting healthcare professionals
                - Orders/Returns: Provide standard policy information
                - Ingredients: Explain benefits in simple terms
                
                Keep the response conversational, helpful, and under 3 sentences.
                """
                
                try:
                    response = gemini_model.generate_content(customer_service_prompt)
                    ai_response = response.text if hasattr(response, 'text') else str(response)
                    
                    st.session_state.chat_history.append({"role": "user", "content": custom_query})
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"AI Assistant temporarily unavailable: {str(e)}")
            else:
                # Fallback response without AI
                fallback_response = f"Thank you for your question about '{custom_query}'. Our customer service team will get back to you shortly. In the meantime, you can browse our product information or contact us directly."
                st.session_state.chat_history.append({"role": "user", "content": custom_query})
                st.session_state.chat_history.append({"role": "assistant", "content": fallback_response})
                st.rerun()
    
    with col_chat2:
        st.markdown("**📊 Chat Analytics**")
        
        # Simulated chat metrics
        chat_metrics = {
            "Daily Queries": 450,
            "Resolution Rate": 87,
            "Avg Response Time": "2.3 min",
            "Customer Satisfaction": 4.2
        }
        
        for metric, value in chat_metrics.items():
            if isinstance(value, int):
                st.metric(metric, f"{value:,}")
            elif isinstance(value, float):
                st.metric(metric, f"{value:.1f}/5.0")
            else:
                st.metric(metric, value)
        
        st.markdown("**🔥 Top Query Types**")
        query_types = ["Product Info (35%)", "Dosage (22%)", "Ingredients (18%)", "Orders (15%)", "Other (10%)"]
        for query in query_types:
            st.markdown(f"• {query}")
        
        st.markdown("**💡 Features:**")
        st.markdown("""
        - ✅ 24/7 Availability
        - ✅ Multi-language Support
        - ✅ Product Recommendations
        - ✅ Order Tracking
        - ✅ Health Information
        - ✅ Escalation to Human Agents
        """)
        
        # Integration options
        st.markdown("**🔌 Integration Options**")
        integration_options = st.multiselect("Select channels:", [
            "Website Widget",
            "WhatsApp Business", 
            "Facebook Messenger",
            "Mobile App",
            "Email Support",
            "Voice Assistant"
        ])
        
        if integration_options:
            st.success(f"Selected: {', '.join(integration_options)}")

# Marketing Summary
st.markdown("---")
st.markdown("### 🎯 Marketing Intelligence Summary")

col_summary1, col_summary2, col_summary3 = st.columns(3)

with col_summary1:
    st.markdown("**🔍 Social Media Insights**")
    st.info(f"• {social_data['mention_volume']:,} monthly mentions\n• {social_data['sentiment_positive']}% positive sentiment\n• Top platform: {social_data['top_platforms'][0]}")

with col_summary2:
    st.markdown("**🤖 ML Analytics**") 
    retention_customers = len(customer_data[customer_data['Churn_Risk'] != 'High'])
    st.info(f"• {len(customer_data):,} customers analyzed\n• {retention_customers/len(customer_data)*100:.1f}% retention rate\n• {len(segments)} distinct segments")

with col_summary3:
    st.markdown("**💬 AI Assistant**")
    st.info(f"• {chat_metrics['Daily Queries']} daily interactions\n• {chat_metrics['Resolution Rate']}% resolution rate\n• {chat_metrics['Customer Satisfaction']}/5.0 satisfaction")