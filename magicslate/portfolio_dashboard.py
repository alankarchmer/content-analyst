"""Portfolio-level analytics for Magic Slate.

This module provides aggregate portfolio views including:
- Performance by brand, genre, and platform
- Concentration analysis
- Portfolio composition metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .title_scorecard import compute_all_scorecards


def compute_portfolio_by_brand(
    df_scorecards: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate portfolio metrics by brand.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        DataFrame with brand-level aggregates
    """
    if df_scorecards.empty:
        return pd.DataFrame()
    
    agg_dict = {
        "title_id": "count",
        "total_hours_viewed": "sum",
        "total_cost": "sum",
        "total_value": "sum",
        "streaming_value": "sum",
        "theatrical_value": "sum",
        "critic_score": "mean",
        "audience_score": "mean",
        "buzz_score": "mean",
    }
    
    result = df_scorecards.groupby("brand").agg(agg_dict).reset_index()
    
    # Rename columns
    result.rename(columns={"title_id": "num_titles"}, inplace=True)
    
    # Compute ROI
    result["roi"] = (result["total_value"] - result["total_cost"]) / result["total_cost"]
    
    # Compute cost per hour
    result["cost_per_hour"] = result["total_cost"] / result["total_hours_viewed"]
    
    # Sort by total value
    result = result.sort_values("total_value", ascending=False)
    
    return result


