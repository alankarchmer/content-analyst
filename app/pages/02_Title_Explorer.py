"""Title Explorer page for Magic Slate - Enhanced with advanced analytics."""

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

st.set_page_config(page_title="Title Explorer - Magic Slate", page_icon="🎬", layout="wide")

st.title("🎬 Title Performance & KPIs")
st.markdown("Deep dive into individual title performance with advanced analytics")

# Get data from session state
df_titles = st.session_state.df_titles
df_engagement = st.session_state.df_engagement
df_quality = st.session_state.df_quality
df_scorecards = st.session_state.df_scorecards

# Title selection
st.markdown("## Select a Title")

col1, col2, col3 = st.columns(3)

with col1:
    selected_brand = st.selectbox(
        "Filter by Brand",
        ["All"] + sorted(df_titles["brand"].unique().tolist())
    )

with col2:
    selected_genre = st.selectbox(
        "Filter by Genre",
        ["All"] + sorted(df_titles["genre"].unique().tolist())
    )

with col3:
    selected_platform = st.selectbox(
        "Filter by Platform",
        ["All"] + sorted(df_titles["platform_primary"].unique().tolist())
    )

# Filter titles
filtered_titles = df_titles.copy()

if selected_brand != "All":
    filtered_titles = filtered_titles[filtered_titles["brand"] == selected_brand]

if selected_genre != "All":
    filtered_titles = filtered_titles[filtered_titles["genre"] == selected_genre]

if selected_platform != "All":
    filtered_titles = filtered_titles[filtered_titles["platform_primary"] == selected_platform]

# Merge with scorecards for sorting
filtered_titles = filtered_titles.merge(
    df_scorecards[["title_id", "total_value", "roi"]],
    on="title_id",
    how="left"
)

# Sort by value
filtered_titles = filtered_titles.sort_values("total_value", ascending=False)

# Title dropdown
title_options = [f"{row['title_name']} ({row['brand']})" 
                for _, row in filtered_titles.iterrows()]
title_ids = filtered_titles["title_id"].tolist()

selected_title_idx = st.selectbox(
    f"Choose from {len(filtered_titles)} titles",
    range(len(title_options)),
    format_func=lambda x: title_options[x]
)

selected_title_id = title_ids[selected_title_idx]

# Compute scorecard
scorecard = compute_title_scorecard(
    title_id=selected_title_id,
    df_titles=df_titles,
    df_engagement=df_engagement,
    df_quality=df_quality
)

# Compute advanced metrics
title_engagement = df_engagement[df_engagement["title_id"] == selected_title_id].copy()
advanced_metrics = compute_advanced_engagement_metrics(
    df_engagement=title_engagement,
    total_value=scorecard.total_value,
    total_cost=scorecard.total_cost
)

# Fit engagement model
predicted_curve, r_squared = fit_engagement_curve_model(title_engagement)

st.markdown("---")

