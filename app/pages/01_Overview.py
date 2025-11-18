"""Overview page for Magic Slate - Enhanced with job-aligned language."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from magicslate.portfolio_dashboard import (
    compute_portfolio_by_brand,
    compute_portfolio_by_genre,
    compute_concentration_metrics,
    compute_portfolio_summary,
    compute_hhi_by_segment,
    compute_new_vs_library_split,
)

st.set_page_config(page_title="Overview - Magic Slate", page_icon="📊", layout="wide")

st.title("📊 Magic Slate: Content Planning & Analysis Platform")
st.markdown("**Advanced analytics for content strategy, portfolio optimization, and investment decisions**")

# Get data from session state
df_scorecards = st.session_state.df_scorecards
df_titles = st.session_state.df_titles

st.markdown("---")

# How this maps to the role
with st.expander("💼 How This Maps to a Content Planning & Analysis Role", expanded=True):
    st.markdown("""
    This platform demonstrates end-to-end analytical capabilities aligned with Disney+ 
    Content Planning & Analysis responsibilities:
    
    ### 🎬 Title Performance & KPIs
    **Title Explorer** provides deep-dive analytics on individual titles including:
    - Advanced engagement metrics (peak-to-week-4 decay, long-tail analysis)
    - Model-based forecasting with R² fit statistics
    - Comparable title analysis with similarity scoring
    - Financial performance decomposition and ROI modeling
    - Analyst commentary synthesizing metrics into actionable insights
    
    ### 📊 Portfolio Strategy & Optimization
    **Portfolio Dashboard** delivers strategic portfolio analytics:
    - Risk vs return landscape analysis by brand/genre
    - Portfolio concentration metrics (HHI, top title concentration)
    - Over/under-investment identification by segment
    - New releases vs library value split
    - Brand and genre performance optimization
    
    ### 💰 Windowing & Deal Valuation
    **Windowing Lab** models release strategies and deal structures:
    - Cash flow timeline modeling by period
    - Cumulative NPV optimization across scenarios
    - Cannibalization effects and trade-off analysis
    - Sensitivity analysis for key assumptions
    - Transparent methodology with formula documentation
    
    ### 💡 Greenlight & Renewal Forecasting
    **Greenlight Studio** supports investment decisions:
    - Comparable title analysis with similarity scoring
    - Bear/base/bull scenario generation
    - Performance distribution visualization
    - Budget sensitivity analysis
    - Data-driven greenlight recommendations
    
    ### 📚 Methodology & Technical Rigor
    **Methodology Notebook** documents analytical approach:
    - Data generation and modeling methodology
    - Engagement curve modeling with statistical fit
    - Financial mapping (hours → value)
    - End-to-end case study demonstrating workflow
    - Transparent assumptions and limitations
    
    ---
    
    **Technical Skills Demonstrated**:
    - Python (pandas, numpy, plotly)
    - Statistical modeling (regression, curve fitting)
    - Financial modeling (NPV, ROI, cash flow analysis)
    - Data visualization and storytelling
    - Business acumen and strategic thinking
    """)

st.markdown("---")

# Executive summary
st.markdown("## 📈 Executive Portfolio Summary")

summary = compute_portfolio_summary(df_scorecards)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Titles", summary["total_titles"])
    
with col2:
    st.metric("Total Hours Viewed", f"{summary['total_hours']/1_000_000:.1f}M")

with col3:
    st.metric("Total Investment", f"${summary['total_cost']/1_000_000_000:.2f}B")

with col4:
    st.metric("Portfolio ROI", f"{summary['overall_roi']*100:.1f}%")

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric("Total Value Generated", f"${summary['total_value']/1_000_000_000:.2f}B")

with col6:
    st.metric("Avg Cost per Hour", f"${summary['avg_cost_per_hour']:.2f}")

with col7:
    st.metric("Avg Quality Score", f"{summary['avg_quality_score']:.1f}/100")

with col8:
    net_value = summary['total_value'] - summary['total_cost']
    st.metric("Net Value Created", f"${net_value/1_000_000_000:.2f}B")

st.markdown("---")

# Portfolio health section
st.markdown("## 🎯 Portfolio Health & Concentration")

col1, col2, col3 = st.columns(3)

# Brand HHI
brand_hhi = compute_hhi_by_segment(df_scorecards, segment_by="brand")

with col1:
    st.markdown("### Brand Concentration")
    st.metric("HHI (Brand)", f"{brand_hhi['hhi']:.0f}")
    st.caption(brand_hhi['interpretation'])
    
    if brand_hhi['hhi'] < 1500:
        st.success("✅ Well-diversified")
    elif brand_hhi['hhi'] < 2500:
        st.warning("⚠️ Moderate concentration")
    else:
        st.error("🔴 High concentration")

# Genre HHI
genre_hhi = compute_hhi_by_segment(df_scorecards, segment_by="genre")

with col2:
    st.markdown("### Genre Concentration")
    st.metric("HHI (Genre)", f"{genre_hhi['hhi']:.0f}")
    st.caption(genre_hhi['interpretation'])

# Top titles
concentration = compute_concentration_metrics(df_scorecards, top_n=10)

with col3:
    st.markdown("### Top Titles Share")
    st.metric("Top 10 Value Share", f"{concentration['top_n_share']*100:.1f}%")
    st.caption(f"{concentration['top_n']} of {concentration['total_titles']} titles")

# New vs Library
new_lib_split = compute_new_vs_library_split(df_scorecards, df_titles)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### New Releases vs Library Split")
    
    fig = go.Figure(data=[
        go.Pie(
            labels=["New Releases", "Library"],
            values=[new_lib_split['new_value'], new_lib_split['library_value']],
            marker_colors=['#1f77b4', '#ff7f0e'],
            textinfo='label+percent'
        )
    ])
    
    fig.update_layout(height=300, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Split Metrics")
    
    st.metric("New Releases", f"{new_lib_split['new_share']*100:.1f}%")
    st.caption(f"{new_lib_split['new_count']} titles")
    
    st.metric("Library", f"{new_lib_split['library_share']*100:.1f}%")
    st.caption(f"{new_lib_split['library_count']} titles")

st.markdown("---")

# Value by Brand
st.markdown("## 🎨 Value by Brand")

df_brand = compute_portfolio_by_brand(df_scorecards)

col1, col2 = st.columns([2, 1])

with col1:
    fig = px.bar(
        df_brand,
        x="brand",
        y="total_value",
        title="Total Value by Brand",
        labels={"total_value": "Total Value ($)", "brand": "Brand"},
        color="roi",
        color_continuous_scale="RdYlGn",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Top 3 Brands by Value")
    for i, row in df_brand.head(3).iterrows():
        st.markdown(f"""
        **{row['brand']}**
        - Value: ${row['total_value']/1_000_000:.1f}M
        - ROI: {row['roi']*100:.0f}%
        - Titles: {row['num_titles']}
        """)

st.markdown("---")

# Value by Genre
st.markdown("## 🎭 Value by Genre")

df_genre = compute_portfolio_by_genre(df_scorecards)

fig = px.bar(
    df_genre.head(10),
    x="total_value",
    y="genre",
    orientation="h",
    title="Top 10 Genres by Value",
    labels={"total_value": "Total Value ($)", "genre": "Genre"},
    color="roi",
    color_continuous_scale="RdYlGn",
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Top titles table
st.markdown("## 🏆 Top 10 Titles by Value")

col1, col2 = st.columns([1, 2])

with col1:
    st.metric("Top 10 Share of Value", f"{concentration['top_n_share']*100:.1f}%")
    st.metric("HHI (Concentration Index)", f"{concentration['hhi']:.0f}")
    
    st.markdown("""
    **HHI Guide:**
    - < 1500: Competitive
    - 1500-2500: Moderate concentration
    - > 2500: High concentration
    """)

with col2:
    # Top 10 titles pie chart
    top_titles_data = []
    other_value = concentration['total_value'] - concentration['top_n_value']
    
    for title in concentration['top_titles']:
        top_titles_data.append({
            'name': title['title_name'][:30],  # Truncate long names
            'value': title['total_value']
        })
    
    top_titles_data.append({'name': 'All Others', 'value': other_value})
    
    df_pie = pd.DataFrame(top_titles_data)
    
    fig = px.pie(
        df_pie,
        values='value',
        names='name',
        title="Top 10 Titles vs Rest of Portfolio"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Top titles table
top_titles_df = pd.DataFrame(concentration['top_titles'])
top_titles_df['total_value'] = top_titles_df['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
top_titles_df['value_share'] = top_titles_df['value_share'].apply(lambda x: f"{x*100:.1f}%")
top_titles_df['roi'] = top_titles_df['roi'].apply(lambda x: f"{x*100:.0f}%")

st.dataframe(
    top_titles_df[['title_name', 'brand', 'total_value', 'value_share', 'roi']], 
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ROI Distribution
st.markdown("## 💰 ROI Distribution Analysis")

fig = px.histogram(
    df_scorecards,
    x="roi",
    nbins=30,
    title="Distribution of Title ROI",
    labels={"roi": "ROI", "count": "Number of Titles"},
)
fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
fig.add_vline(x=df_scorecards["roi"].median(), line_dash="dash", line_color="green", 
              annotation_text=f"Median: {df_scorecards['roi'].median()*100:.0f}%")
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# ROI quartiles
col1, col2, col3, col4 = st.columns(4)

quartiles = df_scorecards["roi"].quantile([0.25, 0.5, 0.75])

with col1:
    st.metric("Q1 (25th percentile)", f"{quartiles[0.25]*100:.0f}%")

with col2:
    st.metric("Median (50th)", f"{quartiles[0.5]*100:.0f}%")

with col3:
    st.metric("Q3 (75th percentile)", f"{quartiles[0.75]*100:.0f}%")

with col4:
    st.metric("Mean ROI", f"{df_scorecards['roi'].mean()*100:.0f}%")

st.markdown("---")

# Navigation guide
st.markdown("## 🧭 Platform Navigation Guide")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📊 Analysis Pages
    
    1. **Title Explorer (Title Performance & KPIs)**
       - Deep-dive title analytics
       - Advanced engagement metrics
       - Model fit visualization
       - Comparable titles analysis
    
    2. **Portfolio Dashboard (Portfolio Strategy)**
       - Risk/return landscape
       - Concentration analysis
       - Investment efficiency
       - Brand/genre optimization
    
    3. **Windowing Lab (Deal Valuation)**
       - Release strategy modeling
       - Cash flow timeline
       - NPV optimization
       - Sensitivity analysis
    """)

with col2:
    st.markdown("""
    ### 💡 Decision Support Pages
    
    4. **Greenlight Studio (Forecasting)**
       - New title forecasting
       - Comparable title analysis
       - Scenario generation
       - Greenlight recommendations
    
    5. **Data & Assumptions**
       - Business assumptions
       - Parameter reference
       - Data dictionary
    
    6. **Methodology & Analyst Notebook**
       - Technical documentation
       - Full case study
       - Methodology explanations
       - Example analytics
    """)

st.markdown("""
---

### 🚀 Getting Started

1. **Explore existing titles**: Use **Title Explorer** to analyze individual title performance
2. **Understand the portfolio**: Review **Portfolio Dashboard** for strategic insights
3. **Model scenarios**: Test windowing strategies in **Windowing Lab**
4. **Forecast new concepts**: Generate projections in **Greenlight Studio**
5. **Learn methodology**: Review **Methodology Notebook** for technical details

---

**Note**: All data is synthetically generated for demonstration purposes. Real applications 
would use internal streaming analytics and financial data.
""")
