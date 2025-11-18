"""Excel export functionality for Magic Slate.

This module creates downloadable Excel workbooks with comprehensive
analytics data and reports.
"""

import pandas as pd
from io import BytesIO
from typing import Dict, Optional
from . import assumptions as asmp
from .title_scorecard import compute_all_scorecards
from .portfolio_dashboard import (
    compute_portfolio_by_brand,
    compute_portfolio_by_genre,
    compute_portfolio_by_platform,
    compute_concentration_metrics,
    compute_classification_distribution,
)


def create_assumptions_sheet() -> pd.DataFrame:
    """Create a DataFrame with key assumptions for export.
    
    Returns:
        DataFrame with assumption parameters
    """
    assumptions_data = [
        {"Category": "Streaming ARPU", "Parameter": "Disney+ ARPU (monthly)", 
         "Value": f"${asmp.DISNEY_PLUS_ARPU:.2f}", "Unit": "USD"},
        {"Category": "Streaming ARPU", "Parameter": "Hulu ARPU (monthly)", 
         "Value": f"${asmp.HULU_ARPU:.2f}", "Unit": "USD"},
        {"Category": "Ad Revenue", "Parameter": "Hulu Ad ARPU per Hour", 
         "Value": f"${asmp.HULU_AD_ARPU_PER_HOUR:.2f}", "Unit": "USD"},
        {"Category": "Engagement Conversion", "Parameter": "Acquisition Base (per 1M hours)", 
         "Value": str(asmp.ACQUISITION_CONVERSION_BASE), "Unit": "subscribers"},
        {"Category": "Engagement Conversion", "Parameter": "Retention Base (per 1M hours)", 
         "Value": str(asmp.RETENTION_IMPACT_BASE), "Unit": "subscriber-months"},
        {"Category": "Windowing", "Parameter": "PVOD Cannibalization Factor", 
         "Value": f"{asmp.PVOD_CANNIBALIZATION_FACTOR:.0%}", "Unit": "percentage"},
        {"Category": "Windowing", "Parameter": "License Cannibalization Factor", 
         "Value": f"{asmp.LICENSE_CANNIBALIZATION_FACTOR:.0%}", "Unit": "percentage"},
        {"Category": "Financial", "Parameter": "Discount Rate", 
         "Value": f"{asmp.DISCOUNT_RATE:.0%}", "Unit": "annual"},
        {"Category": "Theatrical", "Parameter": "Low Budget Multiplier", 
         "Value": str(asmp.THEATRICAL_MULTIPLIER_BY_TIER["Low"]), "Unit": "multiple of budget"},
        {"Category": "Theatrical", "Parameter": "Medium Budget Multiplier", 
         "Value": str(asmp.THEATRICAL_MULTIPLIER_BY_TIER["Medium"]), "Unit": "multiple of budget"},
        {"Category": "Theatrical", "Parameter": "High Budget Multiplier", 
         "Value": str(asmp.THEATRICAL_MULTIPLIER_BY_TIER["High"]), "Unit": "multiple of budget"},
    ]
    
    return pd.DataFrame(assumptions_data)