def compute_portfolio_by_genre(
    df_scorecards: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate portfolio metrics by genre.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        DataFrame with genre-level aggregates
    """
    if df_scorecards.empty:
        return pd.DataFrame()
    
    agg_dict = {
        "title_id": "count",
        "total_hours_viewed": "sum",
        "total_cost": "sum",
        "total_value": "sum",
        "streaming_value": "sum",
        "critic_score": "mean",
        "audience_score": "mean",
    }
    
    result = df_scorecards.groupby("genre").agg(agg_dict).reset_index()
    result.rename(columns={"title_id": "num_titles"}, inplace=True)
    
    result["roi"] = (result["total_value"] - result["total_cost"]) / result["total_cost"]
    result["cost_per_hour"] = result["total_cost"] / result["total_hours_viewed"]
    
    result = result.sort_values("total_value", ascending=False)
    
    return result


def compute_portfolio_by_platform(
    df_scorecards: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate portfolio metrics by platform.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        DataFrame with platform-level aggregates
    """
    if df_scorecards.empty:
        return pd.DataFrame()
    
    agg_dict = {
        "title_id": "count",
        "total_hours_viewed": "sum",
        "total_cost": "sum",
        "total_value": "sum",
        "streaming_value": "sum",
        "ad_value": "sum",
        "critic_score": "mean",
        "audience_score": "mean",
    }
    
    result = df_scorecards.groupby("platform_primary").agg(agg_dict).reset_index()
    result.rename(columns={
        "title_id": "num_titles",
        "platform_primary": "platform"
    }, inplace=True)
    
    result["roi"] = (result["total_value"] - result["total_cost"]) / result["total_cost"]
    result["cost_per_hour"] = result["total_cost"] / result["total_hours_viewed"]
    
    result = result.sort_values("total_value", ascending=False)
    
    return result


def compute_portfolio_by_content_type(
    df_scorecards: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate portfolio metrics by content type (Film vs Series).
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        DataFrame with content-type-level aggregates
    """
    if df_scorecards.empty:
        return pd.DataFrame()
    
    agg_dict = {
        "title_id": "count",
        "total_hours_viewed": "sum",
        "total_cost": "sum",
        "total_value": "sum",
        "streaming_value": "sum",
        "theatrical_value": "sum",
        "critic_score": "mean",
        "audience_score": "mean",
    }
    
    result = df_scorecards.groupby("content_type").agg(agg_dict).reset_index()
    result.rename(columns={"title_id": "num_titles"}, inplace=True)
    
    result["roi"] = (result["total_value"] - result["total_cost"]) / result["total_cost"]
    result["cost_per_hour"] = result["total_cost"] / result["total_hours_viewed"]
    
    result = result.sort_values("total_value", ascending=False)
    
    return result


def compute_concentration_metrics(
    df_scorecards: pd.DataFrame,
    top_n: int = 10
) -> Dict:
    """Compute portfolio concentration metrics.
    
    Analyzes how value is concentrated in top titles.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        top_n: Number of top titles to analyze
        
    Returns:
        Dict with concentration metrics and top titles
    """
    if df_scorecards.empty:
        return {
            "total_titles": 0,
            "top_n": top_n,
            "top_n_share": 0.0,
            "top_n_value": 0.0,
            "total_value": 0.0,
            "top_titles": [],
            "hhi": 0.0,
        }
    
    df = df_scorecards.sort_values("total_value", ascending=False).copy()
    
    total_titles = len(df)
    total_value = df["total_value"].sum()
    
    if total_value <= 0:
        return {
            "total_titles": total_titles,
            "top_n": top_n,
            "top_n_share": 0.0,
            "top_n_value": 0.0,
            "total_value": 0.0,
            "top_titles": [],
            "hhi": 0.0,
        }
    
    # Top N metrics
    top_n_df = df.head(top_n)
    top_n_value = top_n_df["total_value"].sum()
    top_n_share = top_n_value / total_value
    
    # Top titles info
    top_titles = []
    for _, row in top_n_df.iterrows():
        top_titles.append({
            "title_name": row["title_name"],
            "brand": row["brand"],
            "total_value": row["total_value"],
            "value_share": row["total_value"] / total_value,
            "roi": row["roi"],
        })
    
    # Herfindahl-Hirschman Index (concentration measure)
    df["value_share"] = df["total_value"] / total_value
    hhi = (df["value_share"] ** 2).sum() * 10000  # Scale to 0-10000
    
    return {
        "total_titles": total_titles,
        "top_n": top_n,
        "top_n_share": top_n_share,
        "top_n_value": top_n_value,
        "total_value": total_value,
        "top_titles": top_titles,
        "hhi": hhi,
    }


def compute_classification_distribution(
    df_scorecards: pd.DataFrame
) -> pd.DataFrame:
    """Compute distribution of titles by classification.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        DataFrame with classification counts and metrics
    """
    if df_scorecards.empty or "classification" not in df_scorecards.columns:
        return pd.DataFrame()
    
    agg_dict = {
        "title_id": "count",
        "total_hours_viewed": "sum",
        "total_cost": "sum",
        "total_value": "sum",
        "roi": "mean",
    }
    
    result = df_scorecards.groupby("classification").agg(agg_dict).reset_index()
    result.rename(columns={"title_id": "num_titles"}, inplace=True)
    
    # Sort by value
    result = result.sort_values("total_value", ascending=False)
    
    return result


def compute_portfolio_summary(
    df_scorecards: pd.DataFrame
) -> Dict:
    """Compute overall portfolio summary metrics.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        Dict with portfolio-wide summary metrics
    """
    if df_scorecards.empty:
        return {
            "total_titles": 0,
            "total_hours": 0.0,
            "total_cost": 0.0,
            "total_value": 0.0,
            "overall_roi": 0.0,
            "avg_cost_per_hour": 0.0,
            "avg_quality_score": 0.0,
        }
    
    total_titles = len(df_scorecards)
    total_hours = df_scorecards["total_hours_viewed"].sum()
    total_cost = df_scorecards["total_cost"].sum()
    total_value = df_scorecards["total_value"].sum()
    
    overall_roi = (total_value - total_cost) / total_cost if total_cost > 0 else 0.0
    avg_cost_per_hour = total_cost / total_hours if total_hours > 0 else 0.0
    
    avg_critic = df_scorecards["critic_score"].mean()
    avg_audience = df_scorecards["audience_score"].mean()
    avg_quality_score = (avg_critic + avg_audience) / 2
    
    return {
        "total_titles": total_titles,
        "total_hours": total_hours,
        "total_cost": total_cost,
        "total_value": total_value,
        "overall_roi": overall_roi,
        "avg_cost_per_hour": avg_cost_per_hour,
        "avg_quality_score": avg_quality_score,
    }


def filter_scorecards(
    df_scorecards: pd.DataFrame,
    brands: Optional[List[str]] = None,
    genres: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
    content_types: Optional[List[str]] = None,
    min_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Filter scorecards based on various criteria.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        brands: List of brands to include (None = all)
        genres: List of genres to include (None = all)
        platforms: List of platforms to include (None = all)
        content_types: List of content types to include (None = all)
        min_date: Minimum release date (None = all)
        
    Returns:
        Filtered DataFrame
    """
    df = df_scorecards.copy()
    
    if brands:
        df = df[df["brand"].isin(brands)]
    
    if genres:
        df = df[df["genre"].isin(genres)]
    
    if platforms:
        df = df[df["platform_primary"].isin(platforms)]
    
    if content_types:
        df = df[df["content_type"].isin(content_types)]
    
    # Note: min_date filtering would require merging with titles df
    # Skipping for now as scorecards don't have dates
    
    return df


def compute_roi_quartiles(df_scorecards: pd.DataFrame) -> Dict:
    """Compute ROI quartile distribution.
    
    Args:
        df_scorecards: DataFrame with title scorecards
        
    Returns:
        Dict with quartile statistics
    """
    if df_scorecards.empty or "roi" not in df_scorecards.columns:
        return {}
    
    quartiles = df_scorecards["roi"].quantile([0.25, 0.5, 0.75]).to_dict()
    
    return {
        "q1": quartiles[0.25],
        "median": quartiles[0.5],
        "q3": quartiles[0.75],
        "min": df_scorecards["roi"].min(),
        "max": df_scorecards["roi"].max(),
        "mean": df_scorecards["roi"].mean(),
    }


def compute_risk_metrics_by_segment(
    df_scorecards: pd.DataFrame,
    segment_by: str = "brand"
) -> pd.DataFrame:
    """Compute risk metrics (ROI volatility) by segment.
    
    Args:
        df_scorecards: Scorecards DataFrame
        segment_by: Column to segment by ("brand", "genre", etc.)
        
    Returns:
        DataFrame with segment, mean_roi, roi_std (risk metric)
    """
    if df_scorecards.empty or segment_by not in df_scorecards.columns:
        return pd.DataFrame()
    
    result = df_scorecards.groupby(segment_by).agg({
        "roi": ["mean", "std", "count"],
        "total_value": "sum"
    }).reset_index()
    
    result.columns = [segment_by, "mean_roi", "roi_std", "num_titles", "total_value"]
    
    # Fill NaN std with 0 (for single-title segments)
    result["roi_std"] = result["roi_std"].fillna(0)
    
    return result


def compute_hhi_by_segment(
    df_scorecards: pd.DataFrame,
    segment_by: str = "brand"
) -> Dict:
    """Compute Herfindahl-Hirschman Index for a segment.
    
    Args:
        df_scorecards: Scorecards DataFrame
        segment_by: Column to segment by
        
    Returns:
        Dict with HHI and interpretation
    """
    if df_scorecards.empty or segment_by not in df_scorecards.columns:
        return {"hhi": 0, "interpretation": "N/A"}
    
    # Aggregate value by segment
    segment_values = df_scorecards.groupby(segment_by)["total_value"].sum()
    total_value = segment_values.sum()
    
    if total_value <= 0:
        return {"hhi": 0, "interpretation": "N/A"}
    
    # Compute HHI
    shares = segment_values / total_value
    hhi = (shares ** 2).sum() * 10000
    
    # Interpretation
    if hhi < 1500:
        interpretation = "Competitive (Low Concentration)"
    elif hhi < 2500:
        interpretation = "Moderate Concentration"
    else:
        interpretation = "High Concentration"
    
    return {
        "hhi": hhi,
        "interpretation": interpretation,
        "segment_shares": shares.to_dict()
    }


def compute_over_under_investment(
    df_scorecards: pd.DataFrame,
    segment_by: str = "brand"
) -> pd.DataFrame:
    """Identify over/under-invested segments.
    
    A segment is over-invested if cost_share >> value_share.
    A segment is under-invested if value_share >> cost_share.
    
    Args:
        df_scorecards: Scorecards DataFrame
        segment_by: Column to segment by
        
    Returns:
        DataFrame with segment, cost_share, value_share, status
    """
    if df_scorecards.empty or segment_by not in df_scorecards.columns:
        return pd.DataFrame()
    
    # Aggregate by segment
    segment_agg = df_scorecards.groupby(segment_by).agg({
        "total_cost": "sum",
        "total_value": "sum"
    }).reset_index()
    
    total_cost = segment_agg["total_cost"].sum()
    total_value = segment_agg["total_value"].sum()
    
    if total_cost <= 0 or total_value <= 0:
        return pd.DataFrame()
    
    segment_agg["cost_share"] = segment_agg["total_cost"] / total_cost
    segment_agg["value_share"] = segment_agg["total_value"] / total_value
    
    # Compute status
    def determine_status(row):
        cost_share = row["cost_share"]
        value_share = row["value_share"]
        
        # Over-invested: spending more than value created (relative to portfolio)
        if cost_share > value_share * 1.2:
            return "Over-invested ⚠️"
        # Under-invested: creating more value than investment (opportunity)
        elif value_share > cost_share * 1.2:
            return "Under-invested ✅"
        else:
            return "Balanced ➖"
    
    segment_agg["status"] = segment_agg.apply(determine_status, axis=1)
    
    # Sort by value share descending
    segment_agg = segment_agg.sort_values("value_share", ascending=False)
    
    return segment_agg[[segment_by, "cost_share", "value_share", "status"]]


def compute_title_risk_return_data(
    df_scorecards: pd.DataFrame,
    df_titles: pd.DataFrame
) -> pd.DataFrame:
    """Prepare title-level risk/return data for scatter plot.
    
    Risk is defined as the ROI volatility of comparable titles in the same
    brand/genre bucket.
    
    Args:
        df_scorecards: Scorecards DataFrame
        df_titles: Titles DataFrame
        
    Returns:
        DataFrame with title_name, brand, genre, roi, risk_metric
    """
    if df_scorecards.empty:
        return pd.DataFrame()
    
    # Merge with titles for additional context
    df = df_scorecards.merge(
        df_titles[["title_id", "brand", "genre"]],
        on="title_id",
        how="left",
        suffixes=("", "_title")
    )
    
    # Use brand column from scorecard if available, else from titles
    if "brand_title" in df.columns:
        df["brand"] = df["brand"].fillna(df["brand_title"])
    
    # Compute risk as ROI std within brand+genre
    df["brand_genre"] = df["brand"] + " - " + df["genre"]
    
    risk_by_segment = df.groupby("brand_genre")["roi"].std().to_dict()
    
    df["risk_metric"] = df["brand_genre"].map(risk_by_segment)
    df["risk_metric"] = df["risk_metric"].fillna(df["roi"].std())  # Portfolio std as fallback
    
    # Select columns for output
    result = df[[
        "title_id", "title_name", "brand", "genre", 
        "roi", "risk_metric", "total_value", "total_cost"
    ]].copy()
    
    return result


def compute_new_vs_library_split(
    df_scorecards: pd.DataFrame,
    df_titles: pd.DataFrame,
    recent_cutoff_date: Optional[pd.Timestamp] = None
) -> Dict:
    """Compute value split between new releases and library titles.
    
    Args:
        df_scorecards: Scorecards DataFrame
        df_titles: Titles DataFrame with release dates
        recent_cutoff_date: Date to define "new" (default: last 12 months)
        
    Returns:
        Dict with new_share, library_share, new_value, library_value
    """
    if df_scorecards.empty or df_titles.empty:
        return {
            "new_share": 0.0,
            "library_share": 0.0,
            "new_value": 0.0,
            "library_value": 0.0,
        }
    
    # Merge to get dates
    df = df_scorecards.merge(
        df_titles[["title_id", "release_disney_plus_date", "release_hulu_date"]],
        on="title_id",
        how="left"
    )
    
    # Determine release date (use whichever is earlier)
    df["release_date"] = df[["release_disney_plus_date", "release_hulu_date"]].min(axis=1)
    
    # If no cutoff provided, use last 12 months
    if recent_cutoff_date is None:
        max_date = df["release_date"].max()
        if pd.notna(max_date):
            recent_cutoff_date = max_date - pd.DateOffset(months=12)
        else:
            recent_cutoff_date = pd.Timestamp("2023-01-01")
    
    # Classify
    df["is_new"] = df["release_date"] >= recent_cutoff_date
    
    new_value = df[df["is_new"] == True]["total_value"].sum()
    library_value = df[df["is_new"] == False]["total_value"].sum()
    total_value = df["total_value"].sum()
    
    new_share = new_value / total_value if total_value > 0 else 0.0
    library_share = library_value / total_value if total_value > 0 else 0.0
    
    return {
        "new_share": new_share,
        "library_share": library_share,
        "new_value": new_value,
        "library_value": library_value,
        "new_count": df["is_new"].sum(),
        "library_count": (~df["is_new"]).sum(),
    }
