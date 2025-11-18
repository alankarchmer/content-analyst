"""Greenlight forecasting for new title concepts in Magic Slate.

This module provides predictive analytics for greenlight decisions by:
- Finding comparable titles
- Building performance distributions
- Generating bear/base/bull scenarios
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from .data_models import NewTitleConcept
from .title_scorecard import compute_all_scorecards


def find_comparable_titles(
    concept: NewTitleConcept,
    df_titles: pd.DataFrame,
    df_scorecards: pd.DataFrame,
    top_n: int = 5
) -> pd.DataFrame:
    """Find comparable titles for a new concept.
    
    Uses a scoring system to find the most similar titles based on:
    - Brand match
    - Genre match
    - Content type match
    - Budget tier similarity
    
    Args:
        concept: NewTitleConcept describing the proposed title
        df_titles: DataFrame with title metadata
        df_scorecards: DataFrame with computed scorecards
        top_n: Number of comps to return
        
    Returns:
        DataFrame with top N comparable titles
    """
    # Merge titles with scorecards
    df = df_titles.merge(
        df_scorecards[["title_id", "total_hours_viewed", "total_value", "roi", "classification"]],
        on="title_id",
        how="inner"
    )
    
    # Compute similarity score for each title
    scores = []
    
    for idx, row in df.iterrows():
        score = 0
        
        # Brand match (highest weight)
        if row["brand"] == concept.brand:
            score += 5
        
        # Genre match
        if row["genre"] == concept.genre:
            score += 3
        
        # Content type match
        if row["content_type"] == concept.content_type:
            score += 4
        
        # Budget tier similarity
        concept_budget_millions = concept.production_budget_estimate
        if concept_budget_millions < 20:
            concept_tier = "Low"
        elif concept_budget_millions < 80:
            concept_tier = "Medium"
        else:
            concept_tier = "High"
        
        if row["production_budget_tier"] == concept_tier:
            score += 3
        elif abs(["Low", "Medium", "High"].index(row["production_budget_tier"]) - 
                ["Low", "Medium", "High"].index(concept_tier)) == 1:
            score += 1
        
        # IP familiarity proxy (franchise titles get bonus)
        if concept.ip_familiarity in ["Sequel", "Spin-off", "Franchise Core"]:
            if row["brand"] in ["Marvel", "Star Wars", "Pixar"]:
                score += 2
        
        scores.append(score)
    
    df["similarity_score"] = scores
    
    # Return top N
    comps = df.nlargest(top_n, "similarity_score").copy()
    
    return comps


def compute_performance_distribution(
    comps: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """Compute performance distribution statistics from comparables.
    
    Args:
        comps: DataFrame with comparable titles
        
    Returns:
        Dict with mean and std for key metrics
    """
    metrics = ["total_hours_viewed", "total_value", "roi"]
    
    distributions = {}
    
    for metric in metrics:
        if metric in comps.columns and not comps[metric].empty:
            distributions[metric] = {
                "mean": comps[metric].mean(),
                "std": comps[metric].std(),
                "min": comps[metric].min(),
                "max": comps[metric].max(),
            }
        else:
            distributions[metric] = {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }
    
    return distributions


def generate_scenarios(
    concept: NewTitleConcept,
    distributions: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """Generate bear/base/bull forecast scenarios.
    
    Args:
        concept: NewTitleConcept with concept details
        distributions: Performance distributions from comps
        
    Returns:
        Dict with scenario forecasts
    """
    scenarios = {}
    
    # Base scenario: mean of comps
    base_hours = distributions["total_hours_viewed"]["mean"]
    base_value = distributions["total_value"]["mean"]
    base_roi = distributions["roi"]["mean"]
    
    # Apply concept-specific adjustments
    # Star power and buzz modulate performance
    star_factor = 0.8 + (concept.star_power_score / 5.0) * 0.4  # Range: 0.8 to 1.2
    buzz_factor = 0.8 + (concept.buzz_potential_score / 100.0) * 0.4  # Range: 0.8 to 1.2
    concept_multiplier = (star_factor + buzz_factor) / 2
    
    base_hours *= concept_multiplier
    base_value *= concept_multiplier
    
    # Recalculate ROI with actual cost
    total_cost = concept.production_budget_estimate * 1_000_000 + concept.marketing_spend_estimate * 1_000_000
    base_roi = (base_value - total_cost) / total_cost if total_cost > 0 else 0.0
    
    scenarios["base"] = {
        "total_hours_viewed": base_hours,
        "total_value": base_value,
        "total_cost": total_cost,
        "roi": base_roi,
    }
    
    # Bear scenario: mean - 1 std, adjusted down
    bear_hours = distributions["total_hours_viewed"]["mean"] - distributions["total_hours_viewed"]["std"]
    bear_hours = max(bear_hours, distributions["total_hours_viewed"]["min"])
    bear_hours *= concept_multiplier * 0.7  # Additional pessimism
    
    bear_value = distributions["total_value"]["mean"] - distributions["total_value"]["std"]
    bear_value = max(bear_value, distributions["total_value"]["min"])
    bear_value *= concept_multiplier * 0.7
    
    bear_roi = (bear_value - total_cost) / total_cost if total_cost > 0 else 0.0
    
    scenarios["bear"] = {
        "total_hours_viewed": bear_hours,
        "total_value": bear_value,
        "total_cost": total_cost,
        "roi": bear_roi,
    }
    
    # Bull scenario: mean + 1 std, adjusted up
    bull_hours = distributions["total_hours_viewed"]["mean"] + distributions["total_hours_viewed"]["std"]
    bull_hours = min(bull_hours * 1.3, distributions["total_hours_viewed"]["max"] * 1.2)
    bull_hours *= concept_multiplier * 1.3  # Additional optimism
    
    bull_value = distributions["total_value"]["mean"] + distributions["total_value"]["std"]
    bull_value = min(bull_value * 1.3, distributions["total_value"]["max"] * 1.2)
    bull_value *= concept_multiplier * 1.3
    
    bull_roi = (bull_value - total_cost) / total_cost if total_cost > 0 else 0.0
    
    scenarios["bull"] = {
        "total_hours_viewed": bull_hours,
        "total_value": bull_value,
        "total_cost": total_cost,
        "roi": bull_roi,
    }
    
    return scenarios


def forecast_new_title(
    concept: NewTitleConcept,
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame
) -> Dict:
    """Generate complete forecast for a new title concept.
    
    This is the main forecasting function that:
    1. Finds comparable titles
    2. Derives performance distributions
    3. Generates bear/base/bull scenarios
    4. Provides recommendation
    
    Args:
        concept: NewTitleConcept describing the proposed title
        df_titles: DataFrame with title metadata
        df_engagement: DataFrame with engagement data
        df_quality: DataFrame with quality scores
        
    Returns:
        Dict with forecast results including scenarios, comps, and recommendation
    """
    # Compute scorecards if not already done
    df_scorecards = compute_all_scorecards(df_titles, df_engagement, df_quality)
    
    # Find comps
    comps = find_comparable_titles(concept, df_titles, df_scorecards, top_n=5)
    
    if comps.empty:
        return {
            "concept_name": concept.concept_name,
            "comps": [],
            "scenarios": {},
            "recommendation": "Unable to generate forecast: no comparable titles found.",
        }
    
    # Compute distributions
    distributions = compute_performance_distribution(comps)
    
    # Generate scenarios
    scenarios = generate_scenarios(concept, distributions)
    
    # Generate recommendation
    recommendation = generate_recommendation(concept, scenarios, comps)
    
    # Format comps for output
    comps_list = []
    for _, row in comps.iterrows():
        comps_list.append({
            "title_name": row["title_name"],
            "brand": row["brand"],
            "genre": row["genre"],
            "content_type": row["content_type"],
            "similarity_score": row["similarity_score"],
            "total_hours_viewed": row["total_hours_viewed"],
            "total_value": row["total_value"],
            "roi": row["roi"],
        })
    
    return {
        "concept_name": concept.concept_name,
        "comps": comps_list,
        "distributions": distributions,
        "scenarios": scenarios,
        "recommendation": recommendation,
    }


def generate_recommendation(
    concept: NewTitleConcept,
    scenarios: Dict[str, Dict[str, float]],
    comps: pd.DataFrame
) -> str:
    """Generate greenlight recommendation narrative.
    
    Args:
        concept: NewTitleConcept
        scenarios: Dict with bear/base/bull scenarios
        comps: DataFrame with comparable titles
        
    Returns:
        Recommendation narrative string
    """
    base = scenarios.get("base", {})
    bear = scenarios.get("bear", {})
    bull = scenarios.get("bull", {})
    
    if not base:
        return "Insufficient data to generate recommendation."
    
    narrative = []
    
    # Summary
    narrative.append(f"**Greenlight Forecast for '{concept.concept_name}'**\n\n")
    
    # Comparable titles
    narrative.append(f"Based on analysis of **{len(comps)} comparable titles**, ")
    narrative.append(f"including {', '.join(comps['title_name'].head(3).tolist())}.\n\n")
    
    # Scenario summary
    narrative.append("**Scenario Summary**:\n")
    narrative.append(f"- **Bear Case**: {bear.get('roi', 0)*100:.0f}% ROI | ")
    narrative.append(f"${bear.get('total_value', 0)/1_000_000:.1f}M value\n")
    narrative.append(f"- **Base Case**: {base.get('roi', 0)*100:.0f}% ROI | ")
    narrative.append(f"${base.get('total_value', 0)/1_000_000:.1f}M value\n")
    narrative.append(f"- **Bull Case**: {bull.get('roi', 0)*100:.0f}% ROI | ")
    narrative.append(f"${bull.get('total_value', 0)/1_000_000:.1f}M value\n\n")
    
    # Recommendation logic
    base_roi = base.get("roi", 0)
    bear_roi = bear.get("roi", 0)
    
    narrative.append("**Recommendation**: ")
    
    if base_roi > 1.0 and bear_roi > 0.3:
        recommendation_text = "**STRONG GREENLIGHT**"
        reasoning = "Base case shows excellent returns with limited downside risk."
    elif base_roi > 0.5 and bear_roi > 0:
        recommendation_text = "**GREENLIGHT**"
        reasoning = "Solid projected returns with manageable downside."
    elif base_roi > 0.2:
        recommendation_text = "**CONDITIONAL GREENLIGHT**"
        reasoning = "Moderate returns projected. Consider budget optimization or talent upgrades."
    elif base_roi > 0:
        recommendation_text = "**MARGINAL**"
        reasoning = "Returns are positive but limited. Recommend further development or budget reduction."
    else:
        recommendation_text = "**PASS**"
        reasoning = "Projected returns do not justify investment at current budget level."
    
    narrative.append(f"{recommendation_text}\n\n")
    narrative.append(f"*{reasoning}*\n\n")
    
    # Key factors
    narrative.append("**Key Factors**:\n")
    
    if concept.ip_familiarity in ["Sequel", "Franchise Core"]:
        narrative.append("- ✓ Strong IP foundation reduces risk\n")
    elif concept.ip_familiarity == "New IP":
        narrative.append("- ⚠ New IP carries higher execution risk\n")
    
    if concept.star_power_score >= 4:
        narrative.append("- ✓ Strong talent attachment\n")
    elif concept.star_power_score <= 2:
        narrative.append("- ⚠ Limited star power may impact marketing\n")
    
    if concept.buzz_potential_score >= 70:
        narrative.append("- ✓ High buzz potential\n")
    elif concept.buzz_potential_score <= 40:
        narrative.append("- ⚠ Lower buzz potential may require marketing investment\n")
    
    # Comp performance context
    avg_comp_roi = comps["roi"].mean() if "roi" in comps.columns else 0
    if avg_comp_roi > 0.8:
        narrative.append(f"- ✓ Comps show strong average ROI of {avg_comp_roi*100:.0f}%\n")
    elif avg_comp_roi < 0.3:
        narrative.append(f"- ⚠ Comps show modest average ROI of {avg_comp_roi*100:.0f}%\n")
    
    return "".join(narrative)


def scenario_sensitivity_analysis(
    concept: NewTitleConcept,
    scenarios: Dict[str, Dict[str, float]],
    cost_adjustments: List[float] = [-0.2, -0.1, 0, 0.1, 0.2]
) -> pd.DataFrame:
    """Perform sensitivity analysis on cost assumptions.
    
    Args:
        concept: NewTitleConcept
        scenarios: Dict with forecast scenarios
        cost_adjustments: List of cost adjustment factors (e.g., -0.2 = 20% reduction)
        
    Returns:
        DataFrame with sensitivity analysis results
    """
    results = []
    
    base_scenario = scenarios.get("base", {})
    base_value = base_scenario.get("total_value", 0)
    base_cost = base_scenario.get("total_cost", 0)
    
    for adjustment in cost_adjustments:
        adjusted_cost = base_cost * (1 + adjustment)
        adjusted_roi = (base_value - adjusted_cost) / adjusted_cost if adjusted_cost > 0 else 0
        
        results.append({
            "cost_adjustment": f"{adjustment*100:+.0f}%",
            "adjusted_cost": adjusted_cost,
            "projected_value": base_value,
            "roi": adjusted_roi,
        })
    
    return pd.DataFrame(results)
