"""Windowing and licensing scenario simulator for Magic Slate.

This module simulates different release window strategies and their
financial impact on title performance.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from .data_models import WindowingScenario
from . import assumptions as asmp
from . import metrics as met


def simulate_windowing_scenarios(
    title_id: str,
    scenarios: List[WindowingScenario],
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame
) -> pd.DataFrame:
    """Simulate multiple windowing scenarios for a title.
    
    This function models how different release strategies affect revenue
    across theatrical, PVOD, streaming, and licensing windows.
    
    Args:
        title_id: Title identifier
        scenarios: List of WindowingScenario objects to simulate
        df_titles: DataFrame with title metadata
        df_engagement: DataFrame with engagement data
        df_quality: DataFrame with quality scores
        
    Returns:
        DataFrame with one row per scenario and value components
    """
    # Get title data
    title_row = df_titles[df_titles["title_id"] == title_id].iloc[0]
    title_engagement = df_engagement[df_engagement["title_id"] == title_id].copy()
    quality_row = df_quality[df_quality["title_id"] == title_id].iloc[0]
    
    title_metadata = title_row.to_dict()
    quality_dict = quality_row.to_dict()
    
    results = []
    
    for scenario in scenarios:
        # Validate scenario is for this title
        if scenario.title_id != title_id:
            continue
        
        # 1. Theatrical Revenue
        theatrical_value = 0.0
        if title_row["content_type"] == "Film":
            theatrical_value = asmp.estimate_theatrical_revenue(
                title_metadata=title_metadata,
                quality_scores=quality_dict
            )
        
        # 2. PVOD Revenue
        pvod_value = 0.0
        if theatrical_value > 0 and scenario.pvod_window_days > 0:
            # PVOD value depends on theatrical performance and streaming window
            streaming_offset = max(
                scenario.disney_plus_offset_days,
                scenario.hulu_offset_days
            )
            
            pvod_value = asmp.estimate_pvod_revenue(
                theatrical_revenue=theatrical_value,
                quality_scores=quality_dict,
                streaming_window_days=streaming_offset
            )
        
        # 3. Streaming Value
        # Base streaming value from engagement
        total_hours = title_engagement["proxy_hours_viewed"].sum()
        platform = title_row["platform_primary"]
        
        value_metrics = met.hours_to_value_metrics(
            total_hours=total_hours,
            title_metadata=title_metadata,
            quality_scores=quality_dict,
            platform=platform
        )
        
        base_streaming_value = value_metrics["total_streaming_value"]
        ad_value = value_metrics["ad_value"]
        
        # Adjust streaming value based on window timing
        # Earlier streaming = higher initial engagement
        # Later streaming = potential engagement decay
        streaming_offset = max(
            scenario.disney_plus_offset_days,
            scenario.hulu_offset_days
        )
        
        if streaming_offset < 45:
            # Very early streaming (< 45 days) - minimal decay
            streaming_multiplier = 1.0
        elif streaming_offset < 90:
            # Standard window - slight decay
            streaming_multiplier = 0.95
        else:
            # Long window - more decay
            streaming_multiplier = 0.85 + (1.0 - min(streaming_offset / 365, 1.0)) * 0.1
        
        adjusted_streaming_value = base_streaming_value * streaming_multiplier
        
        # Apply licensing cannibalization if applicable
        has_license = scenario.third_party_license_start_days > 0
        if has_license:
            adjusted_streaming_value = asmp.apply_license_cannibalization(
                base_streaming_value=adjusted_streaming_value,
                has_third_party_license=True
            )
        
        # 4. Third-party License Revenue
        license_value = scenario.third_party_license_fee if has_license else 0.0
        
        # 5. Compute NPV across windows
        # Model cashflows over time
        cashflows = pd.Series(dtype=float)
        
        # Theatrical (immediate, week 0-12)
        if theatrical_value > 0:
            for week in range(12):
                cashflows[week] = theatrical_value / 12
        
        # PVOD (after theatrical window)
        if pvod_value > 0:
            pvod_start_week = scenario.theatrical_window_days // 7
            pvod_duration_weeks = scenario.pvod_window_days // 7
            for week in range(pvod_start_week, pvod_start_week + pvod_duration_weeks):
                cashflows[week] = pvod_value / pvod_duration_weeks
        
        # Streaming (after streaming window, over 2 years)
        streaming_start_week = streaming_offset // 7
        streaming_duration_weeks = 104  # 2 years
        for week in range(streaming_start_week, streaming_start_week + streaming_duration_weeks):
            # Decay streaming value over time
            decay_factor = np.exp(-0.05 * (week - streaming_start_week) / 52)
            weekly_value = (adjusted_streaming_value / streaming_duration_weeks) * decay_factor
            cashflows[week] = cashflows.get(week, 0.0) + weekly_value
        
        # Licensing (lump sum at license start)
        if license_value > 0:
            license_week = scenario.third_party_license_start_days // 7
            cashflows[license_week] = cashflows.get(license_week, 0.0) + license_value
        
        # Compute NPV
        total_npv = met.compute_npv(cashflows, periods_per_year=52)
        
        # Total undiscounted value
        total_value = (theatrical_value + pvod_value + 
                      adjusted_streaming_value + ad_value + license_value)
        
        results.append({
            "scenario_name": scenario.scenario_name,
            "theatrical_window_days": scenario.theatrical_window_days,
            "pvod_window_days": scenario.pvod_window_days,
            "streaming_offset_days": streaming_offset,
            "license_start_days": scenario.third_party_license_start_days,
            "theatrical_value": theatrical_value,
            "pvod_value": pvod_value,
            "streaming_value": adjusted_streaming_value,
            "ad_value": ad_value,
            "license_value": license_value,
            "total_value": total_value,
            "total_npv": total_npv,
        })
    
    return pd.DataFrame(results)


def create_default_windowing_scenarios(
    title_id: str,
    content_type: str
) -> List[WindowingScenario]:
    """Create a set of default windowing scenarios for comparison.
    
    Args:
        title_id: Title identifier
        content_type: "Film" or "Series"
        
    Returns:
        List of WindowingScenario objects
    """
    scenarios = []
    
    if content_type == "Film":
        # Scenario 1: Traditional theatrical window (90 days)
        scenarios.append(WindowingScenario(
            scenario_name="Traditional Theatrical",
            title_id=title_id,
            theatrical_window_days=90,
            pvod_window_days=45,
            disney_plus_offset_days=90,
            hulu_offset_days=90,
            third_party_license_start_days=0,
            third_party_license_fee=0.0,
        ))
        
        # Scenario 2: Short window (45 days)
        scenarios.append(WindowingScenario(
            scenario_name="Short Window",
            title_id=title_id,
            theatrical_window_days=45,
            pvod_window_days=30,
            disney_plus_offset_days=45,
            hulu_offset_days=45,
            third_party_license_start_days=0,
            third_party_license_fee=0.0,
        ))
        
        # Scenario 3: Day-and-date streaming
        scenarios.append(WindowingScenario(
            scenario_name="Day-and-Date Streaming",
            title_id=title_id,
            theatrical_window_days=0,
            pvod_window_days=0,
            disney_plus_offset_days=0,
            hulu_offset_days=0,
            third_party_license_start_days=0,
            third_party_license_fee=0.0,
        ))
        
        # Scenario 4: With third-party licensing
        scenarios.append(WindowingScenario(
            scenario_name="With Licensing Deal",
            title_id=title_id,
            theatrical_window_days=90,
            pvod_window_days=45,
            disney_plus_offset_days=90,
            hulu_offset_days=90,
            third_party_license_start_days=730,  # 2 years
            third_party_license_fee=50_000_000,  # $50M
        ))
    else:
        # Series: simpler scenarios (no theatrical)
        # Scenario 1: Exclusive streaming
        scenarios.append(WindowingScenario(
            scenario_name="Exclusive Streaming",
            title_id=title_id,
            theatrical_window_days=0,
            pvod_window_days=0,
            disney_plus_offset_days=0,
            hulu_offset_days=0,
            third_party_license_start_days=0,
            third_party_license_fee=0.0,
        ))
        
        # Scenario 2: With licensing after 1 year
        scenarios.append(WindowingScenario(
            scenario_name="License After 1 Year",
            title_id=title_id,
            theatrical_window_days=0,
            pvod_window_days=0,
            disney_plus_offset_days=0,
            hulu_offset_days=0,
            third_party_license_start_days=365,
            third_party_license_fee=30_000_000,  # $30M
        ))
    
    return scenarios


def compare_scenarios(df_scenarios: pd.DataFrame) -> str:
    """Generate narrative comparison of windowing scenarios.
    
    Args:
        df_scenarios: DataFrame with scenario results
        
    Returns:
        Narrative string comparing scenarios
    """
    if df_scenarios.empty:
        return "No scenarios to compare."
    
    # Find best scenario by NPV
    best_idx = df_scenarios["total_npv"].idxmax()
    best_scenario = df_scenarios.loc[best_idx]
    
    narrative = [
        f"**Best Scenario**: {best_scenario['scenario_name']} ",
        f"produces the highest NPV of **${best_scenario['total_npv']/1_000_000:.1f}M**.\n\n"
    ]
    
    # Value breakdown for best scenario
    narrative.append("**Value Breakdown**:\n")
    
    if best_scenario["theatrical_value"] > 0:
        pct = best_scenario["theatrical_value"] / best_scenario["total_value"] * 100
        narrative.append(f"- Theatrical: ${best_scenario['theatrical_value']/1_000_000:.1f}M ({pct:.0f}%)\n")
    
    if best_scenario["pvod_value"] > 0:
        pct = best_scenario["pvod_value"] / best_scenario["total_value"] * 100
        narrative.append(f"- PVOD: ${best_scenario['pvod_value']/1_000_000:.1f}M ({pct:.0f}%)\n")
    
    if best_scenario["streaming_value"] > 0:
        pct = best_scenario["streaming_value"] / best_scenario["total_value"] * 100
        narrative.append(f"- Streaming: ${best_scenario['streaming_value']/1_000_000:.1f}M ({pct:.0f}%)\n")
    
    if best_scenario["license_value"] > 0:
        pct = best_scenario["license_value"] / best_scenario["total_value"] * 100
        narrative.append(f"- Licensing: ${best_scenario['license_value']/1_000_000:.1f}M ({pct:.0f}%)\n")
    
    # Key insights
    narrative.append("\n**Key Insights**:\n")
    
    # Compare NPV range
    npv_range = df_scenarios["total_npv"].max() - df_scenarios["total_npv"].min()
    npv_range_pct = npv_range / df_scenarios["total_npv"].max() * 100
    
    narrative.append(f"- Window strategy can impact value by up to **{npv_range_pct:.0f}%**.\n")
    
    # Theatrical vs streaming trade-off
    if "theatrical_value" in df_scenarios.columns:
        theatrical_scenarios = df_scenarios[df_scenarios["theatrical_value"] > 0]
        if not theatrical_scenarios.empty:
            avg_theatrical_pct = (theatrical_scenarios["theatrical_value"] / 
                                 theatrical_scenarios["total_value"]).mean() * 100
            narrative.append(f"- Theatrical windows contribute an average of **{avg_theatrical_pct:.0f}%** of total value.\n")
    
    return "".join(narrative)


def compute_cashflow_timeline(
    title_id: str,
    scenario: WindowingScenario,
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame,
    periods_per_year: int = 52
) -> pd.DataFrame:
    """Compute period-by-period cashflows for a windowing scenario.
    
    Args:
        title_id: Title identifier
        scenario: WindowingScenario configuration
        df_titles: Titles DataFrame
        df_engagement: Engagement DataFrame
        df_quality: Quality DataFrame
        periods_per_year: 52 for weekly, 12 for monthly
        
    Returns:
        DataFrame with columns: period, theatrical_cf, pvod_cf, streaming_cf, 
                                ad_cf, license_cf, total_cf, cumulative_npv
    """
    # Get title data
    title_row = df_titles[df_titles["title_id"] == title_id].iloc[0]
    title_engagement = df_engagement[df_engagement["title_id"] == title_id].copy()
    quality_row = df_quality[df_quality["title_id"] == title_id].iloc[0]
    
    title_metadata = title_row.to_dict()
    quality_dict = quality_row.to_dict()
    
    # Compute values for each window
    # 1. Theatrical
    theatrical_value = 0.0
    if title_row["content_type"] == "Film":
        theatrical_value = asmp.estimate_theatrical_revenue(
            title_metadata=title_metadata,
            quality_scores=quality_dict
        )
    
    # 2. PVOD
    pvod_value = 0.0
    if theatrical_value > 0 and scenario.pvod_window_days > 0:
        streaming_offset = max(
            scenario.disney_plus_offset_days,
            scenario.hulu_offset_days
        )
        pvod_value = asmp.estimate_pvod_revenue(
            theatrical_revenue=theatrical_value,
            quality_scores=quality_dict,
            streaming_window_days=streaming_offset
        )
    
    # 3. Streaming
    total_hours = title_engagement["proxy_hours_viewed"].sum()
    platform = title_row["platform_primary"]
    
    value_metrics = met.hours_to_value_metrics(
        total_hours=total_hours,
        title_metadata=title_metadata,
        quality_scores=quality_dict,
        platform=platform
    )
    
    base_streaming_value = value_metrics["total_streaming_value"]
    ad_value = value_metrics["ad_value"]
    
    # Adjust for window timing
    streaming_offset = max(
        scenario.disney_plus_offset_days,
        scenario.hulu_offset_days
    )
    
    if streaming_offset < 45:
        streaming_multiplier = 1.0
    elif streaming_offset < 90:
        streaming_multiplier = 0.95
    else:
        streaming_multiplier = 0.85 + (1.0 - min(streaming_offset / 365, 1.0)) * 0.1
    
    adjusted_streaming_value = base_streaming_value * streaming_multiplier
    
    # Apply licensing cannibalization
    has_license = scenario.third_party_license_start_days > 0
    if has_license:
        adjusted_streaming_value = asmp.apply_license_cannibalization(
            base_streaming_value=adjusted_streaming_value,
            has_third_party_license=True
        )
    
    license_value = scenario.third_party_license_fee if has_license else 0.0
    
    # Build period-by-period cashflows
    max_periods = 260  # 5 years of weekly periods
    cashflows = []
    
    for period in range(max_periods):
        cf_theatrical = 0.0
        cf_pvod = 0.0
        cf_streaming = 0.0
        cf_ad = 0.0
        cf_license = 0.0
        
        # Theatrical (weeks 0-12)
        if theatrical_value > 0 and period < 12:
            cf_theatrical = theatrical_value / 12
        
        # PVOD (after theatrical window)
        if pvod_value > 0:
            pvod_start_period = scenario.theatrical_window_days // 7
            pvod_duration_periods = scenario.pvod_window_days // 7
            if pvod_start_period <= period < (pvod_start_period + pvod_duration_periods):
                cf_pvod = pvod_value / pvod_duration_periods
        
        # Streaming (after streaming offset, decays over 2 years)
        streaming_start_period = streaming_offset // 7
        streaming_duration = 104  # 2 years
        if streaming_start_period <= period < (streaming_start_period + streaming_duration):
            weeks_since_start = period - streaming_start_period
            decay_factor = np.exp(-0.05 * weeks_since_start / 52)
            cf_streaming = (adjusted_streaming_value / streaming_duration) * decay_factor
            cf_ad = (ad_value / streaming_duration) * decay_factor
        
        # License (lump sum at license start)
        if license_value > 0:
            license_period = scenario.third_party_license_start_days // 7
            if period == license_period:
                cf_license = license_value
        
        total_cf = cf_theatrical + cf_pvod + cf_streaming + cf_ad + cf_license
        
        cashflows.append({
            "period": period,
            "theatrical_cf": cf_theatrical,
            "pvod_cf": cf_pvod,
            "streaming_cf": cf_streaming,
            "ad_cf": cf_ad,
            "license_cf": cf_license,
            "total_cf": total_cf,
        })
    
    df_cf = pd.DataFrame(cashflows)
    
    # Compute cumulative NPV
    discount_rate_period = (1 + asmp.DISCOUNT_RATE) ** (1 / periods_per_year) - 1
    
    df_cf["discount_factor"] = 1 / ((1 + discount_rate_period) ** df_cf["period"])
    df_cf["discounted_cf"] = df_cf["total_cf"] * df_cf["discount_factor"]
    df_cf["cumulative_npv"] = df_cf["discounted_cf"].cumsum()
    
    return df_cf