def export_to_excel(
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame,
    df_scorecards: Optional[pd.DataFrame] = None
) -> BytesIO:
    """Export comprehensive analytics to Excel workbook.
    
    Creates a multi-sheet Excel workbook with:
    - Assumptions
    - Title catalog
    - Engagement data (sample)
    - Quality metrics
    - Title scorecards
    - Portfolio summaries by brand, genre, platform
    - Concentration analysis
    
    Args:
        df_titles: Title metadata DataFrame
        df_engagement: Engagement data DataFrame
        df_quality: Quality metrics DataFrame
        df_scorecards: Pre-computed scorecards (optional, will compute if not provided)
        
    Returns:
        BytesIO object containing Excel workbook
    """
    # Compute scorecards if not provided
    if df_scorecards is None:
        df_scorecards = compute_all_scorecards(df_titles, df_engagement, df_quality)
    
    # Create BytesIO buffer
    output = BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        currency_format = workbook.add_format({'num_format': '$#,##0'})
        percent_format = workbook.add_format({'num_format': '0.0%'})
        number_format = workbook.add_format({'num_format': '#,##0'})
        
        # Sheet 1: Assumptions
        df_assumptions = create_assumptions_sheet()
        df_assumptions.to_excel(writer, sheet_name='Assumptions', index=False)
        
        # Sheet 2: Title Catalog
        df_titles_export = df_titles.copy()
        df_titles_export.to_excel(writer, sheet_name='Title Catalog', index=False)
        
        # Sheet 3: Engagement Data (sample - first 1000 rows to keep file size reasonable)
        df_engagement_sample = df_engagement.head(1000).copy()
        df_engagement_sample.to_excel(writer, sheet_name='Engagement Sample', index=False)
        
        # Sheet 4: Quality Metrics
        df_quality.to_excel(writer, sheet_name='Quality Metrics', index=False)
        
        # Sheet 5: Title Scorecards
        df_scorecards_export = df_scorecards.copy()
        # Format currency columns
        currency_cols = ['production_budget', 'marketing_spend', 'total_cost', 
                        'streaming_value', 'ad_value', 'theatrical_value', 
                        'pvod_value', 'total_value', 'cost_per_hour_viewed']
        
        df_scorecards_export.to_excel(writer, sheet_name='Title Scorecards', index=False)
        worksheet = writer.sheets['Title Scorecards']
        
        # Apply currency format to specific columns
        for col_name in currency_cols:
            if col_name in df_scorecards_export.columns:
                col_idx = df_scorecards_export.columns.get_loc(col_name)
                worksheet.set_column(col_idx, col_idx, 15, currency_format)
        
        # Apply percent format to ROI
        if 'roi' in df_scorecards_export.columns:
            roi_idx = df_scorecards_export.columns.get_loc('roi')
            worksheet.set_column(roi_idx, roi_idx, 10, percent_format)
        
        # Sheet 6: Portfolio by Brand
        df_brand = compute_portfolio_by_brand(df_scorecards)
        df_brand.to_excel(writer, sheet_name='Portfolio by Brand', index=False)
        
        # Sheet 7: Portfolio by Genre
        df_genre = compute_portfolio_by_genre(df_scorecards)
        df_genre.to_excel(writer, sheet_name='Portfolio by Genre', index=False)
        
        # Sheet 8: Portfolio by Platform
        df_platform = compute_portfolio_by_platform(df_scorecards)
        df_platform.to_excel(writer, sheet_name='Portfolio by Platform', index=False)
        
        # Sheet 9: Classification Distribution
        df_classification = compute_classification_distribution(df_scorecards)
        if not df_classification.empty:
            df_classification.to_excel(writer, sheet_name='Classification', index=False)
        
        # Sheet 10: Top Titles
        concentration_metrics = compute_concentration_metrics(df_scorecards, top_n=20)
        if concentration_metrics.get("top_titles"):
            df_top = pd.DataFrame(concentration_metrics["top_titles"])
            df_top.to_excel(writer, sheet_name='Top 20 Titles', index=False)
            
            # Add summary metrics at the top
            summary_data = {
                "Metric": ["Total Portfolio Value", "Top 20 Value", "Top 20 Share", "HHI"],
                "Value": [
                    concentration_metrics["total_value"],
                    concentration_metrics["top_n_value"],
                    concentration_metrics["top_n_share"],
                    concentration_metrics["hhi"]
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Concentration Summary', index=False)
    
    # Reset buffer position
    output.seek(0)
    
    return output


def export_title_report(
    title_id: str,
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame,
    scorecard_dict: Dict
) -> BytesIO:
    """Export detailed report for a single title.
    
    Args:
        title_id: Title identifier
        df_titles: Title metadata DataFrame
        df_engagement: Engagement data DataFrame
        df_quality: Quality metrics DataFrame
        scorecard_dict: Dict with scorecard metrics
        
    Returns:
        BytesIO object containing Excel workbook
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Title Summary
        summary_data = {
            "Metric": [
                "Title Name", "Brand", "Genre", "Platform", "Content Type",
                "Total Hours Viewed", "Peak Hours", "Peak Week",
                "Production Budget", "Marketing Spend", "Total Cost",
                "Streaming Value", "Ad Value", "Theatrical Value", "PVOD Value",
                "Total Value", "ROI", "Cost per Hour",
                "Critic Score", "Audience Score", "IMDB Rating", "Buzz Score",
                "Classification"
            ],
            "Value": [
                scorecard_dict.get("title_name", ""),
                scorecard_dict.get("brand", ""),
                scorecard_dict.get("genre", ""),
                scorecard_dict.get("platform_primary", ""),
                scorecard_dict.get("content_type", ""),
                scorecard_dict.get("total_hours_viewed", 0),
                scorecard_dict.get("peak_hours", 0),
                scorecard_dict.get("peak_week", 0),
                scorecard_dict.get("production_budget", 0),
                scorecard_dict.get("marketing_spend", 0),
                scorecard_dict.get("total_cost", 0),
                scorecard_dict.get("streaming_value", 0),
                scorecard_dict.get("ad_value", 0),
                scorecard_dict.get("theatrical_value", 0),
                scorecard_dict.get("pvod_value", 0),
                scorecard_dict.get("total_value", 0),
                scorecard_dict.get("roi", 0),
                scorecard_dict.get("cost_per_hour_viewed", 0),
                scorecard_dict.get("critic_score", 0),
                scorecard_dict.get("audience_score", 0),
                scorecard_dict.get("imdb_rating", 0),
                scorecard_dict.get("buzz_score", 0),
                scorecard_dict.get("classification", "")
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Title Summary', index=False)
        
        # Sheet 2: Weekly Engagement
        title_engagement = df_engagement[df_engagement["title_id"] == title_id].copy()
        title_engagement.to_excel(writer, sheet_name='Weekly Engagement', index=False)
    
    output.seek(0)
    return output
