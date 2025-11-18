"""Portfolio Dashboard page for Magic Slate - Enhanced with strategic analytics."""

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
    compute_title_risk_return_data,
    compute_hhi_by_segment,
    compute_over_under_investment,
    compute_new_vs_library_split,
)

st.set_page_config(page_title="Portfolio Dashboard - Magic Slate", page_icon="📊", layout="wide")

st.title("📊 Portfolio Strategy & Analysis")
st.markdown("Comprehensive portfolio analytics and strategic insights for content planning")

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
st.markdown("## 📈 Portfolio Summary")

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

# Risk vs Return Analysis
st.markdown("## 📉 Portfolio Risk / Return Landscape")

risk_return_data = compute_title_risk_return_data(filtered_scorecards, df_titles)

if not risk_return_data.empty:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig = px.scatter(
            risk_return_data,
            x="risk_metric",
            y="roi",
            size="total_value",
            color="brand",
            hover_name="title_name",
            hover_data={
                "risk_metric": ":.3f",
                "roi": ":.1%",
                "total_value": ":$,.0f",
                "brand": True
            },
            labels={
                "risk_metric": "Risk (ROI Volatility)",
                "roi": "Return on Investment",
                "total_value": "Total Value ($)"
            },
            title="Title-Level Risk vs Return by Brand"
        )
        
        # Add quadrant lines
        median_risk = risk_return_data["risk_metric"].median()
        median_roi = risk_return_data["roi"].median()
        
        fig.add_hline(y=median_roi, line_dash="dash", line_color="gray", 
                     annotation_text=f"Median ROI: {median_roi*100:.0f}%")
        fig.add_vline(x=median_risk, line_dash="dash", line_color="gray",
                     annotation_text=f"Median Risk: {median_risk:.2f}")
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Interpretation")
        st.markdown("""
        **Risk Metric**: ROI volatility within brand/genre segment
        
        **Quadrants**:
        - **Top-Left**: High return, low risk (optimal)
        - **Top-Right**: High return, high risk (aggressive)
        - **Bottom-Left**: Low return, low risk (stable)
        - **Bottom-Right**: Low return, high risk (avoid)
        
        **Bubble Size**: Total value generated
        """)
        
        # Quadrant summary
        top_left = risk_return_data[
            (risk_return_data["roi"] > median_roi) & 
            (risk_return_data["risk_metric"] < median_risk)
        ]
        st.metric("Optimal Titles", len(top_left))
        st.caption("High return, low risk")

st.markdown("---")

# Portfolio Health Metrics
st.markdown("## 🎯 Portfolio Health & Concentration")

col1, col2, col3 = st.columns(3)

# HHI by Brand
brand_hhi = compute_hhi_by_segment(filtered_scorecards, segment_by="brand")

with col1:
    st.markdown("### Value Concentration by Brand")
    st.metric("HHI (Brand)", f"{brand_hhi['hhi']:.0f}")
    st.caption(brand_hhi['interpretation'])
    
    if brand_hhi['hhi'] < 1500:
        st.success("✅ Healthy diversification")
    elif brand_hhi['hhi'] < 2500:
        st.warning("⚠️ Moderate concentration")
    else:
        st.error("🔴 High concentration risk")

# HHI by Genre
genre_hhi = compute_hhi_by_segment(filtered_scorecards, segment_by="genre")

with col2:
    st.markdown("### Value Concentration by Genre")
    st.metric("HHI (Genre)", f"{genre_hhi['hhi']:.0f}")
    st.caption(genre_hhi['interpretation'])

# Top titles concentration
concentration = compute_concentration_metrics(filtered_scorecards, top_n=10)

with col3:
    st.markdown("### Top Titles Concentration")
    st.metric("Top 10 Value Share", f"{concentration['top_n_share']*100:.1f}%")
    st.caption(f"{concentration['top_n']} of {concentration['total_titles']} titles")
    
    if concentration['top_n_share'] > 0.6:
        st.warning("⚠️ Value highly concentrated")
    else:
        st.success("✅ Balanced value distribution")

