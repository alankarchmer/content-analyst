"""Business assumptions and parameters for Magic Slate.

This module defines core financial and operational assumptions used across
the analytics platform, including ARPU, conversion rates, and economic parameters.
"""

import numpy as np
import pandas as pd


# ============================================================================
# STREAMING ECONOMICS
# ============================================================================

# Average Revenue Per User (monthly subscription)
DISNEY_PLUS_ARPU = 7.99  # USD per month
HULU_ARPU = 12.99  # USD per month (assuming ad-free tier average)

# Ad-supported revenue
HULU_AD_ARPU_PER_HOUR = 0.05  # USD per hour viewed (ad-supported tier)

# Churn assumptions
BASE_MONTHLY_CHURN_RATE = 0.05  # 5% monthly churn baseline


# ============================================================================
# ENGAGEMENT TO VALUE CONVERSION
# ============================================================================

# Acquisition conversion factors (new subscribers per 1M hours viewed)
# These represent how many new subscribers a title drives based on its appeal
ACQUISITION_CONVERSION_BASE = 50  # Base new subs per 1M hours
ACQUISITION_QUALITY_MULTIPLIER = 1.5  # Multiplier for high-quality content

# Retention impact (additional subscriber-months retained per 1M hours)
# Represents reduced churn due to content satisfaction
RETENTION_IMPACT_BASE = 100  # Additional sub-months per 1M hours
RETENTION_QUALITY_MULTIPLIER = 1.3  # Multiplier for high-quality content


# ============================================================================
# WINDOWING & LICENSING
# ============================================================================

# Cannibalization factors (how much early streaming reduces other windows)
PVOD_CANNIBALIZATION_FACTOR = 0.3  # 30% reduction in PVOD if streaming early
LICENSE_CANNIBALIZATION_FACTOR = 0.25  # 25% reduction in streaming value if licensed

# Theatrical performance assumptions
THEATRICAL_MULTIPLIER_BY_TIER = {
    "Low": 2.5,  # Box office as multiple of production budget
    "Medium": 3.0,
    "High": 3.5,
}

# PVOD assumptions (as % of theatrical revenue)
PVOD_REVENUE_PCT_OF_THEATRICAL = 0.15  # 15% of theatrical


# ============================================================================
# FINANCIAL PARAMETERS
# ============================================================================

# Discount rate for NPV calculations
DISCOUNT_RATE = 0.10  # 10% annual discount rate

# Time value parameters
MONTHS_PER_YEAR = 12
WEEKS_PER_YEAR = 52


# ============================================================================
# CLASSIFICATION THRESHOLDS
# ============================================================================

# Title classification based on performance metrics
TENTPOLE_THRESHOLD = {
    "min_budget": 80_000_000,  # $80M+
    "min_value": 200_000_000,  # $200M+ total value
}

WORKHORSE_THRESHOLD = {
    "min_roi": 0.5,  # 50% ROI
    "max_roi": 2.0,
    "min_budget": 10_000_000,
}

NICHE_GEM_THRESHOLD = {
    "max_budget": 20_000_000,
    "min_roi": 1.5,  # 150% ROI
    "max_cost_per_hour": 5.0,  # $5 per hour
}

