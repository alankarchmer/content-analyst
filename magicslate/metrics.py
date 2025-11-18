"""Core metrics and calculation functions for Magic Slate.

This module provides reusable functions for computing engagement metrics,
financial value, and analytical transformations.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from . import assumptions as asmp


def compute_engagement_curve(df_engagement: pd.DataFrame) -> Dict:
    """Compute engagement curve metrics for a title.
    
    Analyzes the time-series pattern of hours viewed to extract:
    - Peak performance
    - Decay characteristics
    - Long-tail behavior
    
    Args:
        df_engagement: DataFrame with columns [week_number, proxy_hours_viewed]
        
    Returns:
        Dict with engagement metrics:
            - peak_hours: Maximum hours in any week
            - peak_week: Week number of peak
            - total_hours: Total hours across all weeks
            - decay_rate: Exponential decay parameter
            - long_tail_share: Fraction of hours after week 4
            - weeks_above_threshold: Weeks with >10% of peak hours
    """
    if df_engagement.empty:
        return {
            "peak_hours": 0.0,
            "peak_week": 0,
            "total_hours": 0.0,
            "decay_rate": 0.0,
            "long_tail_share": 0.0,
            "weeks_above_threshold": 0,
        }
    
    df = df_engagement.sort_values("week_number").copy()
    
    # Basic metrics
    peak_idx = df["proxy_hours_viewed"].idxmax()
    peak_hours = df.loc[peak_idx, "proxy_hours_viewed"]
    peak_week = df.loc[peak_idx, "week_number"]
    total_hours = df["proxy_hours_viewed"].sum()
    
    # Decay rate estimation (exponential fit after peak)
    post_peak = df[df["week_number"] > peak_week].copy()
    
    decay_rate = 0.0
    if len(post_peak) >= 3:
        # Fit exponential decay: hours = peak * exp(-decay_rate * weeks_since_peak)
        post_peak["weeks_since_peak"] = post_peak["week_number"] - peak_week
        post_peak["log_hours"] = np.log(post_peak["proxy_hours_viewed"] + 1)  # +1 to avoid log(0)
        
        # Simple linear regression on log-transformed data
        X = post_peak["weeks_since_peak"].values
        y = post_peak["log_hours"].values
        
        if len(X) > 1 and np.std(X) > 0:
            # Fit line: log(hours) = intercept + slope * weeks
            slope = np.cov(X, y)[0, 1] / np.var(X) if np.var(X) > 0 else 0
            decay_rate = -slope  # Negative slope = positive decay rate
            decay_rate = max(0, decay_rate)  # Ensure non-negative
    
    # Long tail share (hours after week 4)
    long_tail_hours = df[df["week_number"] > 4]["proxy_hours_viewed"].sum()
    long_tail_share = long_tail_hours / total_hours if total_hours > 0 else 0.0
    
    # Weeks above threshold (>10% of peak)
    threshold = peak_hours * 0.1
    weeks_above_threshold = (df["proxy_hours_viewed"] > threshold).sum()
    
    return {
        "peak_hours": peak_hours,
        "peak_week": int(peak_week),
        "total_hours": total_hours,
        "decay_rate": decay_rate,
        "long_tail_share": long_tail_share,
        "weeks_above_threshold": int(weeks_above_threshold),
    }


def hours_to_value_metrics(
    total_hours: float,
    title_metadata: dict,
    quality_scores: dict,
    platform: str
) -> Dict[str, float]:
    """Convert hours viewed into estimated value components.
    
    Uses business assumptions to model how engagement translates to:
    - Subscriber acquisition
    - Subscriber retention
    - Ad revenue (for Hulu)
    - Total streaming value
    
    Args:
        total_hours: Total hours viewed
        title_metadata: Dict with title information
        quality_scores: Dict with quality metrics
        platform: "Disney+" or "Hulu"
        
    Returns:
        Dict with value metrics:
            - acquisition_value: Value from new subscribers
            - retention_value: Value from reduced churn
            - ad_value: Ad revenue (Hulu only)
            - total_streaming_value: Sum of all streaming value
    """
    # Acquisition value
    new_subs = asmp.estimate_new_subscribers_from_hours(
        total_hours, title_metadata, quality_scores
    )
    arpu = asmp.get_platform_arpu(platform)
    
    # Assume new subscribers stay average of 18 months
    avg_lifetime_months = 18
    acquisition_value = new_subs * arpu * avg_lifetime_months
    
    # Retention value
    retained_sub_months = asmp.estimate_retained_subscriber_months_from_hours(
        total_hours, title_metadata, quality_scores
    )
    retention_value = retained_sub_months * arpu
    
    # Ad value (Hulu only)
    ad_value = 0.0
    if platform == "Hulu":
        ad_value = asmp.estimate_ad_revenue_hulu(total_hours)
    
    total_streaming_value = acquisition_value + retention_value + ad_value
    
    return {
        "acquisition_value": acquisition_value,
        "retention_value": retention_value,
        "ad_value": ad_value,
        "total_streaming_value": total_streaming_value,
    }


def compute_npv(
    cashflows: pd.Series,
    discount_rate: float = asmp.DISCOUNT_RATE,
    periods_per_year: float = 12.0
) -> float:
    """Compute Net Present Value of a cashflow series.
    
    Args:
        cashflows: Series of cashflows indexed by period
        discount_rate: Annual discount rate (e.g., 0.10 for 10%)
        periods_per_year: Number of periods per year (12 for monthly, 52 for weekly)
        
    Returns:
        NPV of cashflows
    """
    if cashflows.empty:
        return 0.0
    
    # Convert to period discount rate
    period_discount_rate = (1 + discount_rate) ** (1 / periods_per_year) - 1
    
    # Compute NPV
    npv = 0.0
    for period, cashflow in cashflows.items():
        discount_factor = 1 / ((1 + period_discount_rate) ** period)
        npv += cashflow * discount_factor
    
    return npv


def aggregate_title_value(
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate value metrics for all titles.
    
    Computes title-level metrics including engagement, quality, and value
    for the entire catalog.
    
    Args:
        df_titles: Title metadata DataFrame
        df_engagement: Engagement metrics DataFrame
        df_quality: Quality scores DataFrame
        
    Returns:
        DataFrame with one row per title and aggregated metrics
    """
    results = []
    
    for _, title_row in df_titles.iterrows():
        title_id = title_row["title_id"]
        
        # Get engagement data
        title_engagement = df_engagement[df_engagement["title_id"] == title_id]
        engagement_metrics = compute_engagement_curve(title_engagement)
        
        # Get quality data
        quality_row = df_quality[df_quality["title_id"] == title_id]
        quality_dict = quality_row.to_dict("records")[0] if not quality_row.empty else {}
        
        # Compute value
        title_metadata = title_row.to_dict()
        platform = title_row["platform_primary"]
        
        value_metrics = hours_to_value_metrics(
            total_hours=engagement_metrics["total_hours"],
            title_metadata=title_metadata,
            quality_scores=quality_dict,
            platform=platform
        )
        
        # Combine metrics
        result = {
            "title_id": title_id,
            "title_name": title_row["title_name"],
            "brand": title_row["brand"],
            "genre": title_row["genre"],
            "platform_primary": platform,
            "content_type": title_row["content_type"],
            "production_budget": title_row["estimated_production_budget"],
            "marketing_spend": title_row["estimated_marketing_spend"],
            **engagement_metrics,
            **quality_dict,
            **value_metrics,
        }
        
        results.append(result)
    
    return pd.DataFrame(results)


