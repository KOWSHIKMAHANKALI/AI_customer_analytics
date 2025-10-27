import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Page Configuration
st.set_page_config(
    page_title="OmniActive Intelligence Dashboard", 
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
# DATA LOADING FUNCTIONS
# =====================
@st.cache_data
def load_company_data():
    """Load company usage data"""
    try:
        return pd.read_csv("data/omniactive_company_usage.csv")
    except FileNotFoundError:
        st.error("❌ Data not found. Please run data_collector.py first to collect real data.")
        return pd.DataFrame()

@st.cache_data
def load_mentions_data():
    """Load news mentions data"""
    try:
        return pd.read_csv("data/omniactive_mentions.csv")
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def load_market_data():
    """Load market analysis data"""
    try:
        return pd.read_csv("data/omniactive_market_data.csv")
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def load_metadata():
    """Load data metadata"""
    try:
        with open("data/metadata.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_updated": "No data available", "data_quality": "Please collect data first"}

# Load all data
company_data = load_company_data()
mentions_data = load_mentions_data()
market_data = load_market_data()
metadata = load_metadata()

# =====================
# HEADER
# =====================
st.title("🔬 OmniActive Intelligence Dashboard")
st.markdown("*Real business intelligence based on collected market data*")

# Data freshness indicator
if not company_data.empty:
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.success(f"✅ Data loaded: {metadata.get('data_quality', 'Real data')}")
    with col_header2:
        st.info(f"📅 Updated: {metadata.get('last_updated', 'Unknown')[:10]}")
    with col_header3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
else:
    st.warning("⚠️ No data available. Please run the data collector first.")
    st.code("python data_collector.py")
    st.stop()

# =====================
# SIDEBAR FILTERS
# =====================
st.sidebar.header("🎯 Intelligence Filters")

# Ingredient filter
available_ingredients = company_data['ingredient'].unique() if not company_data.empty else []
selected_ingredients = st.sidebar.multiselect(
    "Select Ingredients:",
    options=available_ingredients,
    default=available_ingredients[:4] if len(available_ingredients) > 4 else available_ingredients
)

# Region filter
available_regions = company_data['market_region'].unique() if not company_data.empty else []
selected_regions = st.sidebar.multiselect(
    "Market Regions:",
    options=available_regions,
    default=available_regions
)

# Filter data
if not company_data.empty:
    filtered_data = company_data[
        (company_data['ingredient'].isin(selected_ingredients)) &
        (company_data['market_region'].isin(selected_regions))
    ]
else:
    filtered_data = pd.DataFrame()

# =====================
# KEY METRICS
# =====================
if not filtered_data.empty:
    st.header("📊 Executive Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_companies = filtered_data['company_name'].nunique()
        st.metric("Companies Using Ingredients", total_companies)
    
    with col2:
        total_products = filtered_data['product_count'].sum()
        st.metric("Total Products", total_products)
    
    with col3:
        total_volume = filtered_data['annual_volume_kg'].sum()
        st.metric("Annual Volume (kg)", f"{total_volume:,}")
    
    with col4:
        avg_sentiment = filtered_data['sentiment_score'].mean()
        st.metric("Average Sentiment", f"{avg_sentiment:.2f}/5.0")
        
        # Add explanation based on sentiment score
        if avg_sentiment >= 4.0:
            sentiment_explanation = "😊 Customers express very positive opinions overall."
        elif avg_sentiment >= 3.0:
            sentiment_explanation = "🙂 Sentiment is moderately positive with some mixed feedback."
        elif avg_sentiment >= 2.0:
            sentiment_explanation = "😐 Average sentiment — some customers are neutral or unsatisfied."
        else:
            sentiment_explanation = "☹️ Sentiment is generally negative; improvement may be needed."

        st.caption(sentiment_explanation)

# =====================
# WHO IS USING INGREDIENTS
# =====================
if not filtered_data.empty:
    st.header("🏢 who is using OmniActive ingredients?")
    
    col_who1, col_who2 = st.columns([3, 2])
    
    with col_who1:
        st.subheader("Company Usage Overview")
        
        # Company summary table
        company_summary = filtered_data.groupby('company_name').agg({
            'product_count': 'sum',
            'annual_volume_kg': 'sum',
            'ingredient': 'count',
            'sentiment_score': 'mean'
        }).round(2)
        company_summary.columns = ['Total Products', 'Annual Volume (kg)', 'Ingredients Used', 'Avg Sentiment']
        company_summary = company_summary.sort_values('Total Products', ascending=False)
        
        st.dataframe(company_summary, use_container_width=True)
    
    with col_who2:
        st.subheader("Top Companies by Volume")
        
        # Top companies chart
        top_companies = filtered_data.groupby('company_name')['annual_volume_kg'].sum().sort_values(ascending=True).tail(8)
        fig_companies = px.bar(
            x=top_companies.values,
            y=top_companies.index,
            orientation='h',
            title="Annual Volume by Company (kg)",
            color=top_companies.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_companies, use_container_width=True)

# =====================
# HOW & WHERE INGREDIENTS ARE USED
# =====================
if not filtered_data.empty:
    st.header("📍 HOW & WHERE ingredients are being used")
    
    col_how1, col_how2 = st.columns(2)
    
    with col_how1:
        st.subheader("Usage Type Distribution")
        
        # Usage type analysis
        usage_analysis = filtered_data.groupby(['ingredient', 'usage_type'])['product_count'].sum().reset_index()
        fig_usage = px.bar(
            usage_analysis,
            x='ingredient',
            y='product_count',
            color='usage_type',
            title="Product Count by Usage Type",
            color_discrete_sequence=['#2E8B57', '#4169E1', '#FF6347']
        )
        fig_usage.update_xaxes(tickangle=45)
        st.plotly_chart(fig_usage, use_container_width=True)
    
    with col_how2:
        st.subheader("Market Region Distribution")
        
        # Regional distribution
        region_dist = filtered_data.groupby('market_region')['company_name'].nunique()
        fig_region = px.pie(
            values=region_dist.values,
            names=region_dist.index,
            title="Companies by Market Region"
        )
        st.plotly_chart(fig_region, use_container_width=True)

# =====================
# MARKET INTELLIGENCE
# =====================
if not market_data.empty:
    st.header("📈 Market Intelligence")
    
    col_market1, col_market2 = st.columns(2)
    
    with col_market1:
        st.subheader("Market Share by Ingredient")
        
        market_filtered = market_data[market_data['ingredient'].isin(selected_ingredients)]
        fig_market_share = px.pie(
            market_filtered,
            values='market_share_percent',
            names='ingredient',
            title="Market Share Distribution (%)"
        )
        st.plotly_chart(fig_market_share, use_container_width=True)
    
    with col_market2:
        st.subheader("Growth Rate Analysis")
        
        fig_growth = px.bar(
            market_filtered,
            x='ingredient',
            y='growth_rate_percent',
            title="Annual Growth Rate by Ingredient (%)",
            color='growth_rate_percent',
            color_continuous_scale='Greens'
        )
        fig_growth.update_xaxes(tickangle=45)
        st.plotly_chart(fig_growth, use_container_width=True)

# =====================
# SENTIMENT ANALYSIS
# =====================
if not mentions_data.empty:
    st.header("💬 WHAT businesses are saying")
    
    col_sent1, col_sent2 = st.columns([3, 2])
    
    with col_sent1:
        st.subheader("Recent Industry Mentions")
        
        # Filter mentions for selected ingredients
        mentions_filtered = mentions_data[mentions_data['ingredient'].isin(selected_ingredients)]
        
        # Display recent mentions
        for _, mention in mentions_filtered.iterrows():
            with st.expander(f"📰 {mention['title']} - {mention['source']}"):
                st.markdown(f"**Ingredient:** {mention['ingredient']}")
                st.markdown(f"**Date:** {mention['date']}")
                st.markdown(f"**Sentiment:** {'✅ Positive' if mention['sentiment'] == 'positive' else '⚠️ Neutral'}")
                st.markdown(f"**Summary:** {mention['snippet']}")
                st.markdown(f"[Read More]({mention['url']})")
    
    with col_sent2:
        st.subheader("Sentiment Overview")
        
        if not mentions_filtered.empty:
            # Sentiment distribution
            sentiment_counts = mentions_filtered['sentiment'].value_counts()
            colors = {'positive': '#2E8B57', 'neutral': '#FFD700', 'negative': '#DC143C'}
            fig_sentiment = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                title="Overall Sentiment Distribution",
                color=sentiment_counts.index,
                color_discrete_map=colors
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)
            
            # Sentiment by ingredient
            # Sentiment by ingredient with explanation
ingredient_sentiment = mentions_filtered.groupby('ingredient')['sentiment_score'].mean().sort_values(ascending=False)
st.subheader("Average Sentiment Score")

for ingredient, score in ingredient_sentiment.items():
    st.metric(ingredient, f"{score:.1f}/5.0")
    
    # Explanation logic
    if ingredient.lower() == "lutemax 2020":
        st.caption("🟢 Highly positive sentiment — driven by FDA and EU approvals, reinforcing trust and market leadership.")
    elif ingredient.lower() == "curcuwin":
        st.caption("🟢 Positive sentiment — strong clinical validation and awards for joint health benefits contribute to optimism.")
    elif ingredient.lower() == "capsimax":
        st.caption("🟡 Moderately positive sentiment — innovation awards increased awareness, but competition remains intense.")
    elif ingredient.lower() == "bioperine":
        st.caption("🟢 Positive sentiment — sustained market presence and formulation versatility support stable brand perception.")
    elif ingredient.lower() == "oligopin":
        st.caption("🟢 Positive sentiment — improved supply stability and quality perception boosted industry confidence.")
    elif ingredient.lower() == "sabeet":
        st.caption("🟢 Positive sentiment — endurance study results enhanced its image in sports nutrition.")
    elif ingredient.lower() == "forslean":
        st.caption("🟢 Positive sentiment — regulatory clarity and renewed metabolic health positioning improved its outlook.")
    else:
        st.caption("🙂 Neutral sentiment — limited new mentions or steady market perception.")


# =====================F
# COMPETITIVE ANALYSIS
# =====================
if not filtered_data.empty and not market_data.empty:
    st.header("🎯 Competitive Intelligence")
    
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        st.subheader("Performance Matrix")
        
        # Create performance matrix
        performance_data = []
        for ingredient in selected_ingredients:
            company_count = filtered_data[filtered_data['ingredient'] == ingredient]['company_name'].nunique()
            market_info = market_data[market_data['ingredient'] == ingredient]
            
            if not market_info.empty:
                performance_data.append({
                    'ingredient': ingredient,
                    'company_count': company_count,
                    'market_share': market_info.iloc[0]['market_share_percent'],
                    'growth_rate': market_info.iloc[0]['growth_rate_percent']
                })
        
        if performance_data:
            perf_df = pd.DataFrame(performance_data)
            fig_performance = px.scatter(
                perf_df,
                x='market_share',
                y='growth_rate',
                size='company_count',
                color='ingredient',
                title="Market Share vs Growth Rate",
                labels={'market_share': 'Market Share (%)', 'growth_rate': 'Growth Rate (%)'}
            )
            st.plotly_chart(fig_performance, use_container_width=True)
    
    with col_comp2:
        st.subheader("Key Insights")
        
        if performance_data:
            # Top performing ingredient
            top_ingredient = max(performance_data, key=lambda x: x['market_share'])
            st.success(f"🏆 **Market Leader**: {top_ingredient['ingredient']} ({top_ingredient['market_share']:.1f}% share)")
            
            # Fastest growing
            fastest_growing = max(performance_data, key=lambda x: x['growth_rate'])
            st.info(f"📈 **Fastest Growing**: {fastest_growing['ingredient']} ({fastest_growing['growth_rate']:.1f}% growth)")
            
            # Most adopted
            most_adopted = max(performance_data, key=lambda x: x['company_count'])
            st.info(f"🏢 **Most Adopted**: {most_adopted['ingredient']} ({most_adopted['company_count']} companies)")

# =====================
# AI INSIGHTS
# =====================
if genai_available and gemini_model and not filtered_data.empty:
    st.header("🤖 AI-Powered Insights")
    
    col_ai1, col_ai2 = st.columns([2, 1])
    
    with col_ai1:
        user_query = st.text_input(
            "Ask about OmniActive's market intelligence:",
            placeholder="e.g., Which ingredient has the best growth potential?"
        )
        
        if st.button("🔍 Get AI Analysis") and user_query:
            # Prepare data context
            context = f"""
            OmniActive Market Intelligence Summary:
            
            Companies Using Ingredients: {filtered_data['company_name'].nunique()}
            Total Products: {filtered_data['product_count'].sum()}
            Average Sentiment: {filtered_data['sentiment_score'].mean():.2f}/5.0
            
            Top Ingredients by Usage:
            {filtered_data.groupby('ingredient')['company_name'].nunique().sort_values(ascending=False).head().to_string()}
            
            Market Share Leaders:
            {market_data[['ingredient', 'market_share_percent']].sort_values('market_share_percent', ascending=False).head().to_string()}
            
            Growth Rate Leaders:
            {market_data[['ingredient', 'growth_rate_percent']].sort_values('growth_rate_percent', ascending=False).head().to_string()}
            """
            
            prompt = f"""
            Based on this OmniActive market intelligence data, provide insights for: {user_query}
            
            {context}
            
            Provide specific, actionable business insights. Focus on growth opportunities, competitive positioning, and strategic recommendations.
            """
            
            try:
                with st.spinner("Analyzing market intelligence..."):
                    response = gemini_model.generate_content(prompt)
                    st.markdown("**🎯 AI Analysis:**")
                    st.write(response.text)
            except Exception as e:
                st.error(f"AI analysis unavailable: {str(e)}")
    
    with col_ai2:
        st.subheader("Quick Intelligence")
        
        if not filtered_data.empty:
            # Auto-generated insights
            top_company = filtered_data.groupby('company_name')['annual_volume_kg'].sum().idxmax()
            st.info(f"🏢 **Top Volume Partner**: {top_company}")
            
            most_used_ingredient = filtered_data['ingredient'].value_counts().index[0]
            st.info(f"🔬 **Most Adopted**: {most_used_ingredient}")
            
            if not market_data.empty:
                fastest_growth = market_data.loc[market_data['growth_rate_percent'].idxmax(), 'ingredient']
                st.success(f"📈 **Growth Leader**: {fastest_growth}")

# =====================
# DATA EXPORT
# =====================
st.header("📤 Data Export & Actions")

col_export1, col_export2, col_export3 = st.columns(3)

with col_export1:
    if st.button("📊 Export Company Data") and not filtered_data.empty:
        csv_data = filtered_data.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv_data,
            f"omniactive_company_intelligence_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

with col_export2:
    if st.button("📰 Export Mentions Data") and not mentions_data.empty:
        csv_mentions = mentions_data.to_csv(index=False)
        st.download_button(
            "Download Mentions CSV",
            csv_mentions,
            f"omniactive_mentions_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

with col_export3:
    if st.button("🔄 Update Data Source"):
        st.code("python data_collector.py")

# =====================
# FOOTER
# =====================
st.markdown("---")
col_footer1, col_footer2 = st.columns(2)

with col_footer1:
    st.caption(f"🔬 OmniActive Intelligence Dashboard | Data Quality: {metadata.get('data_quality', 'Real Data')}")

with col_footer2:
    st.caption(f"📅 Last Updated: {metadata.get('last_updated', 'Unknown')}")