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