def classify_title_performance(
    total_value: float,
    total_cost: float,
    roi: float,
    budget_tier: str,
    cost_per_hour: float
) -> str:
    """Classify a title's performance into categories.
    
    Categories:
    - Tentpole: High-budget, high-value franchise content
    - Workhorse: Solid performers with good ROI
    - Niche Gem: Low-cost, high-efficiency content
    - Underperformer: Negative or very low ROI
    
    Args:
        total_value: Total value generated
        total_cost: Total production + marketing cost
        roi: Return on investment (value - cost) / cost
        budget_tier: "Low", "Medium", or "High"
        cost_per_hour: Cost per hour viewed
        
    Returns:
        Classification string
    """
    # Tentpole: Big budget, big value
    if (total_cost >= asmp.TENTPOLE_THRESHOLD["min_budget"] and 
        total_value >= asmp.TENTPOLE_THRESHOLD["min_value"]):
        return "Tentpole"
    
    # Underperformer: Negative or very low ROI
    if roi <= asmp.UNDERPERFORMER_THRESHOLD["max_roi"]:
        return "Underperformer"
    
    # Niche gem: Low cost, high efficiency
    if (total_cost <= asmp.NICHE_GEM_THRESHOLD["max_budget"] and
        roi >= asmp.NICHE_GEM_THRESHOLD["min_roi"] and
        cost_per_hour <= asmp.NICHE_GEM_THRESHOLD["max_cost_per_hour"]):
        return "Niche Gem"
    
    # Workhorse: Solid middle performers
    if (roi >= asmp.WORKHORSE_THRESHOLD["min_roi"] and
        roi <= asmp.WORKHORSE_THRESHOLD["max_roi"] and
        total_cost >= asmp.WORKHORSE_THRESHOLD["min_budget"]):
        return "Workhorse"
    
    # Default: acceptable performer
    if roi > 0.3:
        return "Acceptable"
    
    return "Marginal"


