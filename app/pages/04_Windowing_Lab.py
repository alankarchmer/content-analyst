"""Windowing Lab page for Magic Slate."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from magicslate.windowing_simulator import (
    simulate_windowing_scenarios,
    create_default_windowing_scenarios,
    compare_scenarios,
)
from magicslate.data_models import WindowingScenario

st.set_page_config(page_title="Windowing Lab - Magic Slate", page_icon="🎞️", layout="wide")

st.title("🎞️ Windowing Lab")
st.markdown("Simulate release window strategies and analyze their financial impact")

# Get data from session state
df_titles = st.session_state.df_titles
df_engagement = st.session_state.df_engagement
df_quality = st.session_state.df_quality
df_scorecards = st.session_state.df_scorecards

st.markdown("""
The Windowing Lab allows you to model different release strategies for titles and 
understand how theatrical, PVOD, streaming, and licensing windows interact to 
maximize total value.
""")

st.markdown("---")

# Title selection
st.markdown("## 🎬 Select a Title")

# Filter to films for more interesting windowing scenarios
films_only = st.checkbox("Show films only (recommended)", value=True)

if films_only:
    available_titles = df_titles[df_titles["content_type"] == "Film"]
else:
    available_titles = df_titles.copy()

# Merge with scorecards for display
available_titles = available_titles.merge(
    df_scorecards[["title_id", "total_value"]],
    on="title_id",
    how="left"
)
available_titles = available_titles.sort_values("total_value", ascending=False)

title_options = [f"{row['title_name']} ({row['brand']}, {row['content_type']})" 
                for _, row in available_titles.iterrows()]
title_ids = available_titles["title_id"].tolist()

if len(title_ids) == 0:
    st.error("No titles available. Please uncheck 'Show films only'.")
    st.stop()

selected_title_idx = st.selectbox(
    "Choose a title",
    range(len(title_options)),
    format_func=lambda x: title_options[x]
)

selected_title_id = title_ids[selected_title_idx]
selected_title = available_titles[available_titles["title_id"] == selected_title_id].iloc[0]

st.markdown(f"**Selected:** {selected_title['title_name']} - {selected_title['brand']}")

st.markdown("---")

# Scenario configuration
st.markdown("## ⚙️ Configure Windowing Scenarios")

st.markdown("Define 2-3 different windowing strategies to compare:")

# Use tabs for scenario configuration
scenario_tabs = st.tabs(["Scenario 1", "Scenario 2", "Scenario 3"])

scenarios = []

for idx, tab in enumerate(scenario_tabs):
    with tab:
        col1, col2 = st.columns(2)
        
        with col1:
            scenario_name = st.text_input(
                "Scenario Name",
                value=f"Scenario {idx+1}",
                key=f"name_{idx}"
            )
            
            theatrical_days = st.number_input(
                "Theatrical Window (days)",
                min_value=0,
                max_value=180,
                value=90 if idx == 0 else (45 if idx == 1 else 0),
                step=15,
                key=f"theatrical_{idx}",
                help="Exclusive theatrical period before other windows"
            )
            
            pvod_days = st.number_input(
                "PVOD Window (days)",
                min_value=0,
                max_value=90,
                value=45 if idx == 0 else (30 if idx == 1 else 0),
                step=15,
                key=f"pvod_{idx}",
                help="Premium VOD window duration"
            )
        
        with col2:
            disney_plus_offset = st.number_input(
                "Disney+ Release Offset (days)",
                min_value=0,
                max_value=365,
                value=90 if idx == 0 else (45 if idx == 1 else 0),
                step=15,
                key=f"disney_{idx}",
                help="Days after theatrical release"
            )
            
            hulu_offset = st.number_input(
                "Hulu Release Offset (days)",
                min_value=0,
                max_value=365,
                value=90 if idx == 0 else (45 if idx == 1 else 0),
                step=15,
                key=f"hulu_{idx}",
                help="Days after theatrical release"
            )
            
            license_start = st.number_input(
                "Third-Party License Start (days)",
                min_value=0,
                max_value=1095,
                value=0 if idx < 2 else 730,
                step=365,
                key=f"license_start_{idx}",
                help="Days until licensing to third party (0 = no license)"
            )
            
            license_fee = st.number_input(
                "License Fee ($M)",
                min_value=0.0,
                max_value=200.0,
                value=0.0 if idx < 2 else 50.0,
                step=10.0,
                key=f"license_fee_{idx}",
                help="License fee in millions"
            )
        
        scenario = WindowingScenario(
            scenario_name=scenario_name,
            title_id=selected_title_id,
            theatrical_window_days=theatrical_days,
            pvod_window_days=pvod_days,
            disney_plus_offset_days=disney_plus_offset,
            hulu_offset_days=hulu_offset,
            third_party_license_start_days=license_start,
            third_party_license_fee=license_fee * 1_000_000,  # Convert to dollars
        )
        
        scenarios.append(scenario)

# Run simulation button
if st.button("🚀 Run Windowing Simulation", type="primary"):
    with st.spinner("Simulating scenarios..."):
        results_df = simulate_windowing_scenarios(
            title_id=selected_title_id,
            scenarios=scenarios,
            df_titles=df_titles,
            df_engagement=df_engagement,
            df_quality=df_quality
        )
        
        st.session_state.windowing_results = results_df
        st.session_state.windowing_scenarios = scenarios

# Display results
if "windowing_results" in st.session_state and st.session_state.windowing_results is not None:
    st.markdown("---")
    st.markdown("## 📊 Simulation Results")
    
    results_df = st.session_state.windowing_results
    
    # NPV comparison
    st.markdown("### 💰 NPV Comparison")
    
    fig = go.Figure(data=[
        go.Bar(
            x=results_df['scenario_name'],
            y=results_df['total_npv'] / 1_000_000,
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(results_df)],
            text=results_df['total_npv'].apply(lambda x: f"${x/1_000_000:.1f}M"),
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Net Present Value by Scenario",
        xaxis_title="Scenario",
        yaxis_title="NPV ($ Millions)",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Best scenario
    best_scenario = results_df.loc[results_df['total_npv'].idxmax()]
    st.success(f"✅ **Best Scenario:** {best_scenario['scenario_name']} with NPV of ${best_scenario['total_npv']/1_000_000:.1f}M")
    
    st.markdown("---")
    
    # Value breakdown
    st.markdown("### 📈 Value Breakdown by Scenario")
    
    # Stacked bar chart
    fig = go.Figure()
    
    if results_df['theatrical_value'].sum() > 0:
        fig.add_trace(go.Bar(
            name='Theatrical',
            x=results_df['scenario_name'],
            y=results_df['theatrical_value'] / 1_000_000,
            marker_color='#1f77b4'
        ))
    
    if results_df['pvod_value'].sum() > 0:
        fig.add_trace(go.Bar(
            name='PVOD',
            x=results_df['scenario_name'],
            y=results_df['pvod_value'] / 1_000_000,
            marker_color='#ff7f0e'
        ))
    
    fig.add_trace(go.Bar(
        name='Streaming',
        x=results_df['scenario_name'],
        y=results_df['streaming_value'] / 1_000_000,
        marker_color='#2ca02c'
    ))
    
    if results_df['ad_value'].sum() > 0:
        fig.add_trace(go.Bar(
            name='Ad Revenue',
            x=results_df['scenario_name'],
            y=results_df['ad_value'] / 1_000_000,
            marker_color='#d62728'
        ))
    
    if results_df['license_value'].sum() > 0:
        fig.add_trace(go.Bar(
            name='Licensing',
            x=results_df['scenario_name'],
            y=results_df['license_value'] / 1_000_000,
            marker_color='#9467bd'
        ))
    
    fig.update_layout(
        barmode='stack',
        title="Value Components by Scenario",
        xaxis_title="Scenario",
        yaxis_title="Value ($ Millions)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed results table
    st.markdown("### 📋 Detailed Results")
    
    display_df = results_df.copy()
    
    # Format currency columns
    currency_cols = ['theatrical_value', 'pvod_value', 'streaming_value', 
                     'ad_value', 'license_value', 'total_value', 'total_npv']
    
    for col in currency_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${x/1_000_000:.2f}M")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Narrative insights
    st.markdown("### 💡 Key Insights")
    
    narrative = compare_scenarios(results_df)
    st.markdown(narrative)

else:
    st.info("👆 Configure scenarios above and click 'Run Windowing Simulation' to see results.")

st.markdown("---")

# Educational content
with st.expander("📚 Learn About Windowing Strategies"):
    st.markdown("""
    ### What is Windowing?
    
    **Windowing** refers to the strategic sequencing of a title's release across 
    different distribution channels to maximize total revenue.
    
    ### Common Windows:
    
    1. **Theatrical Window**: Exclusive theatrical release (typically 45-90 days)
       - Drives box office revenue
       - Builds buzz and awareness
       - Premium pricing
    
    2. **PVOD Window**: Premium Video On Demand (typically 17-45 days)
       - Early home viewing at premium price ($19.99-$29.99)
       - Captures audiences who won't/can't go to theaters
       - Bridges theatrical and streaming
    
    3. **Streaming Window**: Release on Disney+/Hulu
       - Drives subscriber acquisition and retention
       - Provides long-term value
       - May cannibalize earlier windows if too short
    
    4. **Third-Party Licensing**: License to other platforms
       - Provides upfront cash
       - Can cannibalize long-term streaming value
       - Strategic for library titles
    
    ### Key Trade-offs:
    
    - **Shorter windows** → Faster streaming access → Higher streaming value but lower theatrical/PVOD
    - **Longer windows** → More theatrical/PVOD revenue → Potential engagement decay by streaming release
    - **Licensing** → Immediate cash → Reduced exclusive streaming value
    
    ### NPV Considerations:
    
    All cashflows are discounted to present value using a 10% annual discount rate. 
    Earlier revenue is worth more than later revenue.
    """)
