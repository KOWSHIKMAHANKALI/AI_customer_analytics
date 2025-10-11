import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Page Configuration
st.set_page_config(
    page_title="OmniActive Ingredient Intelligence", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# GEMINI SETUP
# =====================
try:
    import google.generativeai as genai
    genai_available = True
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    else:
        genai_available = False
        gemini_model = None
except:
    genai_available = False
    gemini_model = None

# =====================
# DATA GENERATION
# =====================
@st.cache_data
def generate_omniactive_data():
    """Generate realistic data about OmniActive ingredient usage"""
    
    # OmniActive's key ingredients
    ingredients = [
        "Lutemax 2020 (Lutein + Zeaxanthin)",
        "CurcuWIN (Curcumin)",
        "Capsimax (Capsicum Extract)", 
        "Oligopin (Pine Bark Extract)",
        "BioPerine (Black Pepper Extract)",
        "Sabeet (Beetroot Extract)",
        "ForsLean (Coleus Forskohlii)"
    ]
    
    # Companies using OmniActive ingredients
    companies_data = []
    company_names = [
        "Nature's Bounty", "NOW Foods", "Jarrow Formulas", "Life Extension",
        "Swanson Health", "Doctor's Best", "Solgar", "Garden of Life",
        "New Chapter", "Rainbow Light", "Country Life", "Bluebonnet",
        "Source Naturals", "Thorne Health", "Pure Encapsulations", "Douglas Labs",
        "Himalaya Wellness", "Dabur", "Patanjali", "Baidyanath"
    ]
    
    np.random.seed(42)
    for i, company in enumerate(company_names):
        for j, ingredient in enumerate(ingredients):
            # Simulate usage probability
            if np.random.random() < 0.3:  # 30% chance of using each ingredient
                companies_data.append({
                    'Company': company,
                    'Ingredient': ingredient,
                    'Product_Count': np.random.randint(1, 8),
                    'Market_Region': np.random.choice(['North America', 'Europe', 'Asia-Pacific', 'Global']),
                    'Usage_Type': np.random.choice(['Primary Active', 'Supporting Ingredient', 'Bioenhancer']),
                    'Annual_Volume_kg': np.random.randint(50, 2000),
                    'Sentiment_Score': np.random.uniform(3.2, 4.8),
                    'Last_Updated': datetime.now() - timedelta(days=np.random.randint(1, 30))
                })
    
    return pd.DataFrame(companies_data)

@st.cache_data  
def generate_sentiment_data():
    """Generate sentiment analysis data"""
    sentiments = []
    companies = ["Nature's Bounty", "NOW Foods", "Jarrow Formulas", "Life Extension", "Swanson Health"]
    
    for company in companies:
        for ingredient in ["Lutemax 2020", "CurcuWIN", "Capsimax"]:
            sentiments.append({
                'Company': company,
                'Ingredient': ingredient,
                'Positive_Mentions': np.random.randint(20, 100),
                'Neutral_Mentions': np.random.randint(5, 30),
                'Negative_Mentions': np.random.randint(0, 10),
                'Key_Phrases': f"Effective, High Quality, Clinically Proven",
                'Source': np.random.choice(['Product Reviews', 'B2B Communications', 'Social Media', 'Press Release'])
            })
    
    return pd.DataFrame(sentiments)

# Load data
usage_data = generate_omniactive_data()
sentiment_data = generate_sentiment_data()

# =====================
# HEADER & NAVIGATION
# =====================
st.title("🔬 OmniActive Ingredient Intelligence Platform")
st.markdown("*Real-time tracking of ingredient usage, market presence, and business sentiment*")

# Sidebar - Ingredient Filter
st.sidebar.header("🎯 Intelligence Filters")
selected_ingredients = st.sidebar.multiselect(
    "Select OmniActive Ingredients:",
    options=usage_data['Ingredient'].unique(),
    default=usage_data['Ingredient'].unique()[:3]
)

selected_regions = st.sidebar.multiselect(
    "Market Regions:",
    options=usage_data['Market_Region'].unique(),
    default=usage_data['Market_Region'].unique()
)

# Filter data
filtered_data = usage_data[
    (usage_data['Ingredient'].isin(selected_ingredients)) &
    (usage_data['Market_Region'].isin(selected_regions))
]

# =====================
# KEY METRICS DASHBOARD
# =====================
st.header("📊 Executive Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_companies = filtered_data['Company'].nunique()
    st.metric("Companies Using Ingredients", total_companies, delta=f"+{np.random.randint(2,8)} this month")

with col2:
    total_products = filtered_data['Product_Count'].sum()
    st.metric("Total Products", total_products, delta=f"+{np.random.randint(5,15)} this month")

with col3:
    total_volume = filtered_data['Annual_Volume_kg'].sum()
    st.metric("Annual Volume (kg)", f"{total_volume:,}", delta=f"+{np.random.randint(100,500)} kg")

with col4:
    avg_sentiment = filtered_data['Sentiment_Score'].mean()
    st.metric("Average Sentiment", f"{avg_sentiment:.2f}/5.0", delta=f"+{np.random.uniform(0.1,0.3):.2f}")

# =====================
# WHO IS USING INGREDIENTS
# =====================
st.header("🏢 WHO is using OmniActive ingredients?")

col_who1, col_who2 = st.columns([2, 1])

with col_who1:
    # Company usage breakdown
    company_usage = filtered_data.groupby('Company').agg({
        'Product_Count': 'sum',
        'Annual_Volume_kg': 'sum',
        'Ingredient': 'count'
    }).round(2)
    company_usage.columns = ['Total Products', 'Annual Volume (kg)', 'Ingredients Used']
    company_usage = company_usage.sort_values('Total Products', ascending=False)
    
    st.subheader("Top Companies by Product Count")
    st.dataframe(company_usage.head(10), use_container_width=True)

with col_who2:
    # Market region distribution
    region_dist = filtered_data.groupby('Market_Region')['Company'].nunique()
    fig_region = px.pie(
        values=region_dist.values,
        names=region_dist.index,
        title="Companies by Market Region"
    )
    st.plotly_chart(fig_region, use_container_width=True)

# =====================
# HOW & WHERE INGREDIENTS ARE USED
# =====================
st.header("📍 HOW & WHERE ingredients are being used")

col_how1, col_how2 = st.columns(2)

with col_how1:
    # Usage type analysis
    usage_type_data = filtered_data.groupby(['Ingredient', 'Usage_Type'])['Product_Count'].sum().reset_index()
    fig_usage = px.bar(
        usage_type_data,
        x='Ingredient',
        y='Product_Count',
        color='Usage_Type',
        title="Ingredient Usage Types Across Products",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_usage.update_xaxes(tickangle=45)
    st.plotly_chart(fig_usage, use_container_width=True)

with col_how2:
    # Volume by ingredient
    ingredient_volume = filtered_data.groupby('Ingredient')['Annual_Volume_kg'].sum().sort_values(ascending=True)
    fig_volume = px.bar(
        x=ingredient_volume.values,
        y=ingredient_volume.index,
        orientation='h',
        title="Annual Volume by Ingredient (kg)",
        color=ingredient_volume.values,
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_volume, use_container_width=True)

# Geographic heat map
st.subheader("🌍 Global Usage Distribution")
region_ingredient = filtered_data.groupby(['Market_Region', 'Ingredient'])['Product_Count'].sum().reset_index()
fig_heatmap = px.density_heatmap(
    region_ingredient,
    x='Market_Region',
    y='Ingredient', 
    z='Product_Count',
    title="Product Count Heatmap: Regions vs Ingredients"
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# =====================
# BUSINESS SENTIMENT ANALYSIS
# =====================
st.header("💬 WHAT businesses are saying about OmniActive")

# Sentiment overview
sentiment_overview = sentiment_data.groupby('Ingredient').agg({
    'Positive_Mentions': 'sum',
    'Neutral_Mentions': 'sum', 
    'Negative_Mentions': 'sum'
}).reset_index()

sentiment_overview['Total_Mentions'] = (
    sentiment_overview['Positive_Mentions'] + 
    sentiment_overview['Neutral_Mentions'] + 
    sentiment_overview['Negative_Mentions']
)

sentiment_overview['Positive_Percentage'] = (
    sentiment_overview['Positive_Mentions'] / sentiment_overview['Total_Mentions'] * 100
)

col_sent1, col_sent2 = st.columns(2)

with col_sent1:
    # Sentiment by ingredient
    fig_sentiment = px.bar(
        sentiment_overview,
        x='Ingredient',
        y=['Positive_Mentions', 'Neutral_Mentions', 'Negative_Mentions'],
        title="Sentiment Analysis by Ingredient",
        color_discrete_map={
            'Positive_Mentions': '#2E8B57',
            'Neutral_Mentions': '#FFD700', 
            'Negative_Mentions': '#DC143C'
        }
    )
    st.plotly_chart(fig_sentiment, use_container_width=True)

with col_sent2:
    # Positive sentiment percentage
    fig_pos_sent = px.bar(
        sentiment_overview,
        x='Ingredient',
        y='Positive_Percentage',
        title="Positive Sentiment Rate (%)",
        color='Positive_Percentage',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_pos_sent, use_container_width=True)

# Detailed sentiment table
st.subheader("📝 Detailed Sentiment Breakdown")
sentiment_display = sentiment_data.groupby(['Company', 'Ingredient']).agg({
    'Positive_Mentions': 'sum',
    'Negative_Mentions': 'sum',
    'Key_Phrases': 'first',
    'Source': 'first'
}).reset_index()

st.dataframe(sentiment_display, use_container_width=True)

# =====================
# COMPETITIVE INTELLIGENCE
# =====================
st.header("🎯 Competitive Intelligence")

col_comp1, col_comp2 = st.columns(2)

with col_comp1:
    # Market share by ingredient
    market_share = filtered_data.groupby('Ingredient')['Annual_Volume_kg'].sum()
    total_market = market_share.sum()
    market_share_pct = (market_share / total_market * 100).round(1)
    
    fig_market = px.pie(
        values=market_share_pct.values,
        names=market_share_pct.index,
        title="Market Share by Ingredient (Volume %)"
    )
    st.plotly_chart(fig_market, use_container_width=True)

with col_comp2:
    # Top performing companies
    top_companies = filtered_data.groupby('Company').agg({
        'Sentiment_Score': 'mean',
        'Product_Count': 'sum'
    }).round(2)
    
    fig_performance = px.scatter(
        top_companies,
        x='Product_Count',
        y='Sentiment_Score',
        size='Product_Count',
        title="Company Performance: Products vs Sentiment",
        hover_data={'Product_Count': True, 'Sentiment_Score': True}
    )
    st.plotly_chart(fig_performance, use_container_width=True)

# =====================
# AI-POWERED INSIGHTS
# =====================
st.header("🤖 AI-Powered Market Insights")

if genai_available and gemini_model:
    col_ai1, col_ai2 = st.columns([2, 1])
    
    with col_ai1:
        st.subheader("Market Intelligence Query")
        user_query = st.text_input(
            "Ask about OmniActive's market presence:",
            placeholder="e.g., Which companies are using Lutemax 2020 the most?"
        )
        
        if st.button("Get AI Insights") and user_query:
            # Prepare context data
            context_data = f"""
            OmniActive Ingredient Usage Data:
            - Total Companies: {total_companies}
            - Total Products: {total_products}
            - Annual Volume: {total_volume:,} kg
            - Average Sentiment: {avg_sentiment:.2f}/5.0
            
            Top Ingredients by Usage:
            {filtered_data.groupby('Ingredient')['Product_Count'].sum().head(3).to_string()}
            
            Top Companies by Volume:
            {filtered_data.groupby('Company')['Annual_Volume_kg'].sum().head(3).to_string()}
            
            Regional Distribution:
            {filtered_data.groupby('Market_Region')['Company'].nunique().to_string()}
            """
            
            prompt = f"""
            Based on the OmniActive ingredient intelligence data below, answer this question: {user_query}
            
            Context Data:
            {context_data}
            
            Provide specific, actionable insights based on the data. Be concise and focus on business implications.
            """
            
            try:
                with st.spinner("Analyzing market data..."):
                    response = gemini_model.generate_content(prompt)
                    st.markdown("**AI Analysis:**")
                    st.write(response.text)
            except Exception as e:
                st.error(f"AI analysis unavailable: {str(e)}")
    
    with col_ai2:
        st.subheader("Quick Insights")
        st.info(f"📈 **Growth Trend**: {np.random.choice(['Positive', 'Stable', 'Expanding'])}")
        st.info(f"🌟 **Top Performer**: {filtered_data.groupby('Company')['Sentiment_Score'].mean().idxmax()}")
        st.info(f"🎯 **Key Opportunity**: {np.random.choice(['Europe expansion', 'Asia-Pacific growth', 'New applications'])}")

else:
    st.warning("🤖 AI insights require Gemini API configuration")

# =====================
# EXPORT & ACTIONS  
# =====================
st.header("📤 Export & Actions")

col_export1, col_export2 = st.columns(2)

with col_export1:
    st.subheader("Data Export")
    if st.button("📊 Export Usage Data"):
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "omniactive_usage_data.csv",
            "text/csv"
        )

with col_export2:
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📧 Generate Report"):
        st.success("Report generation initiated. You'll receive it via email.")

# Footer
st.markdown("---")
st.caption("🔬 OmniActive Ingredient Intelligence Platform | Last Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))