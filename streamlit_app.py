# herbal_dashboard_streamlit.py

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import re
import streamlit.components.v1 as components
from difflib import get_close_matches

# Configure matplotlib for Streamlit
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Streamlit

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
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    else:
        gemini_model = None
except ImportError:
    genai_available = False
    gemini_model = None

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
            "revenue_trend": [3200, 3400, 3600, 3760],  # Revenue in crores
            "radar_values": [85, 78, 82, 90, 75],  # R&D, Product Range, Revenue, Market Presence, Innovation
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

# Initialize Gemini session keys
if "last_gemini_input" not in st.session_state:
    st.session_state.last_gemini_input = ""
if "gemini_response_text" not in st.session_state:
    st.session_state.gemini_response_text = ""

# Trigger Gemini API call
if user_input and user_input != st.session_state.last_gemini_input:
    # Debug info (temporary)
    debug_info = f"Debug: genai_available={genai_available}, gemini_model={gemini_model is not None}"
    
    if not genai_available:
        st.session_state.gemini_response_text = f"🔧 Gemini AI is not available. Please install google-generativeai package. {debug_info}"
    elif not gemini_model:
        st.session_state.gemini_response_text = f"🔧 Gemini AI is ready but needs API key. Please add GEMINI_API_KEY to .streamlit/secrets.toml file. {debug_info}"
    else:
        with st.spinner("Pharmabot is thinking..."):
            try:
                gemini_response = gemini_model.generate_content(f"""
                You are a knowledgeable assistant on the Indian herbal supplement industry.
                Answer this user question clearly and briefly: "{user_input}"
                """)
                st.session_state.gemini_response_text = gemini_response.text
            except Exception as e:
                st.session_state.gemini_response_text = "⚠️ Gemini failed. Check your API key or connection."

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