UNDERPERFORMER_THRESHOLD = {
    "max_roi": 0.0,  # Negative ROI
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def estimate_new_subscribers_from_hours(
    hours_viewed: float,
    title_metadata: dict,
    quality_scores: dict
) -> float:
    """Estimate new subscriber acquisition from content hours viewed.
    
    This models how compelling content drives platform adoption. High-quality,
    buzzworthy titles drive disproportionate acquisition.
    
    Args:
        hours_viewed: Total hours viewed
        title_metadata: Dict with title info (brand, content_type, etc.)
        quality_scores: Dict with quality metrics
        
    Returns:
        Estimated number of new subscribers acquired
    """
    if hours_viewed <= 0:
        return 0.0
    
    # Base conversion
    hours_millions = hours_viewed / 1_000_000
    base_subs = hours_millions * ACQUISITION_CONVERSION_BASE
    
    # Quality multiplier (buzz and audience scores matter most for acquisition)
    quality_factor = 1.0
    if "buzz_score" in quality_scores and quality_scores["buzz_score"] > 70:
        quality_factor *= ACQUISITION_QUALITY_MULTIPLIER
    if "audience_score" in quality_scores and quality_scores["audience_score"] > 80:
        quality_factor *= 1.2
    
    # Brand multiplier (marquee brands drive more acquisition)
    brand = title_metadata.get("brand", "")
    brand_multiplier = {
        "Marvel": 1.5,
        "Star Wars": 1.4,
        "Pixar": 1.3,
    }.get(brand, 1.0)
    
    # Content type (films tend to drive more acquisition than series)
    content_type_multiplier = 1.2 if title_metadata.get("content_type") == "Film" else 1.0
    
    new_subs = base_subs * quality_factor * brand_multiplier * content_type_multiplier
    
    return new_subs


def estimate_retained_subscriber_months_from_hours(
    hours_viewed: float,
    title_metadata: dict,
    quality_scores: dict
) -> float:
    """Estimate subscriber retention impact from content hours viewed.
    
    This models how satisfying content reduces churn. Quality content keeps
    subscribers engaged and less likely to cancel.
    
    Args:
        hours_viewed: Total hours viewed
        title_metadata: Dict with title info
        quality_scores: Dict with quality metrics
        
    Returns:
        Estimated additional subscriber-months retained
    """
    if hours_viewed <= 0:
        return 0.0
    
    # Base retention impact
    hours_millions = hours_viewed / 1_000_000
    base_retention_months = hours_millions * RETENTION_IMPACT_BASE
    
    # Quality multiplier (high-quality content has stronger retention impact)
    quality_factor = 1.0
    avg_quality = (quality_scores.get("critic_score", 70) + 
                   quality_scores.get("audience_score", 70)) / 2
    if avg_quality > 75:
        quality_factor *= RETENTION_QUALITY_MULTIPLIER
    
    # Series have stronger retention impact (keep viewers coming back)
    content_type = title_metadata.get("content_type", "")
    content_multiplier = 1.3 if content_type == "Series" else 1.0
    
    retention_months = base_retention_months * quality_factor * content_multiplier
    
    return retention_months


def estimate_theatrical_revenue(
    title_metadata: dict,
    quality_scores: dict
) -> float:
    """Estimate theatrical box office revenue.
    
    Simple model based on production budget, quality, and brand appeal.
    
    Args:
        title_metadata: Dict with title info including budget
        quality_scores: Dict with quality metrics
        
    Returns:
        Estimated theatrical revenue in USD
    """
    budget = title_metadata.get("estimated_production_budget", 0)
    budget_tier = title_metadata.get("production_budget_tier", "Medium")
    
    if budget <= 0 or title_metadata.get("content_type") != "Film":
        return 0.0
    
    # Base multiplier by tier
    base_multiplier = THEATRICAL_MULTIPLIER_BY_TIER.get(budget_tier, 3.0)
    
    # Quality impact (good films overperform, bad films underperform)
    avg_score = (quality_scores.get("critic_score", 70) + 
                 quality_scores.get("audience_score", 70)) / 2
    quality_factor = 0.5 + (avg_score / 100) * 1.5  # Range: 0.5 to 2.0
    
    # Brand impact
    brand = title_metadata.get("brand", "")
    brand_multiplier = {
        "Marvel": 1.8,
        "Star Wars": 1.6,
        "Pixar": 1.4,
        "Disney Animation": 1.2,
    }.get(brand, 1.0)
    
    # Budget in millions
    budget_millions = budget
    theatrical_revenue = budget_millions * base_multiplier * quality_factor * brand_multiplier
    
    # Add some variance
    theatrical_revenue *= np.random.uniform(0.8, 1.2)
    
    return max(0, theatrical_revenue * 1_000_000)  # Return in dollars


def estimate_pvod_revenue(
    theatrical_revenue: float,
    quality_scores: dict,
    streaming_window_days: int
) -> float:
    """Estimate PVOD (Premium Video On Demand) revenue.
    
    PVOD revenue depends on theatrical performance and timing.
    Earlier streaming reduces PVOD window and revenue.
    
    Args:
        theatrical_revenue: Theatrical box office revenue
        quality_scores: Dict with quality metrics
        streaming_window_days: Days until streaming release
        
    Returns:
        Estimated PVOD revenue in USD
    """
    if theatrical_revenue <= 0:
        return 0.0
    
    # Base PVOD is fraction of theatrical
    base_pvod = theatrical_revenue * PVOD_REVENUE_PCT_OF_THEATRICAL
    
    # Window adjustment (shorter window = more cannibalization)
    if streaming_window_days < 45:
        window_factor = 1.0 - PVOD_CANNIBALIZATION_FACTOR
    elif streaming_window_days < 75:
        window_factor = 1.0 - (PVOD_CANNIBALIZATION_FACTOR * 0.5)
    else:
        window_factor = 1.0
    
    # Quality boost (high-quality films have better PVOD performance)
    avg_score = (quality_scores.get("critic_score", 70) + 
                 quality_scores.get("audience_score", 70)) / 2
    quality_factor = 0.7 + (avg_score / 100) * 0.6  # Range: 0.7 to 1.3
    
    pvod_revenue = base_pvod * window_factor * quality_factor
    
    return max(0, pvod_revenue)


def estimate_ad_revenue_hulu(hours_viewed: float) -> float:
    """Estimate ad revenue from Hulu viewing.
    
    Args:
        hours_viewed: Total hours viewed on Hulu
        
    Returns:
        Estimated ad revenue in USD
    """
    # Assume 30% of Hulu viewers are on ad-supported tier
    ad_tier_pct = 0.30
    ad_hours = hours_viewed * ad_tier_pct
    ad_revenue = ad_hours * HULU_AD_ARPU_PER_HOUR
    
    return ad_revenue


def get_platform_arpu(platform: str) -> float:
    """Get monthly ARPU for a platform.
    
    Args:
        platform: "Disney+" or "Hulu"
        
    Returns:
        Monthly ARPU in USD
    """
    if platform == "Disney+":
        return DISNEY_PLUS_ARPU
    elif platform == "Hulu":
        return HULU_ARPU
    else:
        return DISNEY_PLUS_ARPU  # Default


def apply_license_cannibalization(
    base_streaming_value: float,
    has_third_party_license: bool
) -> float:
    """Apply cannibalization from third-party licensing.
    
    When content is licensed to third parties, it reduces long-term
    streaming value as viewers can find it elsewhere.
    
    Args:
        base_streaming_value: Base streaming value without licensing
        has_third_party_license: Whether title is licensed to third party
        
    Returns:
        Adjusted streaming value
    """
    if has_third_party_license:
        return base_streaming_value * (1.0 - LICENSE_CANNIBALIZATION_FACTOR)
    return base_streaming_value
