"""Methodology & Analyst Notebook page for Magic Slate."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from magicslate.title_scorecard import compute_title_scorecard, generate_title_narrative
from magicslate.metrics import (
    compute_advanced_engagement_metrics,
    fit_engagement_curve_model,
    find_comparable_titles_for_title,
)
from magicslate.portfolio_dashboard import (
    compute_portfolio_summary,
    compute_title_risk_return_data,
)
from magicslate.greenlight_forecast import forecast_new_title
from magicslate.windowing_simulator import simulate_windowing_scenarios
from magicslate.data_models import NewTitleConcept, WindowingScenario

st.set_page_config(page_title="Methodology - Magic Slate", page_icon="📚", layout="wide")

st.title("📚 Methodology & Analyst Notebook")
st.markdown("Technical documentation and case study demonstrating content planning & analysis capabilities")

# Get data from session state
df_titles = st.session_state.df_titles
df_engagement = st.session_state.df_engagement
df_quality = st.session_state.df_quality
df_scorecards = st.session_state.df_scorecards

st.markdown("---")

# Introduction
st.markdown("""
## 📋 About This Project

**Magic Slate** is a comprehensive content planning & analysis platform designed to demonstrate 
end-to-end analytical capabilities for a Content Planning & Analysis role at Disney+.

This notebook documents the methodology, provides technical details, and presents a full 
case study walkthrough showing how these tools would be used in real content decision-making.