# Title header
st.markdown(f"## {scorecard.title_name}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"**Brand:** {scorecard.brand}")
    st.markdown(f"**Genre:** {scorecard.genre}")

with col2:
    st.markdown(f"**Platform:** {scorecard.platform_primary}")
    st.markdown(f"**Type:** {scorecard.content_type}")

with col3:
    # Classification badge
    classification_colors = {
        "Tentpole": "#ffd700",
        "Workhorse": "#4CAF50",
        "Niche Gem": "#2196F3",
        "Underperformer": "#f44336",
        "Acceptable": "#9E9E9E",
        "Marginal": "#FF9800"
    }
    color = classification_colors.get(scorecard.classification, "#9E9E9E")
    st.markdown(f"**Classification:**")
    st.markdown(f'<span style="background-color: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-weight: bold;">{scorecard.classification}</span>', 
                unsafe_allow_html=True)

with col4:
    st.metric("ROI", f"{scorecard.roi*100:.0f}%")

st.markdown("---")

# Executive KPIs
st.markdown("### 📊 Executive KPIs")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Hours", f"{scorecard.total_hours_viewed/1_000_000:.1f}M")

with col2:
    st.metric("Peak Hours", f"{scorecard.peak_hours/1_000_000:.1f}M")
    st.caption(f"Week {scorecard.peak_week}")

with col3:
    st.metric("Total Value", f"${scorecard.total_value/1_000_000:.1f}M")

with col4:
    st.metric("Total Cost", f"${scorecard.total_cost/1_000_000:.1f}M")

with col5:
    st.metric("Cost per Hour", f"${scorecard.cost_per_hour_viewed:.2f}")

st.markdown("---")

# Advanced Analytics Panel
st.markdown("### 🔬 Advanced Analytics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Peak-to-Week-4 Decay",
        f"{advanced_metrics['peak_to_week4_decay']*100:.1f}%",
        help="Percentage drop from peak hours to week 4"
    )

with col2:
    st.metric(
        "Incremental Subscribers",
        f"{advanced_metrics['estimated_incremental_subs']/1000:.1f}K",
        help="Estimated new subscribers acquired by this title"
    )

with col3:
    st.metric(
        "Retained Sub-Months",
        f"{advanced_metrics['estimated_retained_sub_months']/1000:.1f}K",
        help="Estimated subscriber-months retained"
    )

with col4:
    st.metric(
        "Streaming LTV",
        f"${advanced_metrics['estimated_ltv_contribution']/1_000_000:.1f}M",
        help="Estimated lifetime value contribution from streaming"
    )

# Add model ROI metric
col1, col2, col3, col4 = st.columns(4)

with col1:
    modeled_roi = scorecard.roi * 100
    st.metric("Modeled ROI", f"{modeled_roi:.0f}%")

with col2:
    st.metric("Long Tail Share", f"{scorecard.long_tail_share*100:.0f}%")
    st.caption("Hours after week 4")

with col3:
    weeks_above = (title_engagement["proxy_hours_viewed"] > scorecard.peak_hours * 0.1).sum()
    st.metric("Weeks Above 10%", weeks_above)
    st.caption("Of peak performance")

with col4:
    st.metric("Decay Rate", f"{scorecard.decay_rate:.3f}")
    st.caption("Exponential decay parameter")

st.markdown("---")

# Engagement curve with model fit
st.markdown("### 📈 Engagement Curve & Model Fit")

fig = go.Figure()

# Actual data
fig.add_trace(go.Scatter(
    x=title_engagement["week_number"],
    y=title_engagement["proxy_hours_viewed"] / 1_000_000,
    mode='markers',
    name='Actual',
    marker=dict(size=8, color='#1f77b4'),
))

# Fitted model
if not predicted_curve.empty:
    fig.add_trace(go.Scatter(
        x=predicted_curve.index,
        y=predicted_curve.values / 1_000_000,
        mode='lines',
        name='Fitted Model',
        line=dict(color='#ff7f0e', width=3, dash='dash'),
    ))

fig.update_layout(
    title=f"Weekly Hours Viewed Over Time (Model fit R² = {r_squared:.3f})",
    xaxis_title="Week Number",
    yaxis_title="Hours Viewed (Millions)",
    height=400,
    hovermode='x unified',
    legend=dict(x=0.7, y=0.95)
)

st.plotly_chart(fig, use_container_width=True)

# Model details expander
with st.expander("📘 Model Details: Engagement Curve Fitting"):
    st.markdown("""
    **Engagement Model**: Exponential decay post-peak
    
    The fitted model assumes engagement follows a pattern:
    - **Pre-peak**: Ramp-up period (linear interpolation)
    - **Post-peak**: Exponential decay: `hours(t) = peak × exp(-decay_rate × (t - peak_week))`
    
    **Model Fit (R²)**: Indicates how well the exponential model explains actual engagement.
    - **R² > 0.80**: Excellent fit, highly predictable engagement pattern
    - **R² 0.60-0.80**: Good fit, typical decay behavior
    - **R² < 0.60**: Unusual engagement pattern (may indicate external factors)
    
    **Interpretation**:
    - High R² with high decay = front-loaded engagement (buzz-driven)
    - High R² with low decay = sustained engagement (quality-driven)
    - Low R² = unpredictable pattern (marketing spikes, word-of-mouth)
    """)

st.markdown("---")

# Comparable Titles Section
st.markdown("### 🎯 Comparable Titles Analysis")

comps = find_comparable_titles_for_title(
    title_id=selected_title_id,
    df_titles=df_titles,
    df_scorecards=df_scorecards,
    top_n=5
)

if not comps.empty:
    st.markdown(f"Based on brand, genre, content type, and budget similarity:")
    
    # Comps table
    display_comps = comps[[
        "title_name", "brand", "genre", "content_type", 
        "production_budget_tier", "total_hours_viewed", "total_value", "roi", "similarity_score"
    ]].copy()
    
    display_comps["total_hours_viewed"] = display_comps["total_hours_viewed"].apply(
        lambda x: f"{x/1_000_000:.1f}M"
    )
    display_comps["total_value"] = display_comps["total_value"].apply(
        lambda x: f"${x/1_000_000:.1f}M"
    )
    display_comps["roi"] = display_comps["roi"].apply(lambda x: f"{x*100:.0f}%")
    
    display_comps.columns = [
        "Title", "Brand", "Genre", "Type", "Budget Tier", 
        "Total Hours", "Total Value", "ROI", "Similarity"
    ]
    
    st.dataframe(display_comps, use_container_width=True, hide_index=True)
    
    # Engagement comparison chart
    st.markdown("#### Engagement Comparison vs Comps")
    
    # Normalize all curves to peak = 1.0 for comparison
    fig = go.Figure()
    
    # Add selected title
    selected_title_data = title_engagement.sort_values("week_number")
    normalized_hours = selected_title_data["proxy_hours_viewed"] / selected_title_data["proxy_hours_viewed"].max()
    
    fig.add_trace(go.Scatter(
        x=selected_title_data["week_number"],
        y=normalized_hours,
        mode='lines',
        name=f"{scorecard.title_name} (Selected)",
        line=dict(width=4, color='#1f77b4')
    ))
    
    # Add comparable titles
    colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    for idx, (_, comp_row) in enumerate(comps.head(3).iterrows()):
        comp_id = comp_row["title_id"]
        comp_engagement = df_engagement[df_engagement["title_id"] == comp_id].sort_values("week_number")
        if not comp_engagement.empty:
            comp_normalized = comp_engagement["proxy_hours_viewed"] / comp_engagement["proxy_hours_viewed"].max()
            fig.add_trace(go.Scatter(
                x=comp_engagement["week_number"],
                y=comp_normalized,
                mode='lines',
                name=comp_row["title_name"][:30],
                line=dict(width=2, color=colors[idx % len(colors)], dash='dash')
            ))
    
    fig.update_layout(
        title="Normalized Engagement Curves (Peak = 1.0)",
        xaxis_title="Week Number",
        yaxis_title="Normalized Hours (Peak = 1.0)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comp performance summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        comp_median_roi = comps["roi"].median()
        st.metric("Comp Median ROI", f"{comp_median_roi*100:.0f}%")
    
    with col2:
        selected_vs_median = "above" if scorecard.roi > comp_median_roi else "below"
        delta = (scorecard.roi - comp_median_roi) * 100
        st.metric("This Title vs Median", selected_vs_median, f"{delta:+.0f}pp")
    
    with col3:
        comp_mean_hours = comps["total_hours_viewed"].mean()
        st.metric("Comp Mean Hours", f"{comp_mean_hours/1_000_000:.1f}M")

else:
    st.info("No comparable titles found with current filters.")

st.markdown("---")

# Quality scores
st.markdown("### ⭐ Quality & Reception")

col1, col2 = st.columns([1, 1])

with col1:
    quality_data = pd.DataFrame({
        'Metric': ['Critic Score', 'Audience Score', 'IMDB Rating (scaled)', 'Buzz Score'],
        'Score': [scorecard.critic_score, scorecard.audience_score, 
                 scorecard.imdb_rating * 10, scorecard.buzz_score]
    })
    
    fig = go.Figure(data=[
        go.Bar(
            x=quality_data['Score'],
            y=quality_data['Metric'],
            orientation='h',
            marker_color=['#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            text=quality_data['Score'].round(1),
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Quality Metrics",
        xaxis_title="Score (0-100)",
        xaxis_range=[0, 100],
        height=300,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Quality Breakdown")
    st.markdown(f"**Critic Score:** {scorecard.critic_score:.1f}/100")
    st.progress(scorecard.critic_score / 100)
    
    st.markdown(f"**Audience Score:** {scorecard.audience_score:.1f}/100")
    st.progress(scorecard.audience_score / 100)
    
    st.markdown(f"**IMDB Rating:** {scorecard.imdb_rating:.1f}/10")
    st.progress(scorecard.imdb_rating / 10)
    
    st.markdown(f"**Buzz Score:** {scorecard.buzz_score:.1f}/100")
    st.progress(scorecard.buzz_score / 100)

st.markdown("---")

# Financial breakdown
st.markdown("### 💰 Financial Performance")

col1, col2 = st.columns([2, 1])

with col1:
    # Value waterfall
    value_components = {
        'Streaming Value': scorecard.streaming_value,
        'Ad Value': scorecard.ad_value,
        'Theatrical Value': scorecard.theatrical_value,
        'PVOD Value': scorecard.pvod_value,
    }
    
    # Filter out zero values
    value_components = {k: v for k, v in value_components.items() if v > 0}
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(value_components.keys()),
            y=[v/1_000_000 for v in value_components.values()],
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(value_components)],
            text=[f"${v/1_000_000:.1f}M" for v in value_components.values()],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Value Components",
        xaxis_title="Component",
        yaxis_title="Value ($ Millions)",
        height=350,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Financial Summary")
    
    st.markdown("**Costs:**")
    st.markdown(f"- Production: ${scorecard.production_budget/1_000_000:.1f}M")
    st.markdown(f"- Marketing: ${scorecard.marketing_spend/1_000_000:.1f}M")
    st.markdown(f"- **Total Cost: ${scorecard.total_cost/1_000_000:.1f}M**")
    
    st.markdown("**Value:**")
    for component, value in value_components.items():
        st.markdown(f"- {component}: ${value/1_000_000:.1f}M")
    st.markdown(f"- **Total Value: ${scorecard.total_value/1_000_000:.1f}M**")
    
    net_value = scorecard.total_value - scorecard.total_cost
    st.markdown(f"\n**Net Value: ${net_value/1_000_000:.1f}M**")
    st.markdown(f"**ROI: {scorecard.roi*100:.0f}%**")

st.markdown("---")

# Analyst Commentary Block
with st.expander("📝 Analyst Commentary (Example Narrative)"):
    # Generate commentary based on metrics
    commentary = []
    
    # Opening
    commentary.append(f"**Executive Summary for {scorecard.title_name}**\n\n")
    
    # Launch and engagement
    peak_week_desc = "early" if scorecard.peak_week <= 2 else "mid-release" if scorecard.peak_week <= 4 else "later"
    decay_desc = "strong" if advanced_metrics['peak_to_week4_decay'] < 0.4 else "moderate" if advanced_metrics['peak_to_week4_decay'] < 0.6 else "significant"
    
    commentary.append(
        f"This title launched with a **{peak_week_desc}** peak in week {scorecard.peak_week}, "
        f"followed by a **{decay_desc}** {advanced_metrics['peak_to_week4_decay']*100:.0f}% drop to week 4. "
    )
    
    # Engagement behavior
    if advanced_metrics['peak_to_week4_decay'] < 0.5:
        engagement_behavior = "sustained engagement, indicating strong word-of-mouth and quality-driven viewing"
    else:
        engagement_behavior = "front-loaded behavior typical of buzz-driven titles"
    
    commentary.append(f"This suggests **{engagement_behavior}**.\n\n")
    
    # ROI context
    if scorecard.roi > 0.8:
        roi_desc = "excellent"
        comp_context = "well above"
    elif scorecard.roi > 0.5:
        roi_desc = "strong"
        comp_context = "above"
    elif scorecard.roi > 0.2:
        roi_desc = "modest"
        comp_context = "near"
    elif scorecard.roi > 0:
        roi_desc = "limited"
        comp_context = "below"
    else:
        roi_desc = "negative"
        comp_context = "significantly below"
    
    if not comps.empty:
        commentary.append(
            f"**Financial Performance:** ROI of **{scorecard.roi*100:.0f}%** is **{roi_desc}**, "
            f"performing **{comp_context}** the median for {scorecard.brand} {scorecard.genre} comps. "
        )
    else:
        commentary.append(
            f"**Financial Performance:** ROI of **{scorecard.roi*100:.0f}%** is **{roi_desc}**. "
        )
    
    commentary.append(
        f"At a cost per hour of **${scorecard.cost_per_hour_viewed:.2f}**, "
        f"efficiency is {'strong' if scorecard.cost_per_hour_viewed < 5 else 'moderate' if scorecard.cost_per_hour_viewed < 10 else 'challenged'}.\n\n"
    )
    
    # Long-tail value
    if scorecard.long_tail_share > 0.45:
        library_value = "**strong long-tail engagement** suggests solid library value"
    elif scorecard.long_tail_share > 0.35:
        library_value = "**moderate long-tail** indicates reasonable library potential"
    else:
        library_value = "**weak long-tail** suggests limited ongoing library value"
    
    commentary.append(f"**Library Outlook:** With {scorecard.long_tail_share*100:.0f}% of hours after week 4, {library_value}.\n\n")
    
    # Strategic recommendation
    commentary.append("**Strategic Implications:**\n")
    if scorecard.classification == "Tentpole":
        commentary.append("- Franchise asset - strong candidate for sequels/spin-offs\n")
    elif scorecard.classification == "Niche Gem":
        commentary.append("- High-efficiency content - model for cost-effective production\n")
    elif scorecard.classification == "Workhorse":
        commentary.append("- Reliable performer - continue similar content strategies\n")
    elif scorecard.classification == "Underperformer":
        commentary.append("- Review production and marketing approach\n")
    
    if advanced_metrics['estimated_incremental_subs'] > 100_000:
        commentary.append(f"- Strong subscriber acquisition (~{advanced_metrics['estimated_incremental_subs']/1000:.0f}K new subs)\n")
    
    if scorecard.roi > 0.5 and not comps.empty:
        commentary.append(f"- Consider greenlighting similar concepts in {scorecard.genre}\n")
    
    st.markdown("".join(commentary))

st.markdown("---")

# Performance Narrative (existing)
st.markdown("### 📋 Detailed Performance Narrative")

narrative = generate_title_narrative(scorecard)
st.markdown(narrative)
