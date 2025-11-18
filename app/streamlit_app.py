"""Main Streamlit application for Magic Slate - Content ROI & Windowing Playbook.

This is the entrypoint for the multi-page Streamlit application.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from magicslate import loaders
from magicslate.title_scorecard import compute_all_scorecards


# Page configuration
st.set_page_config(
    page_title="Magic Slate - Content ROI & Windowing Playbook",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .classification-tentpole {
        background-color: #ffd700;
        color: #000;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .classification-workhorse {
        background-color: #4CAF50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .classification-niche {
        background-color: #2196F3;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .classification-underperformer {
        background-color: #f44336;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache all data."""
    df_titles, df_engagement, df_quality = loaders.load_all_data()
    return df_titles, df_engagement, df_quality


@st.cache_data
def compute_scorecards_cached(_df_titles, _df_engagement, _df_quality):
    """Compute and cache scorecards."""
    return compute_all_scorecards(_df_titles, _df_engagement, _df_quality)


# Initialize session state
if "data_loaded" not in st.session_state:
    with st.spinner("Loading data..."):
        df_titles, df_engagement, df_quality = load_data()
        st.session_state.df_titles = df_titles
        st.session_state.df_engagement = df_engagement
        st.session_state.df_quality = df_quality
        st.session_state.data_loaded = True

# Compute scorecards (cached)
if "scorecards_computed" not in st.session_state:
    with st.spinner("Computing analytics..."):
        df_scorecards = compute_scorecards_cached(
            st.session_state.df_titles,
            st.session_state.df_engagement,
            st.session_state.df_quality
        )
        st.session_state.df_scorecards = df_scorecards
        st.session_state.scorecards_computed = True


# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/FFFFFF?text=Magic+Slate", use_container_width=True)
    
    st.markdown("### 🎬 Magic Slate")
    st.markdown("**Content ROI & Windowing Playbook**")
    st.markdown("---")
    
    st.markdown("### 📊 Data Summary")
    st.metric("Titles in Catalog", len(st.session_state.df_titles))
    
    total_hours = st.session_state.df_scorecards["total_hours_viewed"].sum() / 1_000_000
    st.metric("Total Hours Viewed", f"{total_hours:.1f}M")
    
    total_value = st.session_state.df_scorecards["total_value"].sum() / 1_000_000_000
    st.metric("Total Portfolio Value", f"${total_value:.2f}B")
    
    st.markdown("---")
    
    st.markdown("""
    ### 📖 Navigation
    
    Use the pages in the sidebar to explore:
    
    - **Overview**: Portfolio summary
    - **Title Explorer**: Deep dive on titles
    - **Portfolio Dashboard**: Aggregate views
    - **Windowing Lab**: Release strategies
    - **Greenlight Studio**: Forecast new titles
    - **Data & Assumptions**: Raw data access
    """)
    
    st.markdown("---")
    st.markdown("*Built with Streamlit & Python*")


# Main content
st.markdown('<div class="main-header">🎬 Magic Slate</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Content ROI & Windowing Playbook</div>', unsafe_allow_html=True)

st.markdown("""
Welcome to **Magic Slate**, your comprehensive analytics platform for streaming content 
planning and analysis.

### What is Magic Slate?

Magic Slate is an internal analytics tool designed for Content Planning & Analysis teams 
at streaming companies. It provides:

- **Title-level Performance Analytics**: Deep dive into individual title metrics including 
  engagement curves, quality scores, and financial ROI
  
- **Portfolio-level Insights**: Aggregate views by brand, genre, and platform to understand 
  your content strategy's effectiveness
  
- **Windowing Strategy Simulation**: Model different release window scenarios (theatrical, 
  PVOD, streaming, licensing) and their impact on total value
  
- **Greenlight Decision Support**: Forecast performance for new title concepts using 
  comparable titles and scenario analysis

### Getting Started

Use the **navigation menu** on the left to explore different sections of the platform.

**Recommended flow for new users:**
1. Start with **Overview** to understand the portfolio
2. Explore **Title Explorer** to see individual title analytics
3. Use **Portfolio Dashboard** for strategic insights
4. Experiment with **Windowing Lab** for release strategies
5. Try **Greenlight Studio** to forecast new titles

### Key Features

- **Real-time Analytics**: All calculations are performed on-demand with real data
- **Interactive Visualizations**: Charts and graphs respond to your filters and selections
- **Downloadable Reports**: Export Excel workbooks with comprehensive analytics
- **Scenario Planning**: Test different strategies and assumptions

---

**Ready to get started?** Select a page from the sidebar to begin your analysis.
""")

# Quick stats
st.markdown("### 📊 Quick Portfolio Stats")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_cost = st.session_state.df_scorecards["total_cost"].sum() / 1_000_000_000
    st.metric("Total Investment", f"${total_cost:.2f}B")

with col2:
    total_value = st.session_state.df_scorecards["total_value"].sum() / 1_000_000_000
    st.metric("Total Value", f"${total_value:.2f}B")

with col3:
    overall_roi = (st.session_state.df_scorecards["total_value"].sum() - 
                   st.session_state.df_scorecards["total_cost"].sum()) / \
                   st.session_state.df_scorecards["total_cost"].sum()
    st.metric("Portfolio ROI", f"{overall_roi*100:.1f}%")

with col4:
    avg_quality = (st.session_state.df_scorecards["critic_score"].mean() + 
                   st.session_state.df_scorecards["audience_score"].mean()) / 2
    st.metric("Avg Quality Score", f"{avg_quality:.1f}/100")

st.markdown("---")

# Classification distribution
st.markdown("### 🏆 Title Classification Distribution")

classification_counts = st.session_state.df_scorecards["classification"].value_counts()

col1, col2 = st.columns([2, 1])

with col1:
    import plotly.graph_objects as go
    
    fig = go.Figure(data=[
        go.Bar(
            x=classification_counts.index,
            y=classification_counts.values,
            marker_color=['#ffd700', '#4CAF50', '#2196F3', '#9E9E9E', '#f44336'][:len(classification_counts)]
        )
    ])
    
    fig.update_layout(
        title="Titles by Classification",
        xaxis_title="Classification",
        yaxis_title="Number of Titles",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Classification Guide")
    st.markdown("""
    - **Tentpole**: High-budget, high-value franchise content
    - **Workhorse**: Solid performers with good ROI
    - **Niche Gem**: Low-cost, high-efficiency content
    - **Acceptable**: Positive returns
    - **Marginal**: Limited returns
    - **Underperformer**: Negative ROI
    """)