# New vs Library split
new_lib_split = compute_new_vs_library_split(filtered_scorecards, df_titles)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### New Releases vs Library Value")
    
    fig = go.Figure(data=[
        go.Pie(
            labels=["New Releases", "Library"],
            values=[new_lib_split['new_value'], new_lib_split['library_value']],
            marker_colors=['#1f77b4', '#ff7f0e'],
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Value: $%{value:,.0f}<br>Share: %{percent}<extra></extra>'
        )
    ])
    
    fig.update_layout(height=350, title="Value Distribution: New vs Library")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Split Summary")
    st.metric("New Releases Share", f"{new_lib_split['new_share']*100:.1f}%")
    st.caption(f"{new_lib_split['new_count']} titles")
    
    st.metric("Library Share", f"{new_lib_split['library_share']*100:.1f}%")
    st.caption(f"{new_lib_split['library_count']} titles")
    
    st.markdown("---")
    
    if new_lib_split['new_share'] < 0.3:
        st.warning("⚠️ Portfolio skewed toward library")
    elif new_lib_split['new_share'] > 0.7:
        st.info("ℹ️ Portfolio skewed toward new releases")
    else:
        st.success("✅ Balanced new/library mix")

st.markdown("---")

# Over/Under Investment Analysis
st.markdown("## 💰 Investment Efficiency by Segment")

tab1, tab2 = st.tabs(["By Brand", "By Genre"])

with tab1:
    st.markdown("### Brand Investment Analysis")
    
    brand_investment = compute_over_under_investment(filtered_scorecards, segment_by="brand")
    
    if not brand_investment.empty:
        # Format for display
        display_df = brand_investment.copy()
        display_df["cost_share"] = display_df["cost_share"].apply(lambda x: f"{x*100:.1f}%")
        display_df["value_share"] = display_df["value_share"].apply(lambda x: f"{x*100:.1f}%")
        display_df.columns = ["Brand", "Cost Share", "Value Share", "Status"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Summary insights
        over_invested = brand_investment[brand_investment["status"] == "Over-invested ⚠️"]
        under_invested = brand_investment[brand_investment["status"] == "Under-invested ✅"]
        
        st.markdown("#### Key Insights:")
        
        if not under_invested.empty:
            under_brands = ", ".join(under_invested["brand"].tolist())
            st.success(f"**Under-invested (opportunities)**: {under_brands} - Consider increasing investment")
        
        if not over_invested.empty:
            over_brands = ", ".join(over_invested["brand"].tolist())
            st.warning(f"**Over-invested (review needed)**: {over_brands} - Returns not matching investment level")

with tab2:
    st.markdown("### Genre Investment Analysis")
    
    genre_investment = compute_over_under_investment(filtered_scorecards, segment_by="genre")
    
    if not genre_investment.empty:
        # Format for display
        display_df = genre_investment.copy()
        display_df["cost_share"] = display_df["cost_share"].apply(lambda x: f"{x*100:.1f}%")
        display_df["value_share"] = display_df["value_share"].apply(lambda x: f"{x*100:.1f}%")
        display_df.columns = ["Genre", "Cost Share", "Value Share", "Status"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Summary insights
        over_invested = genre_investment[genre_investment["status"] == "Over-invested ⚠️"]
        under_invested = genre_investment[genre_investment["status"] == "Under-invested ✅"]
        
        st.markdown("#### Key Insights:")
        
        if not under_invested.empty:
            under_genres = ", ".join(under_invested["genre"].tolist())
            st.success(f"**Under-invested (opportunities)**: {under_genres}")
        
        if not over_invested.empty:
            over_genres = ", ".join(over_invested["genre"].tolist())
            st.warning(f"**Over-invested (review needed)**: {over_genres}")

st.markdown("---")

# View selector (existing views)
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
