"""Portfolio Dashboard page for Magic Slate."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from magicslate.portfolio_dashboard import (
    compute_portfolio_by_brand,
    compute_portfolio_by_genre,
    compute_portfolio_by_platform,
    compute_portfolio_by_content_type,
    compute_concentration_metrics,
    compute_classification_distribution,
    filter_scorecards,
)

st.set_page_config(page_title="Portfolio Dashboard - Magic Slate", page_icon="📊", layout="wide")

st.title("📊 Portfolio Dashboard")
st.markdown("Comprehensive portfolio analytics and strategic insights")

# Get data from session state
df_scorecards = st.session_state.df_scorecards
df_titles = st.session_state.df_titles

# Filters sidebar
st.sidebar.markdown("## 🔍 Filters")

available_brands = sorted(df_scorecards["brand"].unique().tolist())
selected_brands = st.sidebar.multiselect(
    "Brands",
    available_brands,
    default=available_brands
)

available_genres = sorted(df_scorecards["genre"].unique().tolist())
selected_genres = st.sidebar.multiselect(
    "Genres",
    available_genres,
    default=available_genres
)

available_platforms = sorted(df_scorecards["platform_primary"].unique().tolist())
selected_platforms = st.sidebar.multiselect(
    "Platforms",
    available_platforms,
    default=available_platforms
)

available_types = sorted(df_scorecards["content_type"].unique().tolist())
selected_types = st.sidebar.multiselect(
    "Content Types",
    available_types,
    default=available_types
)

# Apply filters
filtered_scorecards = filter_scorecards(
    df_scorecards,
    brands=selected_brands if selected_brands else None,
    genres=selected_genres if selected_genres else None,
    platforms=selected_platforms if selected_platforms else None,
    content_types=selected_types if selected_types else None
)

st.sidebar.markdown(f"**Filtered: {len(filtered_scorecards)} / {len(df_scorecards)} titles**")

# Summary metrics
st.markdown("## 📈 Filtered Portfolio Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Titles", len(filtered_scorecards))

with col2:
    total_hours = filtered_scorecards["total_hours_viewed"].sum() / 1_000_000
    st.metric("Total Hours", f"{total_hours:.1f}M")

with col3:
    total_value = filtered_scorecards["total_value"].sum() / 1_000_000_000
    st.metric("Total Value", f"${total_value:.2f}B")

with col4:
    total_cost = filtered_scorecards["total_cost"].sum()
    total_val = filtered_scorecards["total_value"].sum()
    roi = (total_val - total_cost) / total_cost if total_cost > 0 else 0
    st.metric("Portfolio ROI", f"{roi*100:.1f}%")

st.markdown("---")

# View selector
view_tab1, view_tab2, view_tab3, view_tab4 = st.tabs([
    "📊 By Brand", "🎭 By Genre", "📺 By Platform", "🏆 By Classification"
])

with view_tab1:
    st.markdown("### Performance by Brand")
    
    df_brand = compute_portfolio_by_brand(filtered_scorecards)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Stacked bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Streaming Value',
            x=df_brand['brand'],
            y=df_brand['streaming_value'] / 1_000_000,
            marker_color='#1f77b4'
        ))
        
        if 'theatrical_value' in df_brand.columns:
            fig.add_trace(go.Bar(
                name='Theatrical Value',
                x=df_brand['brand'],
                y=df_brand['theatrical_value'] / 1_000_000,
                marker_color='#ff7f0e'
            ))
        
        fig.update_layout(
            barmode='stack',
            title="Total Value by Brand",
            xaxis_title="Brand",
            yaxis_title="Value ($ Millions)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ROI comparison
        fig = go.Figure(data=[
            go.Bar(
                x=df_brand['roi'] * 100,
                y=df_brand['brand'],
                orientation='h',
                marker_color=df_brand['roi'].apply(
                    lambda x: '#4CAF50' if x > 0.5 else ('#FFC107' if x > 0 else '#f44336')
                ),
                text=df_brand['roi'].apply(lambda x: f"{x*100:.0f}%"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="ROI by Brand",
            xaxis_title="ROI (%)",
            yaxis_title="Brand",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("#### Brand Performance Table")
    
    display_df = df_brand.copy()
    display_df['total_value'] = display_df['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['total_hours_viewed'] = display_df['total_hours_viewed'].apply(lambda x: f"{x/1_000_000:.1f}M")
    display_df['roi'] = display_df['roi'].apply(lambda x: f"{x*100:.1f}%")
    display_df['cost_per_hour'] = display_df['cost_per_hour'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with view_tab2:
    st.markdown("### Performance by Genre")
    
    df_genre = compute_portfolio_by_genre(filtered_scorecards)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.scatter(
            df_genre,
            x="total_hours_viewed",
            y="total_value",
            size="num_titles",
            color="roi",
            hover_name="genre",
            labels={
                "total_hours_viewed": "Total Hours Viewed",
                "total_value": "Total Value ($)",
                "roi": "ROI"
            },
            title="Genre Performance: Hours vs Value",
            color_continuous_scale="RdYlGn",
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top genres by value
        st.markdown("#### Top Genres by Value")
        for _, row in df_genre.head(5).iterrows():
            st.markdown(f"""
            **{row['genre']}**
            - Value: ${row['total_value']/1_000_000:.1f}M
            - ROI: {row['roi']*100:.0f}%
            - Titles: {row['num_titles']}
            - Avg Quality: {row['critic_score']:.1f}/100
            """)
    
    # Genre table
    st.markdown("#### Genre Performance Table")
    
    display_df = df_genre.copy()
    display_df['total_value'] = display_df['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['roi'] = display_df['roi'].apply(lambda x: f"{x*100:.1f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with view_tab3:
    st.markdown("### Performance by Platform")
    
    df_platform = compute_portfolio_by_platform(filtered_scorecards)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Value by platform
        fig = go.Figure(data=[
            go.Bar(
                x=df_platform['platform'],
                y=df_platform['total_value'] / 1_000_000,
                marker_color=['#1f77b4', '#ff7f0e'][:len(df_platform)],
                text=df_platform['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Total Value by Platform",
            xaxis_title="Platform",
            yaxis_title="Value ($ Millions)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Hours by platform
        fig = go.Figure(data=[
            go.Bar(
                x=df_platform['platform'],
                y=df_platform['total_hours_viewed'] / 1_000_000,
                marker_color=['#2ca02c', '#d62728'][:len(df_platform)],
                text=df_platform['total_hours_viewed'].apply(lambda x: f"{x/1_000_000:.1f}M"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Total Hours by Platform",
            xaxis_title="Platform",
            yaxis_title="Hours (Millions)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Platform comparison
    st.markdown("#### Platform Comparison")
    
    display_df = df_platform.copy()
    display_df['total_value'] = display_df['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['streaming_value'] = display_df['streaming_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['ad_value'] = display_df['ad_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['roi'] = display_df['roi'].apply(lambda x: f"{x*100:.1f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with view_tab4:
    st.markdown("### Performance by Classification")
    
    df_classification = compute_classification_distribution(filtered_scorecards)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Treemap
        fig = px.treemap(
            df_classification,
            path=['classification'],
            values='total_value',
            color='roi',
            color_continuous_scale='RdYlGn',
            title="Value Distribution by Classification"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Classification Summary")
        for _, row in df_classification.iterrows():
            st.markdown(f"""
            **{row['classification']}**
            - Titles: {row['num_titles']}
            - Value: ${row['total_value']/1_000_000:.1f}M
            - Avg ROI: {row['roi']*100:.0f}%
            """)
    
    # Classification table
    st.markdown("#### Classification Performance Table")
    
    display_df = df_classification.copy()
    display_df['total_value'] = display_df['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_df['roi'] = display_df['roi'].apply(lambda x: f"{x*100:.1f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")

# Concentration analysis
st.markdown("## 🎯 Portfolio Concentration Analysis")

concentration = compute_concentration_metrics(filtered_scorecards, top_n=10)

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.metric("Total Titles", concentration['total_titles'])
    st.metric("Top 10 Value Share", f"{concentration['top_n_share']*100:.1f}%")

with col2:
    st.metric("HHI Index", f"{concentration['hhi']:.0f}")
    
    hhi = concentration['hhi']
    if hhi < 1500:
        concentration_level = "✅ Competitive"
    elif hhi < 2500:
        concentration_level = "⚠️ Moderate"
    else:
        concentration_level = "🔴 High Concentration"
    
    st.markdown(f"**Concentration Level:** {concentration_level}")

with col3:
    # Top 10 titles
    st.markdown("#### Top 10 Titles by Value")
    
    top_titles_df = pd.DataFrame(concentration['top_titles'])
    top_titles_df['total_value'] = top_titles_df['total_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    top_titles_df['value_share'] = top_titles_df['value_share'].apply(lambda x: f"{x*100:.1f}%")
    top_titles_df['roi'] = top_titles_df['roi'].apply(lambda x: f"{x*100:.0f}%")
    
    st.dataframe(
        top_titles_df[['title_name', 'brand', 'total_value', 'value_share', 'roi']], 
        use_container_width=True,
        hide_index=True
    )
