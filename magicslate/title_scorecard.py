"""Title-level performance scorecard analytics for Magic Slate.

This module computes comprehensive per-title performance metrics including
engagement, quality, financial performance, and classification.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .data_models import TitleScorecard
from . import metrics as met
from . import assumptions as asmp


def compute_title_scorecard(
    title_id: str,
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame
) -> TitleScorecard:
    """Compute comprehensive performance scorecard for a title.
    
    This function aggregates all key performance indicators for a single title
    including engagement metrics, quality scores, financial value, and
    performance classification.
    
    Args:
        title_id: Title identifier
        df_titles: DataFrame with title metadata
        df_engagement: DataFrame with engagement data
        df_quality: DataFrame with quality scores
        
    Returns:
        TitleScorecard object with all computed metrics
    """
    # Get title data
    title_row = df_titles[df_titles["title_id"] == title_id].iloc[0]
    title_engagement = df_engagement[df_engagement["title_id"] == title_id].copy()
    quality_row = df_quality[df_quality["title_id"] == title_id].iloc[0]
    
    # Extract basic metadata
    title_name = title_row["title_name"]
    brand = title_row["brand"]
    genre = title_row["genre"]
    platform = title_row["platform_primary"]
    content_type = title_row["content_type"]
    
    # Compute engagement metrics
    engagement_metrics = met.compute_engagement_curve(title_engagement)
    total_hours = engagement_metrics["total_hours"]
    
    # Extract quality metrics
    quality_dict = {
        "critic_score": quality_row["critic_score"],
        "audience_score": quality_row["audience_score"],
        "imdb_rating": quality_row["imdb_rating"],
        "buzz_score": quality_row["buzz_score"],
    }
    
    # Compute financial metrics
    production_budget = title_row["estimated_production_budget"] * 1_000_000  # Convert to dollars
    marketing_spend = title_row["estimated_marketing_spend"] * 1_000_000
    total_cost = production_budget + marketing_spend
    
    # Streaming value
    title_metadata = title_row.to_dict()
    value_metrics = met.hours_to_value_metrics(
        total_hours=total_hours,
        title_metadata=title_metadata,
        quality_scores=quality_dict,
        platform=platform
    )
    streaming_value = value_metrics["total_streaming_value"]
    ad_value = value_metrics["ad_value"]
    
    # Theatrical and PVOD value (if applicable)
    theatrical_value = 0.0
    pvod_value = 0.0
    
    if content_type == "Film" and title_row["release_theatrical_date"] is not pd.NaT:
        theatrical_value = asmp.estimate_theatrical_revenue(
            title_metadata=title_metadata,
            quality_scores=quality_dict
        )
        
        # PVOD value (if applicable)
        if title_row["release_pvod_date"] is not pd.NaT and theatrical_value > 0:
            # Calculate streaming window
            streaming_date = (title_row["release_disney_plus_date"] 
                            if pd.notna(title_row["release_disney_plus_date"]) 
                            else title_row["release_hulu_date"])
            
            if pd.notna(streaming_date):
                theatrical_date = title_row["release_theatrical_date"]
                window_days = (streaming_date - theatrical_date).days
            else:
                window_days = 90  # Default
            
            pvod_value = asmp.estimate_pvod_revenue(
                theatrical_revenue=theatrical_value,
                quality_scores=quality_dict,
                streaming_window_days=window_days
            )
    
    # Total value and ROI
    total_value = streaming_value + ad_value + theatrical_value + pvod_value
    roi = (total_value - total_cost) / total_cost if total_cost > 0 else 0.0
    
    # Cost per hour
    cost_per_hour = total_cost / total_hours if total_hours > 0 else float("inf")
    
    # Classification
    classification = met.classify_title_performance(
        total_value=total_value,
        total_cost=total_cost,
        roi=roi,
        budget_tier=title_row["production_budget_tier"],
        cost_per_hour=cost_per_hour
    )
    
    # Build scorecard
    scorecard = TitleScorecard(
        title_id=title_id,
        title_name=title_name,
        brand=brand,
        genre=genre,
        platform_primary=platform,
        content_type=content_type,
        total_hours_viewed=total_hours,
        peak_hours=engagement_metrics["peak_hours"],
        peak_week=engagement_metrics["peak_week"],
        long_tail_share=engagement_metrics["long_tail_share"],
        decay_rate=engagement_metrics["decay_rate"],
        critic_score=quality_dict["critic_score"],
        audience_score=quality_dict["audience_score"],
        imdb_rating=quality_dict["imdb_rating"],
        buzz_score=quality_dict["buzz_score"],
        production_budget=production_budget,
        marketing_spend=marketing_spend,
        total_cost=total_cost,
        streaming_value=streaming_value,
        ad_value=ad_value,
        theatrical_value=theatrical_value,
        pvod_value=pvod_value,
        total_value=total_value,
        roi=roi,
        cost_per_hour_viewed=cost_per_hour,
        classification=classification,
    )
    
    return scorecard


def generate_title_narrative(scorecard: TitleScorecard) -> str:
    """Generate a natural language narrative describing title performance.
    
    Args:
        scorecard: TitleScorecard object
        
    Returns:
        Narrative string describing the title's performance
    """
    narratives = []
    
    # Opening
    narratives.append(f"{scorecard.title_name} is a {scorecard.brand} {scorecard.content_type.lower()}")
    
    # Classification
    if scorecard.classification == "Tentpole":
        narratives.append("classified as a **Tentpole** title - a high-budget, high-value franchise asset.")
    elif scorecard.classification == "Niche Gem":
        narratives.append("classified as a **Niche Gem** - delivering exceptional value at low cost.")
    elif scorecard.classification == "Workhorse":
        narratives.append("classified as a **Workhorse** - a reliable, solid performer.")
    elif scorecard.classification == "Underperformer":
        narratives.append("classified as an **Underperformer** - failing to recoup its investment.")
    else:
        narratives.append(f"classified as **{scorecard.classification}**.")
    
    # Engagement
    hours_millions = scorecard.total_hours_viewed / 1_000_000
    narratives.append(f"\nThe title generated **{hours_millions:.1f}M hours** of viewing, ")
    narratives.append(f"peaking at {scorecard.peak_hours/1_000_000:.1f}M hours in week {scorecard.peak_week}.")
    
    if scorecard.long_tail_share > 0.4:
        narratives.append(f" It shows strong long-tail engagement ({scorecard.long_tail_share*100:.0f}% of hours after week 4).")
    
    # Quality
    avg_quality = (scorecard.critic_score + scorecard.audience_score) / 2
    if avg_quality > 80:
        quality_desc = "excellent"
    elif avg_quality > 70:
        quality_desc = "strong"
    elif avg_quality > 60:
        quality_desc = "moderate"
    else:
        quality_desc = "mixed"
    
    narratives.append(f"\n\nQuality reception was **{quality_desc}** ")
    narratives.append(f"(critics: {scorecard.critic_score:.0f}/100, audience: {scorecard.audience_score:.0f}/100).")
    
    # Financial
    roi_pct = scorecard.roi * 100
    if scorecard.roi > 1.0:
        financial_desc = "exceptional"
    elif scorecard.roi > 0.5:
        financial_desc = "strong"
    elif scorecard.roi > 0:
        financial_desc = "positive but modest"
    else:
        financial_desc = "negative"
    
    narratives.append(f"\n\nFinancially, the title delivered **{financial_desc} returns** ")
    narratives.append(f"with an ROI of **{roi_pct:.0f}%**. ")
    narratives.append(f"Total value generated: ${scorecard.total_value/1_000_000:.1f}M ")
    narratives.append(f"against costs of ${scorecard.total_cost/1_000_000:.1f}M.")
    
    return "".join(narratives)


def compute_all_scorecards(
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame
) -> pd.DataFrame:
    """Compute scorecards for all titles.
    
    Args:
        df_titles: DataFrame with title metadata
        df_engagement: DataFrame with engagement data
        df_quality: DataFrame with quality scores
        
    Returns:
        DataFrame with all scorecards
    """
    scorecards = []
    
    for title_id in df_titles["title_id"]:
        scorecard = compute_title_scorecard(
            title_id=title_id,
            df_titles=df_titles,
            df_engagement=df_engagement,
            df_quality=df_quality
        )
        
        # Convert to dict
        scorecard_dict = {
            "title_id": scorecard.title_id,
            "title_name": scorecard.title_name,
            "brand": scorecard.brand,
            "genre": scorecard.genre,
            "platform_primary": scorecard.platform_primary,
            "content_type": scorecard.content_type,
            "total_hours_viewed": scorecard.total_hours_viewed,
            "peak_hours": scorecard.peak_hours,
            "peak_week": scorecard.peak_week,
            "long_tail_share": scorecard.long_tail_share,
            "decay_rate": scorecard.decay_rate,
            "critic_score": scorecard.critic_score,
            "audience_score": scorecard.audience_score,
            "imdb_rating": scorecard.imdb_rating,
            "buzz_score": scorecard.buzz_score,
            "production_budget": scorecard.production_budget,
            "marketing_spend": scorecard.marketing_spend,
            "total_cost": scorecard.total_cost,
            "streaming_value": scorecard.streaming_value,
            "ad_value": scorecard.ad_value,
            "theatrical_value": scorecard.theatrical_value,
            "pvod_value": scorecard.pvod_value,
            "total_value": scorecard.total_value,
            "roi": scorecard.roi,
            "cost_per_hour_viewed": scorecard.cost_per_hour_viewed,
            "classification": scorecard.classification,
        }
        
        scorecards.append(scorecard_dict)
    
    return pd.DataFrame(scorecards)
