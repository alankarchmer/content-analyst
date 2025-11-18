"""Data & Assumptions page for Magic Slate."""

import streamlit as st
import pandas as pd
from magicslate import assumptions as asmp
from magicslate.exports import export_to_excel

st.set_page_config(page_title="Data & Assumptions - Magic Slate", page_icon="📁", layout="wide")

st.title("📁 Data & Assumptions")
st.markdown("View raw data, business assumptions, and export analytics")

# Get data from session state
df_titles = st.session_state.df_titles
df_engagement = st.session_state.df_engagement
df_quality = st.session_state.df_quality
df_scorecards = st.session_state.df_scorecards

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Raw Data", "⚙️ Assumptions", "📥 Export", "🔄 Refresh Data"
])

with tab1:
    st.markdown("## 📊 Raw Data")
    
    st.markdown("### Title Catalog")
    st.markdown(f"**{len(df_titles)} titles** in catalog")
    
    # Display options
    show_all_titles = st.checkbox("Show all columns", value=False, key="titles_all")
    
    if show_all_titles:
        st.dataframe(df_titles, use_container_width=True, height=400)
    else:
        display_cols = ['title_id', 'title_name', 'brand', 'genre', 'platform_primary', 
                       'content_type', 'production_budget_tier', 'estimated_production_budget']
        st.dataframe(df_titles[display_cols], use_container_width=True, height=400)
    
    st.markdown("---")
    
    st.markdown("### Engagement Data (Sample)")
    st.markdown(f"**{len(df_engagement)} records** total (showing first 500)")
    
    sample_engagement = df_engagement.head(500)
    st.dataframe(sample_engagement, use_container_width=True, height=400)
    
    st.markdown("---")
    
    st.markdown("### Quality Metrics")
    st.markdown(f"**{len(df_quality)} titles** with quality scores")
    
    st.dataframe(df_quality, use_container_width=True, height=400)
    
    st.markdown("---")
    
    st.markdown("### Computed Scorecards (Sample)")
    st.markdown(f"**{len(df_scorecards)} titles** with computed metrics (showing first 100)")
    
    sample_scorecards = df_scorecards.head(100)
    
    # Format for display
    display_scorecards = sample_scorecards.copy()
    
    currency_cols = ['production_budget', 'marketing_spend', 'total_cost', 
                    'streaming_value', 'ad_value', 'theatrical_value', 
                    'pvod_value', 'total_value', 'cost_per_hour_viewed']
    
    for col in currency_cols:
        if col in display_scorecards.columns:
            display_scorecards[col] = display_scorecards[col].apply(
                lambda x: f"${x/1_000_000:.2f}M" if x >= 1_000_000 else f"${x:,.0f}"
            )
    
    if 'roi' in display_scorecards.columns:
        display_scorecards['roi'] = display_scorecards['roi'].apply(lambda x: f"{x*100:.1f}%")
    
    st.dataframe(display_scorecards, use_container_width=True, height=400)

