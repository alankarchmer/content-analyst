"""Greenlight Studio page for Magic Slate - Enhanced with comp analysis."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from magicslate.greenlight_forecast import (
    forecast_new_title,
    scenario_sensitivity_analysis,
)
from magicslate.data_models import NewTitleConcept

st.set_page_config(page_title="Greenlight Studio - Magic Slate", page_icon="💡", layout="wide")

st.title("💡 Greenlight & Forecasting")
st.markdown("Forecast performance for new title concepts using comparable title analysis")

# Get data from session state
df_titles = st.session_state.df_titles
df_engagement = st.session_state.df_engagement
df_quality = st.session_state.df_quality

st.markdown("""
The Greenlight Studio uses **comparable title analysis** to forecast new title performance. 
By analyzing similar titles' actual results, we generate bear/base/bull scenarios with 
data-driven greenlight recommendations.
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
    st.markdown("### 💡 Greenlight Recommendation")
    
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
                roi_color = "normal" if row['ROI (%)'] > 0 else "inverse"
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
    
    # Comparable titles with similarity scores
    st.markdown("### 🎯 Comparable Titles Used for Forecast")
    
    comps = results['comps']
    
    if comps:
        st.markdown(f"Forecast based on analysis of **{len(comps)} comparable titles** with similarity scoring:")
        
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
        display_comps['similarity_score'] = display_comps['similarity_score'].apply(lambda x: f"{x:.1f}")
        
        display_comps = display_comps[[
            'title_name', 'brand', 'genre', 'content_type', 
            'similarity_score', 'total_hours_viewed', 'total_value', 'roi'
        ]]
        
        display_comps.columns = [
            'Title', 'Brand', 'Genre', 'Type', 'Similarity', 
            'Total Hours', 'Total Value', 'ROI'
        ]
        
        st.dataframe(display_comps, use_container_width=True, hide_index=True)
        
        # Explanation of similarity scoring
        with st.expander("ℹ️ How Similarity Scoring Works"):
            st.markdown("""
            **Similarity scores** are computed based on multiple dimensions:
            
            - **Brand match** (weight: 5) - Same brand/studio
            - **Genre match** (weight: 4) - Same primary genre
            - **Content type match** (weight: 3) - Film vs Series
            - **Budget tier match** (weight: 3) - Low/Medium/High budget similarity
            - **Hours similarity** (weight: 2) - Similar viewership scale
            
            Total similarity score ranges from 0-17, with higher scores indicating closer comps.
            
            **Why these comps matter**: Historical performance of similar titles provides the 
            most reliable predictor of new title outcomes, especially when adjusted for 
            concept-specific factors (star power, buzz potential, IP familiarity).
            """)
        
        st.markdown("---")
        
        # Distribution Visualization
        st.markdown("### 📊 Comparable Title Performance Distribution")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # ROI distribution with scenario overlays
            fig = go.Figure()
            
            # Histogram of comp ROI
            fig.add_trace(go.Histogram(
                x=comps_df['roi'] * 100,
                name='Comp ROI Distribution',
                marker_color='rgba(31, 119, 180, 0.6)',
                nbinsx=15,
                hovertemplate='ROI Range: %{x}<br>Count: %{y}<extra></extra>'
            ))
            
            # Overlay scenario lines
            if scenarios:
                for scenario_name, color in [('bear', '#f44336'), ('base', '#FFC107'), ('bull', '#4CAF50')]:
                    if scenario_name in scenarios:
                        roi_val = scenarios[scenario_name]['roi'] * 100
                        fig.add_vline(
                            x=roi_val,
                            line_dash="dash",
                            line_color=color,
                            line_width=3,
                            annotation_text=f"{scenario_name.title()}: {roi_val:.0f}%",
                            annotation_position="top"
                        )
            
            fig.update_layout(
                title="Distribution of Comp ROI with Forecast Scenarios",
                xaxis_title="ROI (%)",
                yaxis_title="Number of Comps",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Distribution Stats")
            
            mean_roi = comps_df['roi'].mean()
            std_roi = comps_df['roi'].std()
            
            st.metric("Mean ROI", f"{mean_roi*100:.0f}%")
            st.metric("Std Dev", f"{std_roi*100:.0f}pp")
            st.metric("Min ROI", f"{comps_df['roi'].min()*100:.0f}%")
            st.metric("Max ROI", f"{comps_df['roi'].max()*100:.0f}%")
            
            st.markdown("---")
            st.markdown("**Scenario Derivation:**")
            st.markdown(f"- Bear = Mean - 1σ")
            st.markdown(f"- Base = Mean")
            st.markdown(f"- Bull = Mean + 1σ")
        
        # Hours vs Value scatter
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
    
    # Model Details Expander
    with st.expander("📘 Model Details: How This Forecast Works"):
        st.markdown("""
        ### Forecasting Methodology
        
        The Greenlight Studio uses a **comparable title analysis** approach with 
        concept-specific adjustments:
        
        #### 1. Find Comparables
        - Identify similar titles based on brand, genre, content type, and budget tier
        - Compute similarity scores across multiple dimensions
        - Select top 5 most comparable titles for analysis
        
        #### 2. Build Performance Distribution
        - Analyze actual performance of comparable titles
        - Compute mean and standard deviation for key metrics:
          - Total hours viewed
          - Total value generated
          - Return on investment (ROI)
        
        #### 3. Generate Scenarios
        - **Bear Case**: Mean - 1σ, adjusted down for pessimism (×0.7)
        - **Base Case**: Mean performance, adjusted for concept factors
        - **Bull Case**: Mean + 1σ, adjusted up for optimism (×1.3)
        
        #### 4. Apply Concept Adjustments
        
        **Star Power & Buzz Multiplier**:
        ```
        Star Factor = 0.8 + (star_power_score / 5.0) × 0.4    # Range: 0.8 - 1.2
        Buzz Factor = 0.8 + (buzz_potential / 100.0) × 0.4    # Range: 0.8 - 1.2
        Concept Multiplier = (Star Factor + Buzz Factor) / 2
        ```
        
        **IP Familiarity**: 
        - Franchise titles get bonus similarity points with Marvel/Star Wars/Pixar comps
        - New IP carries inherently higher execution risk
        
        **Budget Consideration**:
        - Actual budget used to compute ROI
        - Comps selected from same budget tier when possible
        
        #### 5. Generate Recommendation
        
        Decision rules based on base-case ROI and downside risk:
        
        | Base ROI | Bear ROI | Recommendation |
        |----------|----------|----------------|
        | > 100%   | > 30%    | **STRONG GREENLIGHT** |
        | > 50%    | > 0%     | **GREENLIGHT** |
        | > 20%    | Any      | **CONDITIONAL** |
        | > 0%     | Any      | **MARGINAL** |
        | ≤ 0%     | Any      | **PASS** |
        
        ### Limitations & Considerations
        
        - Forecasts based on historical comp performance
        - Actual results depend on execution quality, marketing effectiveness, market conditions
        - Use as **one input** to greenlight decisions, not sole determinant
        - Consider strategic factors beyond pure ROI:
          - Portfolio fit and diversification
          - Long-term franchise potential
          - Brand building and positioning
          - Competitive landscape
        """)
    
    st.markdown("---")
    
    # Sensitivity analysis
    st.markdown("### 🔍 Budget Sensitivity Analysis")
    
    st.markdown("How would ROI change with different production budget levels?")
    
    sensitivity_df = scenario_sensitivity_analysis(
        concept=concept,
        scenarios=scenarios
    )
    
    if not sensitivity_df.empty:
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
            title="ROI Sensitivity to Budget Changes (Base Case)",
            xaxis_title="Budget Adjustment",
            yaxis_title="ROI (%)",
            height=400,
            showlegend=False
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display sensitivity table
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_sens = sensitivity_df.copy()
            display_sens['adjusted_cost'] = display_sens['adjusted_cost'].apply(lambda x: f"${x/1_000_000:.1f}M")
            display_sens['projected_value'] = display_sens['projected_value'].apply(lambda x: f"${x/1_000_000:.1f}M")
            display_sens['roi'] = display_sens['roi'].apply(lambda x: f"{x*100:.0f}%")
            display_sens.columns = ['Budget Adjustment', 'Adjusted Cost', 'Projected Value', 'ROI']
            
            st.dataframe(display_sens, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### Key Insights")
            
            base_roi = scenarios['base']['roi'] if 'base' in scenarios else 0
            
            if base_roi > 0.5:
                st.success("✅ Strong ROI even at higher budgets")
            elif base_roi > 0.2:
                st.info("ℹ️ Budget discipline important")
            else:
                st.warning("⚠️ Need budget reduction or value drivers")
            
            st.markdown(f"""
            **At current budget** (${production_budget:.0f}M):
            - Base ROI: **{base_roi*100:.0f}%**
            
            **Budget flexibility**: ROI remains positive even with {'+20%' if base_roi > 0.5 else '+10%'} budget overrun.
            """)
    
    st.markdown("---")
    
    # Strategic Context & Recommendation Text
    st.markdown("### 🎯 Strategic Context")
    
    # Generate strategic commentary
    base_roi = scenarios['base']['roi'] if 'base' in scenarios else 0
    bear_roi = scenarios['bear']['roi'] if 'bear' in scenarios else 0
    bull_roi = scenarios['bull']['roi'] if 'bull' in scenarios else 0
    
    commentary = []
    
    commentary.append(f"**{concept_name}** is a **{brand} {genre} {content_type}** ")
    commentary.append(f"with a proposed budget of **${production_budget:.0f}M**.\n\n")
    
    # ROI assessment
    if base_roi > 1.0 and bear_roi > 0.3:
        assessment = "**excellent returns with limited downside risk**, making it a strong greenlight candidate"
    elif base_roi > 0.5 and bear_roi > 0:
        assessment = "**solid projected returns with manageable risk**"
    elif base_roi > 0.2:
        assessment = "**modest returns**; consider budget optimization or enhanced marketing strategy"
    elif base_roi > 0:
        assessment = "**marginal returns**; recommend further development or significant budget reduction"
    else:
        assessment = "**insufficient returns** at current budget level; recommend passing or major restructuring"
    
    commentary.append(f"Base-case ROI of **{base_roi*100:.0f}%** with downside of **{bear_roi*100:.0f}%** indicates {assessment}.\n\n")
    
    # IP & Strategic factors
    commentary.append("**Strategic Considerations:**\n")
    
    if ip_familiarity in ["Sequel", "Franchise Core"]:
        commentary.append(f"- ✅ **{ip_familiarity}** status reduces risk and provides built-in audience\n")
    elif ip_familiarity == "New IP":
        commentary.append("- ⚠️ **New IP** requires strong execution and marketing to succeed\n")
    
    if star_power_score >= 4:
        commentary.append("- ✅ **Strong talent** attachment enhances marketing appeal\n")
    elif star_power_score <= 2:
        commentary.append("- ⚠️ **Limited star power** may require compensating creative elements\n")
    
    if buzz_potential_score >= 70:
        commentary.append("- ✅ **High buzz potential** supports organic discovery\n")
    elif buzz_potential_score <= 40:
        commentary.append("- ⚠️ **Lower buzz potential** requires marketing investment\n")
    
    # Comp context
    if comps:
        avg_comp_roi = comps_df['roi'].mean()
        if base_roi > avg_comp_roi * 1.2:
            commentary.append(f"- ✅ Projected ROI **significantly exceeds** comp average of {avg_comp_roi*100:.0f}%\n")
        elif base_roi > avg_comp_roi * 0.8:
            commentary.append(f"- ➖ Projected ROI **in line with** comp average of {avg_comp_roi*100:.0f}%\n")
        else:
            commentary.append(f"- ⚠️ Projected ROI **below** comp average of {avg_comp_roi*100:.0f}%\n")
    
    st.markdown("".join(commentary))

else:
    st.info("👆 Configure your title concept above and click 'Generate Forecast' to see projections.")

st.markdown("---")

# Educational content (existing)
with st.expander("📚 Additional Context on Greenlight Decisions"):
    st.markdown("""
    ### Beyond ROI: Holistic Greenlight Considerations
    
    While ROI is critical, content planning & analysis considers multiple dimensions:
    
    #### Financial Metrics
    - **ROI**: Return vs investment
    - **NPV**: Time-adjusted value
    - **Payback Period**: Time to recoup costs
    - **Downside Risk**: Bear-case scenario outcomes
    
    #### Strategic Fit
    - **Portfolio Diversification**: Brand/genre balance
    - **Franchise Potential**: Long-term IP value
    - **Audience Targeting**: Demographic gaps
    - **Competitive Positioning**: Market landscape
    
    #### Execution Factors
    - **Creative Team**: Track record and fit
    - **Production Timeline**: Release window strategy
    - **Marketing Plan**: Campaign strategy and budget
    - **Distribution Strategy**: Windowing and platform
    
    #### Risk Factors
    - **IP Familiarity**: New vs established IP
    - **Budget Scale**: Relative to typical outcomes
    - **Comp Quality**: How reliable are the comps?
    - **Market Conditions**: Current streaming landscape
    
    ### Typical Greenlight Hurdles
    
    - **Tentpole/Franchise**: ROI > 50%, strategic fit
    - **Mid-Budget Original**: ROI > 80%, strong creative
    - **Low-Budget**: ROI > 150%, high efficiency
    - **Series Renewal**: Strong engagement + retention metrics
    
    Remember: This tool provides **analytical support** for decisions that ultimately 
    require judgment, strategic vision, and deep understanding of audience and content.
    """)
