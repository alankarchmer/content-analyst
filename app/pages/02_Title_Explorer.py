"""Title Explorer page for Magic Slate."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from magicslate.title_scorecard import compute_title_scorecard, generate_title_narrative

st.set_page_config(page_title="Title Explorer - Magic Slate", page_icon="🎬", layout="wide")

st.title("🎬 Title Explorer")
st.markdown("Deep dive into individual title performance")

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

# Key metrics
st.markdown("### 📊 Key Metrics")

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

# Engagement curve
st.markdown("### 📈 Engagement Curve")

title_engagement = df_engagement[df_engagement["title_id"] == selected_title_id].copy()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=title_engagement["week_number"],
    y=title_engagement["proxy_hours_viewed"] / 1_000_000,
    mode='lines+markers',
    name='Hours Viewed',
    line=dict(color='#1f77b4', width=3),
    fill='tozeroy',
    fillcolor='rgba(31, 119, 180, 0.2)'
))

fig.update_layout(
    title="Weekly Hours Viewed Over Time",
    xaxis_title="Week Number",
    yaxis_title="Hours Viewed (Millions)",
    height=400,
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Long Tail Share", f"{scorecard.long_tail_share*100:.0f}%")
    st.caption("Hours after week 4")

with col2:
    st.metric("Decay Rate", f"{scorecard.decay_rate:.3f}")
    st.caption("Exponential decay parameter")

with col3:
    weeks_above = df_scorecards[df_scorecards["title_id"] == selected_title_id].iloc[0]
    # Calculate weeks above threshold
    threshold = scorecard.peak_hours * 0.1
    weeks_above_count = (title_engagement["proxy_hours_viewed"] > threshold).sum()
    st.metric("Weeks Above 10%", weeks_above_count)
    st.caption("Of peak performance")

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

# Narrative
st.markdown("### 📝 Performance Narrative")

narrative = generate_title_narrative(scorecard)
st.markdown(narrative)
