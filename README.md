# 🌿 Indian Herbal Industry Analytics Dashboard

A comprehensive Streamlit application for analyzing the top 6 Indian herbal supplement companies, featuring interactive charts, AI-powered insights, and detailed company comparisons.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app/)

## 🏢 Companies Analyzed

- **Himalaya Wellness Company** (₹3,760 crore revenue)
- **Dabur India Ltd.** (₹12,563 crore revenue)  
- **Arjuna Natural Extracts** (₹370 crore revenue)
- **Baidyanath Group** (₹536 crore revenue)
- **Patanjali Ayurved** (₹9,335 crore revenue)
- **Zandu (Emami-owned)** (₹1,262 crore revenue)

## 🚀 Features

### 📊 Interactive Visualizations
- **Product Portfolio Distribution** - Real pie charts with company-specific percentages
- **Revenue Trends** - Historical financial performance (2021-2024)
- **Comparative Radar Analysis** - Multi-dimensional performance metrics
- **Product Performance Matrix** - Success vs Market Reach bubble charts
- **Geographic Presence** - Global market penetration maps

### 🤖 AI-Powered Insights
- **Pharmabot** - Gemini AI assistant for industry questions
- **Sentiment Analysis** - Customer review insights and word clouds
- **Competitive Intelligence** - OmniActive benchmarking

### 📈 Key Metrics Tracked
- Annual Revenue & Growth Rates
- Market Share & R&D Investment
- Product Categories & Distribution
- Patents & Regulatory Approvals
- Geographic Presence & Customer Ratings

## 🔧 Technical Features

- **Performance Optimized** - Cached data loading and processing
- **Responsive Design** - Fast company switching
- **Real Data Integration** - Accurate financial and market data
- **Interactive Charts** - Plotly-powered visualizations
- **AI Integration** - Google Gemini API support

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Streamlit account (for deployment)
- Google Gemini API key (optional, for AI features)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/trivickram/AI_customer_analytics.git
   cd AI_customer_analytics
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add API Key (Optional)**
   Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

## 📦 Dependencies

```
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
google-generativeai>=0.3.0
wordcloud>=1.9.0
matplotlib>=3.7.0
geopandas>=0.13.0
numpy>=1.24.0
speechrecognition>=3.10.0
```

## 📁 Project Structure

```
AI_customer_analytics/
├── streamlit_app.py                          # Main application
├── requirements.txt                          # Python dependencies
├── Top_6_Indian_Herbal_Companies_Comparison.csv  # Dataset
├── data/
│   └── gdp_data.csv                         # Additional data
├── .streamlit/
│   └── secrets.toml                         # API keys (create this)
├── images/                                  # Company logos (optional)
└── README.md                               # This file
```

## 🎯 Usage Guide

### Navigation
1. **Select Company** - Use sidebar dropdown to switch between companies
2. **View Metrics** - Overview section shows key performance indicators
3. **Explore Charts** - Interactive visualizations update automatically
4. **Ask Questions** - Use Pharmabot for industry insights
5. **Compare Companies** - Detailed competitor analysis section

### Key Sections
- **Company Overview** - Revenue, growth, market share metrics
- **Interactive Charts** - Portfolio distribution, revenue trends, performance radar
- **Product Details** - Ingredients, benefits, scientific claims
- **Sentiment Analysis** - Customer feedback and ratings
- **Geographic Presence** - Global market penetration
- **OmniActive Comparison** - Competitive benchmarking

## 🔍 Data Sources

- Company annual reports and financial statements
- Industry research and market analysis
- Customer review platforms
- Regulatory databases (FDA, FSSAI, etc.)
- Patent databases

## 🚀 Deployment

### Streamlit Cloud
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in dashboard settings
4. Deploy automatically

### Local Deployment
```bash
streamlit run streamlit_app.py --server.port 8501
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit** - Web framework
- **Plotly** - Interactive visualizations  
- **Google Gemini** - AI capabilities
- **Indian Herbal Industry** - Data and insights

## 📧 Contact

**Repository Owner:** [trivickram](https://github.com/trivickram)

For questions, suggestions, or collaboration opportunities, please open an issue or reach out via GitHub.

---

*Built with ❤️ using Streamlit, Plotly, and Google Gemini AI*