with tab2:
    st.markdown("## ⚙️ Business Assumptions")
    
    st.markdown("""
    These are the core business assumptions used throughout the analytics platform.
    These parameters drive the economic models and value calculations.
    """)
    
    st.markdown("---")
    
    # Display assumptions in organized sections
    st.markdown("### 💰 Streaming Economics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Disney+ ARPU (monthly)", f"${asmp.DISNEY_PLUS_ARPU:.2f}")
        st.metric("Hulu ARPU (monthly)", f"${asmp.HULU_ARPU:.2f}")
    
    with col2:
        st.metric("Hulu Ad ARPU (per hour)", f"${asmp.HULU_AD_ARPU_PER_HOUR:.2f}")
        st.metric("Base Monthly Churn Rate", f"{asmp.BASE_MONTHLY_CHURN_RATE:.1%}")
    
    st.markdown("---")
    
    st.markdown("### 📈 Engagement to Value Conversion")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Acquisition Base (per 1M hours)", f"{asmp.ACQUISITION_CONVERSION_BASE} subs")
        st.metric("Acquisition Quality Multiplier", f"{asmp.ACQUISITION_QUALITY_MULTIPLIER}x")
    
    with col2:
        st.metric("Retention Base (per 1M hours)", f"{asmp.RETENTION_IMPACT_BASE} sub-months")
        st.metric("Retention Quality Multiplier", f"{asmp.RETENTION_QUALITY_MULTIPLIER}x")
    
    st.markdown("---")
    
    st.markdown("### 🎞️ Windowing & Licensing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("PVOD Cannibalization Factor", f"{asmp.PVOD_CANNIBALIZATION_FACTOR:.0%}")
        st.metric("License Cannibalization Factor", f"{asmp.LICENSE_CANNIBALIZATION_FACTOR:.0%}")
    
    with col2:
        st.metric("PVOD Revenue (% of Theatrical)", f"{asmp.PVOD_REVENUE_PCT_OF_THEATRICAL:.0%}")
    
    st.markdown("**Theatrical Multipliers** (Box office as multiple of production budget):")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Low Budget", f"{asmp.THEATRICAL_MULTIPLIER_BY_TIER['Low']}x")
    with col2:
        st.metric("Medium Budget", f"{asmp.THEATRICAL_MULTIPLIER_BY_TIER['Medium']}x")
    with col3:
        st.metric("High Budget", f"{asmp.THEATRICAL_MULTIPLIER_BY_TIER['High']}x")
    
    st.markdown("---")
    
    st.markdown("### 💵 Financial Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Discount Rate (NPV)", f"{asmp.DISCOUNT_RATE:.0%}")
    
    with col2:
        st.metric("Periods per Year", f"{asmp.MONTHS_PER_YEAR} months")
    
    st.markdown("---")
    
    st.markdown("### 🏆 Classification Thresholds")
    
    st.markdown("**Tentpole Criteria:**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Min Budget", f"${asmp.TENTPOLE_THRESHOLD['min_budget']/1_000_000:.0f}M")
    with col2:
        st.metric("Min Value", f"${asmp.TENTPOLE_THRESHOLD['min_value']/1_000_000:.0f}M")
    
    st.markdown("**Niche Gem Criteria:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Max Budget", f"${asmp.NICHE_GEM_THRESHOLD['max_budget']/1_000_000:.0f}M")
    with col2:
        st.metric("Min ROI", f"{asmp.NICHE_GEM_THRESHOLD['min_roi']:.0%}")
    with col3:
        st.metric("Max Cost/Hour", f"${asmp.NICHE_GEM_THRESHOLD['max_cost_per_hour']:.2f}")
    
    st.markdown("**Workhorse Criteria:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Min Budget", f"${asmp.WORKHORSE_THRESHOLD['min_budget']/1_000_000:.0f}M")
    with col2:
        st.metric("Min ROI", f"{asmp.WORKHORSE_THRESHOLD['min_roi']:.0%}")
    with col3:
        st.metric("Max ROI", f"{asmp.WORKHORSE_THRESHOLD['max_roi']:.0%}")

with tab3:
    st.markdown("## 📥 Export Data")
    
    st.markdown("""
    Download a comprehensive Excel workbook containing all analytics data, 
    including raw data, computed scorecards, and portfolio summaries.
    """)
    
    st.markdown("### 📊 Excel Export Contents")
    
    st.markdown("""
    The exported workbook includes the following sheets:
    
    - **Assumptions**: All business assumptions and parameters
    - **Title Catalog**: Complete title metadata
    - **Engagement Sample**: Sample engagement data (first 1000 records)
    - **Quality Metrics**: Quality and buzz scores for all titles
    - **Title Scorecards**: Comprehensive per-title analytics
    - **Portfolio by Brand**: Aggregated brand-level metrics
    - **Portfolio by Genre**: Aggregated genre-level metrics
    - **Portfolio by Platform**: Aggregated platform-level metrics
    - **Classification**: Distribution by title classification
    - **Top 20 Titles**: Top-performing titles by value
    - **Concentration Summary**: Portfolio concentration metrics
    """)
    
    st.markdown("---")
    
    if st.button("📥 Generate Excel Report", type="primary"):
        with st.spinner("Generating Excel workbook..."):
            excel_buffer = export_to_excel(
                df_titles=df_titles,
                df_engagement=df_engagement,
                df_quality=df_quality,
                df_scorecards=df_scorecards
            )
            
            st.download_button(
                label="⬇️ Download Excel Workbook",
                data=excel_buffer,
                file_name="magic_slate_analytics.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success("✅ Excel workbook generated successfully!")

with tab4:
    st.markdown("## 🔄 Refresh Data")
    
    st.markdown("""
    The synthetic data is generated once and cached. If you want to regenerate 
    the data with different random values, use the button below.
    
    ⚠️ **Warning**: This will regenerate all data and clear all current analytics.
    """)
    
    st.markdown("---")
    
    if st.button("🔄 Regenerate Synthetic Data", type="secondary"):
        st.warning("Are you sure? This will regenerate all data.")
        
        confirm_col1, confirm_col2 = st.columns(2)
        
        with confirm_col1:
            if st.button("✅ Yes, Regenerate"):
                with st.spinner("Regenerating data..."):
                    from magicslate import loaders
                    from magicslate.title_scorecard import compute_all_scorecards
                    
                    # Regenerate data
                    df_titles, df_engagement, df_quality = loaders.refresh_data()
                    
                    # Update session state
                    st.session_state.df_titles = df_titles
                    st.session_state.df_engagement = df_engagement
                    st.session_state.df_quality = df_quality
                    
                    # Recompute scorecards
                    df_scorecards = compute_all_scorecards(df_titles, df_engagement, df_quality)
                    st.session_state.df_scorecards = df_scorecards
                    
                    st.success("✅ Data regenerated successfully! Please refresh the page.")
        
        with confirm_col2:
            if st.button("❌ Cancel"):
                st.info("Regeneration cancelled.")
    
    st.markdown("---")
    
    st.markdown("### 📊 Current Data Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Titles", len(df_titles))
        st.metric("Engagement Records", len(df_engagement))
    
    with col2:
        total_hours = df_engagement["proxy_hours_viewed"].sum() / 1_000_000
        st.metric("Total Hours", f"{total_hours:.1f}M")
        
        avg_hours_per_title = total_hours / len(df_titles)
        st.metric("Avg Hours per Title", f"{avg_hours_per_title:.1f}M")
    
    with col3:
        brands = df_titles["brand"].nunique()
        genres = df_titles["genre"].nunique()
        st.metric("Brands", brands)
        st.metric("Genres", genres)
