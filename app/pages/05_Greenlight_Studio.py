"""Greenlight Studio page for Magic Slate."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from magicslate.greenlight_forecast import (
    forecast_new_title,
    scenario_sensitivity_analysis,
)
from magicslate.data_models import NewTitleConcept

st.set_page_config(page_title="Greenlight Studio - Magic Slate", page_icon="💡", layout="wide")

st.title("💡 Greenlight Studio")
st.markdown("Forecast performance for new title concepts and support greenlight decisions")

# Get data from session state
df_titles = st.session_state.df_titles
df_engagement = st.session_state.df_engagement
df_quality = st.session_state.df_quality

st.markdown("""
The Greenlight Studio uses comparable title analysis to forecast the performance 
of new title concepts. Configure your proposed title below and get bear/base/bull 
scenarios with a greenlight recommendation.
""")

st.markdown("---")

# Concept configuration
st.markdown("## 🎬 Configure Your Title Concept")

col1, col2 = st.columns(2)

with col1:
    concept_name = st.text_input(
        "Title Concept Name",
        value="Untitled Project",
        help="Working title for your concept"
    )
    
    brand = st.selectbox(
        "Brand",
        sorted(df_titles["brand"].unique().tolist()),
        help="Which brand/studio will produce this title"
    )
    
    genre = st.selectbox(
        "Genre",
        sorted(df_titles["genre"].unique().tolist()),
        help="Primary genre"
    )
    
    content_type = st.selectbox(
        "Content Type",
        ["Film", "Series"],
        help="Film or series"
    )
    
    if content_type == "Series":
        season_number = st.number_input("Season Number", min_value=1, max_value=10, value=1)
        episode_count = st.number_input("Episode Count", min_value=1, max_value=24, value=8)
    else:
        season_number = None
        episode_count = None

with col2:
    production_budget = st.number_input(
        "Production Budget ($M)",
        min_value=1.0,
        max_value=300.0,
        value=50.0,
        step=5.0,
        help="Estimated production budget in millions"
    )
    
    marketing_spend = st.number_input(
        "Marketing Spend ($M)",
        min_value=0.0,
        max_value=150.0,
        value=production_budget * 0.3,
        step=5.0,
        help="Estimated marketing spend in millions"
    )
    
    ip_familiarity = st.selectbox(
        "IP Familiarity",
        ["New IP", "Sequel", "Spin-off", "Franchise Core"],
        help="How familiar is this IP to audiences"
    )
    
    star_power_score = st.slider(
        "Star Power Score",
        min_value=1,
        max_value=5,
        value=3,
        help="1 = No-name cast, 5 = A-list ensemble"
    )
    
    buzz_potential_score = st.slider(
        "Buzz Potential Score",
        min_value=0,
        max_value=100,
        value=50,
        help="Expected social media and cultural buzz (0-100)"
    )

# Create concept object
concept = NewTitleConcept(
    concept_name=concept_name,
    brand=brand,
    genre=genre,
    content_type=content_type,
    season_number=season_number,
    episode_count=episode_count,
    production_budget_estimate=production_budget,
    marketing_spend_estimate=marketing_spend,
    ip_familiarity=ip_familiarity,
    star_power_score=star_power_score,
    buzz_potential_score=buzz_potential_score,
)

# Run forecast button
if st.button("🚀 Generate Forecast", type="primary"):
    with st.spinner("Analyzing comparable titles and generating forecast..."):
        forecast_results = forecast_new_title(
            concept=concept,
            df_titles=df_titles,
            df_engagement=df_engagement,
            df_quality=df_quality
        )
        
        st.session_state.forecast_results = forecast_results

# Display results
if "forecast_results" in st.session_state and st.session_state.forecast_results is not None:
    results = st.session_state.forecast_results
    
    st.markdown("---")
    st.markdown("## 📊 Forecast Results")
    
    # Recommendation
    st.markdown("### 💡 Recommendation")
    
    recommendation_html = results['recommendation'].replace('\n', '<br>')
    st.markdown(recommendation_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Scenarios
    st.markdown("### 📈 Performance Scenarios")
    
    scenarios = results['scenarios']
    
    if scenarios:
        # Create scenario comparison table
        scenario_data = []
        for scenario_name in ['bear', 'base', 'bull']:
            if scenario_name in scenarios:
                s = scenarios[scenario_name]
                scenario_data.append({
                    'Scenario': scenario_name.title(),
                    'Total Hours (M)': s['total_hours_viewed'] / 1_000_000,
                    'Total Value ($M)': s['total_value'] / 1_000_000,
                    'Total Cost ($M)': s['total_cost'] / 1_000_000,
                    'ROI (%)': s['roi'] * 100,
                })
        
        scenario_df = pd.DataFrame(scenario_data)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        for idx, row in scenario_df.iterrows():
            with [col1, col2, col3][idx]:
                st.markdown(f"#### {row['Scenario']} Case")
                st.metric("Hours Viewed", f"{row['Total Hours (M)']:.1f}M")
                st.metric("Total Value", f"${row['Total Value ($M)']:.1f}M")
                st.metric("ROI", f"{row['ROI (%)']:.0f}%")
        
        # ROI comparison chart
        fig = go.Figure(data=[
            go.Bar(
                x=scenario_df['Scenario'],
                y=scenario_df['ROI (%)'],
                marker_color=['#f44336', '#FFC107', '#4CAF50'],
                text=scenario_df['ROI (%)'].apply(lambda x: f"{x:.0f}%"),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="ROI by Scenario",
            xaxis_title="Scenario",
            yaxis_title="ROI (%)",
            height=400,
            showlegend=False
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Value comparison
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Value',
            x=scenario_df['Scenario'],
            y=scenario_df['Total Value ($M)'],
            marker_color='#1f77b4',
            text=scenario_df['Total Value ($M)'].apply(lambda x: f"${x:.1f}M"),
            textposition='auto',
        ))
        
        fig.add_trace(go.Bar(
            name='Cost',
            x=scenario_df['Scenario'],
            y=scenario_df['Total Cost ($M)'],
            marker_color='#ff7f0e',
            text=scenario_df['Total Cost ($M)'].apply(lambda x: f"${x:.1f}M"),
            textposition='auto',
        ))
        
        fig.update_layout(
            title="Value vs Cost by Scenario",
            xaxis_title="Scenario",
            yaxis_title="Amount ($M)",
            height=400,
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Comparable titles
    st.markdown("### 🎯 Comparable Titles Used")
    
    comps = results['comps']
    
    if comps:
        st.markdown(f"Forecast based on analysis of **{len(comps)} comparable titles**:")
        
        comps_df = pd.DataFrame(comps)
        
        # Format for display
        display_comps = comps_df.copy()
        display_comps['total_hours_viewed'] = display_comps['total_hours_viewed'].apply(
            lambda x: f"{x/1_000_000:.1f}M"
        )
        display_comps['total_value'] = display_comps['total_value'].apply(
            lambda x: f"${x/1_000_000:.1f}M"
        )
        display_comps['roi'] = display_comps['roi'].apply(lambda x: f"{x*100:.0f}%")
        
        st.dataframe(
            display_comps[['title_name', 'brand', 'genre', 'content_type', 
                          'similarity_score', 'total_hours_viewed', 'total_value', 'roi']],
            use_container_width=True,
            hide_index=True
        )
        
        # Comp performance distribution
        st.markdown("#### Comparable Title Performance Distribution")
        
        fig = px.scatter(
            comps_df,
            x='total_hours_viewed',
            y='total_value',
            size='similarity_score',
            color='roi',
            hover_name='title_name',
            labels={
                'total_hours_viewed': 'Total Hours Viewed',
                'total_value': 'Total Value ($)',
                'roi': 'ROI'
            },
            title="Comp Performance: Hours vs Value",
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Sensitivity analysis
    st.markdown("### 🔍 Cost Sensitivity Analysis")
    
    st.markdown("How would ROI change with different production budgets?")
    
    sensitivity_df = scenario_sensitivity_analysis(
        concept=concept,
        scenarios=scenarios
    )
    
    fig = go.Figure(data=[
        go.Bar(
            x=sensitivity_df['cost_adjustment'],
            y=sensitivity_df['roi'] * 100,
            marker_color=sensitivity_df['roi'].apply(
                lambda x: '#4CAF50' if x > 0.5 else ('#FFC107' if x > 0 else '#f44336')
            ),
            text=sensitivity_df['roi'].apply(lambda x: f"{x*100:.0f}%"),
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="ROI Sensitivity to Budget Changes",
        xaxis_title="Budget Adjustment",
        yaxis_title="ROI (%)",
        height=400,
        showlegend=False
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display sensitivity table
    display_sens = sensitivity_df.copy()
    display_sens['adjusted_cost'] = display_sens['adjusted_cost'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_sens['projected_value'] = display_sens['projected_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
    display_sens['roi'] = display_sens['roi'].apply(lambda x: f"{x*100:.0f}%")
    
    st.dataframe(display_sens, use_container_width=True, hide_index=True)

else:
    st.info("👆 Configure your title concept above and click 'Generate Forecast' to see projections.")

st.markdown("---")

# Educational content
with st.expander("📚 How the Forecast Works"):
    st.markdown("""
    ### Forecasting Methodology
    
    The Greenlight Studio uses a **comparable title analysis** approach:
    
    1. **Find Comparables**: 
       - Identifies similar titles based on brand, genre, content type, and budget tier
       - Scores similarity on multiple dimensions
       - Selects top 5 most comparable titles
    
    2. **Build Performance Distribution**:
       - Analyzes actual performance of comparable titles
       - Computes mean and standard deviation for key metrics
       - Considers hours viewed, total value, and ROI
    
    3. **Generate Scenarios**:
       - **Bear Case**: Mean - 1 standard deviation, with pessimistic adjustments
       - **Base Case**: Mean performance, adjusted for concept-specific factors
       - **Bull Case**: Mean + 1 standard deviation, with optimistic adjustments
    
    4. **Apply Concept Adjustments**:
       - Star power and buzz potential modulate the forecast
       - IP familiarity affects risk profile
       - Budget tier influences comp selection
    
    5. **Generate Recommendation**:
       - Evaluates base-case ROI and downside risk
       - Considers strategic factors (IP, talent, buzz)
       - Provides actionable greenlight guidance
    
    ### Limitations
    
    - Forecasts are based on historical performance of similar titles
    - Actual performance depends on execution quality, marketing, and market conditions
    - Use as one input to greenlight decisions, not the sole determinant
    - Consider strategic and portfolio factors beyond pure ROI
    """)
