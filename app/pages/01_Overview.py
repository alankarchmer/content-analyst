"""Overview page for Magic Slate."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from magicslate.portfolio_dashboard import (
    compute_portfolio_by_brand,
    compute_portfolio_by_genre,
    compute_concentration_metrics,
    compute_portfolio_summary,
)

st.set_page_config(page_title="Overview - Magic Slate", page_icon="📊", layout="wide")

st.title("📊 Portfolio Overview")
st.markdown("High-level summary of your content portfolio performance")

# Get data from session state
df_scorecards = st.session_state.df_scorecards

# Portfolio summary
st.markdown("## 📈 Portfolio Summary")

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

# Concentration Analysis
st.markdown("## 🎯 Portfolio Concentration")

concentration = compute_concentration_metrics(df_scorecards, top_n=10)

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
    
    import pandas as pd
    df_pie = pd.DataFrame(top_titles_data)
    
    fig = px.pie(
        df_pie,
        values='value',
        names='name',
        title="Top 10 Titles vs Rest of Portfolio"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ROI Distribution
st.markdown("## 💰 ROI Distribution")

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