def compute_portfolio_concentration(
    df_titles_with_value: pd.DataFrame,
    top_n: int = 10
) -> Dict:
    """Compute concentration metrics for the portfolio.
    
    Analyzes how value is distributed across the catalog.
    
    Args:
        df_titles_with_value: DataFrame with title value metrics
        top_n: Number of top titles to analyze
        
    Returns:
        Dict with concentration metrics
    """
    if df_titles_with_value.empty or "total_streaming_value" not in df_titles_with_value.columns:
        return {
            "top_n_share": 0.0,
            "top_n_titles": [],
            "hhi": 0.0,
        }
    
    df = df_titles_with_value.sort_values("total_streaming_value", ascending=False).copy()
    
    total_value = df["total_streaming_value"].sum()
    
    if total_value <= 0:
        return {
            "top_n_share": 0.0,
            "top_n_titles": [],
            "hhi": 0.0,
        }
    
    # Top N concentration
    top_n_value = df.head(top_n)["total_streaming_value"].sum()
    top_n_share = top_n_value / total_value
    
    top_n_titles = df.head(top_n)[["title_name", "total_streaming_value"]].to_dict("records")
    
    # Herfindahl-Hirschman Index (measure of concentration)
    df["value_share"] = df["total_streaming_value"] / total_value
    hhi = (df["value_share"] ** 2).sum() * 10000  # Scale to 0-10000
    
    return {
        "top_n_share": top_n_share,
        "top_n_titles": top_n_titles,
        "hhi": hhi,
    }


def rolling_engagement_stats(
    df_engagement: pd.DataFrame,
    window: int = 4
) -> pd.DataFrame:
    """Compute rolling statistics for engagement data.
    
    Args:
        df_engagement: Engagement DataFrame with week_number and proxy_hours_viewed
        window: Rolling window size in weeks
        
    Returns:
        DataFrame with additional rolling statistics columns
    """
    df = df_engagement.sort_values(["title_id", "week_number"]).copy()
    
    # Compute rolling stats by title
    df["rolling_avg_hours"] = df.groupby("title_id")["proxy_hours_viewed"].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    
    df["rolling_std_hours"] = df.groupby("title_id")["proxy_hours_viewed"].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )
    
    return df


def calculate_cost_efficiency_metrics(
    total_hours: float,
    total_cost: float,
    total_value: float
) -> Dict[str, float]:
    """Calculate cost efficiency metrics.
    
    Args:
        total_hours: Total hours viewed
        total_cost: Total production + marketing cost
        total_value: Total value generated
        
    Returns:
        Dict with efficiency metrics
    """
    cost_per_hour = total_cost / total_hours if total_hours > 0 else float("inf")
    value_per_dollar = total_value / total_cost if total_cost > 0 else 0.0
    roi = (total_value - total_cost) / total_cost if total_cost > 0 else 0.0
    
    return {
        "cost_per_hour_viewed": cost_per_hour,
        "value_per_dollar_spent": value_per_dollar,
        "roi": roi,
    }