**Note on Data**: All data is synthetically generated to mimic Disney+/Hulu catalog patterns. 
Real-world applications would use internal streaming analytics, financial data, and research.
""")

st.markdown("---")

# Methodology Sections
st.markdown("## 🔬 Methodology")

with st.expander("### 1. Data Simulation Approach", expanded=False):
    st.markdown("""
    #### Why Synthetic Data?
    
    Without access to proprietary Disney+ streaming data, we generate synthetic data that 
    captures key statistical properties of real streaming catalogs:
    
    **Title Catalog**:
    - Realistic distribution of brands (Marvel, Pixar, Disney Animation, Star Wars, etc.)
    - Genre variety (Action, Comedy, Drama, Sci-Fi, Fantasy, Animation, etc.)
    - Budget tiers (Low: <$20M, Medium: $20-80M, High: >$80M)
    - Platform distribution (Disney+ premium, Hulu general entertainment)
    - Content types (Films, Series with seasons/episodes)
    
    **Engagement Generation**:
    - Weekly time-series data for each title
    - Peak week determined by content type, quality, and brand
    - Exponential decay post-peak with variation by title attributes
    - Long-tail behavior based on quality and genre
    - Total hours calibrated to match scale of real streaming platforms
    
    **Quality Scores**:
    - Critic scores (0-100, normally distributed around 72)
    - Audience scores (0-100, slightly higher mean)
    - IMDB ratings (5-9.5, scaled appropriately)
    - Buzz scores (social media/cultural impact proxy)
    - Correlations between metrics to reflect real relationships
    
    #### Data Generation Process
    
    1. **Title Metadata**: Random sampling with realistic distributions
    2. **Quality Scores**: Correlated random generation with brand/genre effects
    3. **Engagement Curves**: Parametric model (peak + exponential decay)
    4. **Financial Mapping**: Business logic to convert hours → value
    
    This approach allows demonstration of analytical methods while acknowledging 
    data limitations.
    """)

with st.expander("### 2. Engagement Modeling", expanded=False):
    st.markdown("""
    #### Engagement Curve Model
    
    We model weekly engagement using a **peak + exponential decay** pattern:
    
    ```
    For t < peak_week:
        hours(t) = linear ramp-up to peak
    
    For t >= peak_week:
        hours(t) = peak_hours × exp(-decay_rate × (t - peak_week))
    ```
    
    **Parameters**:
    - `peak_week`: Determined by content type (films peak week 1-2, series vary)
    - `peak_hours`: Function of budget, quality, brand, and genre
    - `decay_rate`: Steeper for buzz-driven content, gentler for quality content
    
    **Model Fit (R²)**:
    - We fit exponential decay to post-peak actual data
    - R² measures how well the simple model explains observed patterns
    - High R² = predictable decay, Low R² = irregular patterns
    
    #### Why This Model?
    
    - **Simplicity**: Parsimonious 3-parameter model
    - **Interpretability**: Parameters have clear business meaning
    - **Empirical Support**: Matches observed streaming patterns
    - **Predictive**: Useful for forecasting library value
    
    #### Limitations
    
    - Doesn't capture marketing spikes or external events
    - Assumes smooth decay (reality is noisier)
    - Single-curve fit may miss multi-modal patterns
    """)

with st.expander("### 3. Financial Mapping: Hours → Value", expanded=False):
    st.markdown("""
    #### Economic Model
    
    We translate engagement (hours viewed) into financial value through multiple channels:
    
    **1. Subscriber Acquisition Value**
    
    ```
    New Subs = (Hours / 1M) × Base Conversion × Quality × Brand × Type
    Acquisition Value = New Subs × ARPU × Avg Lifetime (18 months)
    ```
    
    - High-quality, marquee content drives disproportionate acquisition
    - Films drive more acquisition than series
    
    **2. Subscriber Retention Value**
    
    ```
    Retained Sub-Months = (Hours / 1M) × Base Retention × Quality × Type
    Retention Value = Retained Sub-Months × ARPU
    ```
    
    - Satisfying content reduces churn
    - Series have stronger retention impact (ongoing engagement)
    
    **3. Advertising Revenue (Hulu)**
    
    ```
    Ad Revenue = Hours × Ad Tier % × ARPU per Hour
    ```
    
    - Assume 30% of Hulu viewers on ad-supported tier
    - ~$0.05 per hour ad revenue
    
    **4. Theatrical Revenue (Films)**
    
    ```
    Box Office = Budget × Multiplier × Quality Factor × Brand Multiplier
    ```
    
    - Multiplier: 2.5-3.5x budget by tier
    - Quality and brand significantly impact performance
    
    **5. PVOD Revenue (Films)**
    
    ```
    PVOD = Theatrical × 15% × Window Factor × Quality Factor
    ```
    
    - Window factor: Shorter streaming windows cannibalize PVOD
    
    #### Key Assumptions
    
    - **Disney+ ARPU**: $7.99/month
    - **Hulu ARPU**: $12.99/month
    - **Avg Subscriber Lifetime**: 18 months
    - **Discount Rate**: 10% annually
    
    #### Value Components
    
    Total Value = Acquisition + Retention + Ads + Theatrical + PVOD + Licensing
    
    ROI = (Total Value - Total Cost) / Total Cost
    """)

with st.expander("### 4. Windowing & Deal Valuation", expanded=False):
    st.markdown("""
    #### Windowing Strategy Model
    
    **Release windows** sequentially maximize revenue across channels while managing 
    cannibalization effects.
    
    #### Window Sequence
    
    1. **Theatrical** (0-90 days): Exclusive theatrical, drives box office
    2. **PVOD** (45-90 days): Premium home viewing ($20-30), bridges to streaming
    3. **Streaming** (45-180 days): Disney+/Hulu exclusive, drives subs
    4. **Licensing** (optional, 1-3 years): Third-party deals for upfront cash
    
    #### Cannibalization Model
    
    **PVOD ← Streaming**:
    - Streaming < 45 days: PVOD reduced 30%
    - Streaming 45-75 days: PVOD reduced 15%
    - Streaming > 75 days: No impact
    
    **Streaming ← Licensing**:
    - Third-party license reduces exclusive streaming value by 25%
    
    **Engagement ← Window Length**:
    - Longer windows risk engagement decay
    - Modeled as streaming value multiplier (0.85 - 1.0) by offset
    
    #### NPV Calculation
    
    All cashflows discounted to present value:
    
    ```
    NPV = Σ (CF_t / (1 + r)^t)
    ```
    
    - `r` = 10% annual discount rate → 0.19% weekly rate
    - Earlier revenue worth more than later revenue
    - Guides optimal window timing
    
    #### Cash Flow Modeling
    
    Period-by-period cashflows for each window:
    - Theatrical: Spread over 12 weeks
    - PVOD: Spread over window duration
    - Streaming: 104 weeks with exponential decay
    - Licensing: Lump sum at license date
    
    #### Trade-offs
    
    - **Short windows**: Maximize streaming value, risk PVOD/theatrical
    - **Long windows**: Maximize PVOD/theatrical, risk engagement decay
    - **Licensing**: Immediate cash, reduces long-term exclusive value
    """)

with st.expander("### 5. Greenlight & Comparable Title Analysis", expanded=False):
    st.markdown("""
    #### Forecasting Methodology
    
    New title forecasts use **comparable title analysis** - the most reliable 
    predictor of performance for similar content.
    
    #### Step 1: Find Comparables
    
    **Similarity Scoring**:
    ```
    Score = 0
    + 5 if brand matches
    + 4 if genre matches
    + 3 if content type matches
    + 3 if budget tier matches (±1 tier = +1)
    + 2 × (min(hours) / max(hours))  # Scale similarity
    ```
    
    Select top 5 by similarity score.
    
    #### Step 2: Build Distribution
    
    For each metric (hours, value, ROI):
    - Compute mean (μ) and standard deviation (σ) across comps
    - These form the baseline distribution
    
    #### Step 3: Generate Scenarios
    
    **Base Case**:
    ```
    Base = μ × Concept_Multiplier
    
    Concept_Multiplier = (Star_Factor + Buzz_Factor) / 2
    Star_Factor = 0.8 + (star_power / 5) × 0.4
    Buzz_Factor = 0.8 + (buzz / 100) × 0.4
    ```
    
    **Bear Case**:
    ```
    Bear = (μ - σ) × Concept_Multiplier × 0.7
    ```
    
    **Bull Case**:
    ```
    Bull = (μ + σ) × Concept_Multiplier × 1.3
    ```
    
    #### Step 4: Compute ROI
    
    ```
    ROI = (Projected_Value - Actual_Budget) / Actual_Budget
    ```
    
    Use actual proposed budget, not comp average.
    
    #### Step 5: Generate Recommendation
    
    **Decision Rules**:
    - Base > 100% ROI + Bear > 30% → **STRONG GREENLIGHT**
    - Base > 50% ROI + Bear > 0% → **GREENLIGHT**
    - Base > 20% ROI → **CONDITIONAL**
    - Base > 0% ROI → **MARGINAL**
    - Base ≤ 0% ROI → **PASS**
    
    Additional factors: IP familiarity, star power, buzz potential, comp quality.
    
    #### Why This Works
    
    - **Empirical**: Based on actual historical performance
    - **Peer-anchored**: Similar titles are best predictors
    - **Risk-adjusted**: Bear/base/bull captures uncertainty
    - **Concept-specific**: Adjusts for unique attributes
    
    #### Limitations
    
    - Dependent on comp quality and relevance
    - Assumes execution comparable to comps
    - Doesn't capture breakthrough potential of truly novel concepts
    - Should be one input among many strategic considerations
    """)

st.markdown("---")

# Example Visualizations
st.markdown("## 📊 Example Analytics from the Platform")

col1, col2 = st.columns(2)

# Get a sample title for demonstration
sample_title_id = df_scorecards.sort_values("total_value", ascending=False).iloc[0]["title_id"]
sample_scorecard = compute_title_scorecard(
    title_id=sample_title_id,
    df_titles=df_titles,
    df_engagement=df_engagement,
    df_quality=df_quality
)
sample_engagement = df_engagement[df_engagement["title_id"] == sample_title_id]

with col1:
    st.markdown("### Example: Engagement Curve with Model Fit")
    
    predicted_curve, r_squared = fit_engagement_curve_model(sample_engagement)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sample_engagement["week_number"],
        y=sample_engagement["proxy_hours_viewed"] / 1_000_000,
        mode='markers',
        name='Actual',
        marker=dict(size=8, color='#1f77b4')
    ))
    
    if not predicted_curve.empty:
        fig.add_trace(go.Scatter(
            x=predicted_curve.index,
            y=predicted_curve.values / 1_000_000,
            mode='lines',
            name='Fitted Model',
            line=dict(color='#ff7f0e', width=3, dash='dash')
        ))
    
    fig.update_layout(
        title=f"{sample_scorecard.title_name}<br>Model Fit R² = {r_squared:.3f}",
        xaxis_title="Week",
        yaxis_title="Hours (M)",
        height=350,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Example: Portfolio Risk/Return")
    
    risk_return_data = compute_title_risk_return_data(df_scorecards, df_titles)
    
    if not risk_return_data.empty:
        # Sample subset for cleaner viz
        sample_data = risk_return_data.sample(min(30, len(risk_return_data)))
        
        fig = px.scatter(
            sample_data,
            x="risk_metric",
            y="roi",
            size="total_value",
            color="brand",
            hover_name="title_name",
            labels={"risk_metric": "Risk", "roi": "ROI"}
        )
        
        fig.update_layout(
            title="Title-Level Risk vs Return",
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Case Study
st.markdown("## 🎯 Case Study: End-to-End Content Decision")

st.markdown("""
This case study demonstrates how to use Magic Slate tools for a complete 
content planning & analysis workflow, from evaluating existing titles to 
greenlighting new concepts.
""")

case_study_tabs = st.tabs([
    "1️⃣ Title Performance", 
    "2️⃣ Portfolio Context", 
    "3️⃣ Windowing Strategy", 
    "4️⃣ Greenlight Decision"
])

# Select a high-value title for case study
case_title_id = df_scorecards.sort_values("total_value", ascending=False).iloc[2]["title_id"]
case_scorecard = compute_title_scorecard(
    title_id=case_title_id,
    df_titles=df_titles,
    df_engagement=df_engagement,
    df_quality=df_quality
)
case_title = df_titles[df_titles["title_id"] == case_title_id].iloc[0]

with case_study_tabs[0]:
    st.markdown(f"### Scenario: Evaluating '{case_scorecard.title_name}'")
    
    st.markdown(f"""
    **Context**: We want to understand the performance of **{case_scorecard.title_name}**, 
    a {case_title['brand']} {case_title['genre']} {case_title['content_type']}, 
    and its implications for future content strategy.
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Hours", f"{case_scorecard.total_hours_viewed/1_000_000:.1f}M")
    with col2:
        st.metric("Total Value", f"${case_scorecard.total_value/1_000_000:.1f}M")
    with col3:
        st.metric("Total Cost", f"${case_scorecard.total_cost/1_000_000:.1f}M")
    with col4:
        st.metric("ROI", f"{case_scorecard.roi*100:.0f}%")
    
    # Advanced metrics
    case_engagement = df_engagement[df_engagement["title_id"] == case_title_id]
    adv_metrics = compute_advanced_engagement_metrics(
        case_engagement, 
        case_scorecard.total_value,
        case_scorecard.total_cost
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Peak-to-Week-4 Decay", f"{adv_metrics['peak_to_week4_decay']*100:.1f}%")
    with col2:
        st.metric("Incremental Subs", f"{adv_metrics['estimated_incremental_subs']/1000:.1f}K")
    with col3:
        st.metric("Streaming LTV", f"${adv_metrics['estimated_ltv_contribution']/1_000_000:.1f}M")
    
    st.markdown("#### Analysis")
    
    if case_scorecard.roi > 0.8:
        roi_assessment = "exceptional"
    elif case_scorecard.roi > 0.5:
        roi_assessment = "strong"
    elif case_scorecard.roi > 0.2:
        roi_assessment = "modest"
    else:
        roi_assessment = "challenged"
    
    st.markdown(f"""
    **Key Findings**:
    - This title delivered **{roi_assessment} ROI of {case_scorecard.roi*100:.0f}%**
    - Peak-to-week-4 decay of {adv_metrics['peak_to_week4_decay']*100:.0f}% suggests 
      {'sustained engagement' if adv_metrics['peak_to_week4_decay'] < 0.5 else 'front-loaded performance'}
    - Estimated to drive ~{adv_metrics['estimated_incremental_subs']/1000:.0f}K new subscribers
    - Long-tail share of {case_scorecard.long_tail_share*100:.0f}% indicates 
      {'strong' if case_scorecard.long_tail_share > 0.4 else 'moderate'} library value
    
    **Implication**: {'Continue investing in similar content' if case_scorecard.roi > 0.5 else 'Review strategy for this type of content'}
    """)

with case_study_tabs[1]:
    st.markdown("### Portfolio Context: How Does This Title Fit?")
    
    st.markdown(f"""
    Understanding **{case_scorecard.title_name}** in the context of the broader portfolio.
    """)
    
    # Find comps
    comps = find_comparable_titles_for_title(
        title_id=case_title_id,
        df_titles=df_titles,
        df_scorecards=df_scorecards,
        top_n=5
    )
    
    if not comps.empty:
        comp_median_roi = comps["roi"].median()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Comparable Titles")
            
            display_comps = comps[["title_name", "brand", "genre", "roi"]].copy()
            display_comps["roi"] = display_comps["roi"].apply(lambda x: f"{x*100:.0f}%")
            display_comps.columns = ["Title", "Brand", "Genre", "ROI"]
            
            st.dataframe(display_comps, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### Performance vs Comps")
            
            st.metric("This Title ROI", f"{case_scorecard.roi*100:.0f}%")
            st.metric("Comp Median ROI", f"{comp_median_roi*100:.0f}%")
            
            delta = (case_scorecard.roi - comp_median_roi) * 100
            if delta > 10:
                st.success(f"✅ Outperforming comps by {delta:.0f}pp")
            elif delta > -10:
                st.info(f"➖ In line with comps ({delta:+.0f}pp)")
            else:
                st.warning(f"⚠️ Underperforming comps by {abs(delta):.0f}pp")
    
    # Portfolio share
    portfolio_summary = compute_portfolio_summary(df_scorecards)
    title_value_share = case_scorecard.total_value / portfolio_summary['total_value']
    
    st.markdown("#### Portfolio Contribution")
    st.markdown(f"""
    - **Value Share**: {title_value_share*100:.1f}% of total portfolio value
    - **Brand**: {case_title['brand']} - a {'high' if case_title['brand'] in ['Marvel', 'Star Wars', 'Pixar'] else 'core'} priority brand
    - **Classification**: {case_scorecard.classification}
    
    **Strategic Role**: {'Tentpole franchise asset' if case_scorecard.classification == 'Tentpole' else 'Solid portfolio contributor' if case_scorecard.classification in ['Workhorse', 'Acceptable'] else 'Niche/specialized content'}
    """)

with case_study_tabs[2]:
    st.markdown("### Windowing Strategy: Optimizing Value Capture")
    
    st.markdown(f"""
    **Question**: If we were releasing **{case_scorecard.title_name}** today, 
    what windowing strategy would maximize NPV?
    """)
    
    # Simulate windowing scenarios (only if film)
    if case_title['content_type'] == "Film":
        scenarios = [
            WindowingScenario(
                scenario_name="Traditional (90-day)",
                title_id=case_title_id,
                theatrical_window_days=90,
                pvod_window_days=45,
                disney_plus_offset_days=90,
                hulu_offset_days=90,
                third_party_license_start_days=0,
                third_party_license_fee=0,
            ),
            WindowingScenario(
                scenario_name="Short Window (45-day)",
                title_id=case_title_id,
                theatrical_window_days=45,
                pvod_window_days=30,
                disney_plus_offset_days=45,
                hulu_offset_days=45,
                third_party_license_start_days=0,
                third_party_license_fee=0,
            ),
            WindowingScenario(
                scenario_name="Streaming-First",
                title_id=case_title_id,
                theatrical_window_days=0,
                pvod_window_days=0,
                disney_plus_offset_days=0,
                hulu_offset_days=0,
                third_party_license_start_days=0,
                third_party_license_fee=0,
            ),
        ]
        
        with st.spinner("Simulating windowing scenarios..."):
            results = simulate_windowing_scenarios(
                title_id=case_title_id,
                scenarios=scenarios,
                df_titles=df_titles,
                df_engagement=df_engagement,
                df_quality=df_quality
            )
        
        # Display results
        fig = go.Figure(data=[
            go.Bar(
                x=results['scenario_name'],
                y=results['total_npv'] / 1_000_000,
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                text=results['total_npv'].apply(lambda x: f"${x/1_000_000:.1f}M"),
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="NPV by Windowing Strategy",
            xaxis_title="Strategy",
            yaxis_title="NPV ($M)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        best_scenario = results.loc[results['total_npv'].idxmax()]
        
        st.markdown("#### Recommendation")
        st.success(f"""
        **Best Strategy**: {best_scenario['scenario_name']} with NPV of ${best_scenario['total_npv']/1_000_000:.1f}M
        
        This strategy balances:
        - Theatrical revenue capture
        - PVOD window optimization
        - Streaming value timing
        - Time value of money (NPV discount)
        """)
    else:
        st.info("Windowing analysis most relevant for films. This is a series.")

with case_study_tabs[3]:
    st.markdown("### Greenlight Decision: Similar New Concept")
    
    st.markdown(f"""
    **Question**: Should we greenlight a similar concept to **{case_scorecard.title_name}**?
    
    Let's forecast a hypothetical new {case_title['brand']} {case_title['genre']} project.
    """)
    
    # Create hypothetical concept
    new_concept = NewTitleConcept(
        concept_name=f"New {case_title['brand']} {case_title['genre']} Project",
        brand=case_title['brand'],
        genre=case_title['genre'],
        content_type=case_title['content_type'],
        production_budget_estimate=case_title['estimated_production_budget'],
        marketing_spend_estimate=case_title['estimated_marketing_spend'],
        ip_familiarity="Sequel" if case_title['brand'] in ['Marvel', 'Star Wars'] else "New IP",
        star_power_score=3,
        buzz_potential_score=60,
    )
    
    with st.spinner("Generating forecast..."):
        forecast = forecast_new_title(
            concept=new_concept,
            df_titles=df_titles,
            df_engagement=df_engagement,
            df_quality=df_quality
        )
    
    scenarios = forecast['scenarios']
    
    if scenarios:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Bear Case")
            st.metric("ROI", f"{scenarios['bear']['roi']*100:.0f}%")
            st.metric("Value", f"${scenarios['bear']['total_value']/1_000_000:.1f}M")
        
        with col2:
            st.markdown("#### Base Case")
            st.metric("ROI", f"{scenarios['base']['roi']*100:.0f}%")
            st.metric("Value", f"${scenarios['base']['total_value']/1_000_000:.1f}M")
        
        with col3:
            st.markdown("#### Bull Case")
            st.metric("ROI", f"{scenarios['bull']['roi']*100:.0f}%")
            st.metric("Value", f"${scenarios['bull']['total_value']/1_000_000:.1f}M")
        
        st.markdown("#### Recommendation")
        
        base_roi = scenarios['base']['roi']
        bear_roi = scenarios['bear']['roi']
        
        if base_roi > 1.0 and bear_roi > 0.3:
            recommendation = "**STRONG GREENLIGHT** ✅"
            rationale = "Excellent base case with limited downside risk"
        elif base_roi > 0.5 and bear_roi > 0:
            recommendation = "**GREENLIGHT** ✅"
            rationale = "Solid returns with manageable risk"
        elif base_roi > 0.2:
            recommendation = "**CONDITIONAL** ⚠️"
            rationale = "Moderate returns; review budget and creative approach"
        else:
            recommendation = "**PASS** or **REVISE** ❌"
            rationale = "Returns insufficient at current budget"
        
        st.success(f"""
        {recommendation}
        
        **Rationale**: {rationale}
        
        - Base-case ROI: {base_roi*100:.0f}%
        - Downside ROI: {bear_roi*100:.0f}%
        - Based on {len(forecast['comps'])} comparable titles
        """)

st.markdown("---")

# Closing
st.markdown("""
## 🎓 Key Takeaways

This platform demonstrates:

1. **Advanced Analytics**: Moving beyond raw metrics to modeled insights (curve fitting, 
   comp analysis, NPV optimization)

2. **Decision Support**: Translating data into actionable recommendations (greenlight, 
   windowing, portfolio strategy)

3. **End-to-End Workflow**: From title performance → portfolio strategy → new concept 
   evaluation → deal structuring

4. **Technical Rigor**: Proper statistical methods, financial modeling, and transparent 
   assumptions

5. **Business Communication**: Translating complex analysis into clear narratives for 
   stakeholders

---

**For a Content Planning & Analysis role**, these capabilities map directly to:
- **Title Performance & KPIs**: Deep-dive analytics on individual titles
- **Portfolio Strategy**: Brand/genre/platform optimization and concentration analysis
- **Windowing & Deal Valuation**: Modeling distribution strategies and NPV
- **Greenlight & Forecasting**: Comp-based forecasting and investment recommendations

**Contact**: This project demonstrates readiness to contribute to data-driven content 
strategy at Disney+, leveraging analytical depth with strategic business acumen.
""")
