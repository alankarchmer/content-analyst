"""Data loading utilities for Magic Slate.

This module handles loading data from CSV files or generating synthetic data
if files don't exist.
"""

import os
import pandas as pd
from typing import Tuple
from . import data_generation


DATA_DIR = "data"
TITLES_FILE = "titles.csv"
ENGAGEMENT_FILE = "title_engagement_proxies.csv"
QUALITY_FILE = "title_quality.csv"


def ensure_data_exists(data_dir: str = DATA_DIR) -> None:
    """Ensure synthetic data files exist, generating them if needed.
    
    Args:
        data_dir: Directory where data files should be stored
    """
    titles_path = os.path.join(data_dir, TITLES_FILE)
    engagement_path = os.path.join(data_dir, ENGAGEMENT_FILE)
    quality_path = os.path.join(data_dir, QUALITY_FILE)
    
    # Check if all required files exist
    files_exist = (
        os.path.exists(titles_path) and
        os.path.exists(engagement_path) and
        os.path.exists(quality_path)
    )
    
    if not files_exist:
        print("📊 Generating synthetic data...")
        data_generation.save_synthetic_data(data_dir)
        print("✓ Data generation complete!")


def load_titles(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Load title catalog data.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        DataFrame with title metadata
    """
    ensure_data_exists(data_dir)
    
    titles_path = os.path.join(data_dir, TITLES_FILE)
    df = pd.read_csv(titles_path)
    
    # Parse date columns
    date_columns = [
        "release_theatrical_date",
        "release_pvod_date",
        "release_disney_plus_date",
        "release_hulu_date",
    ]
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    return df


def load_engagement(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Load engagement data.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        DataFrame with title engagement metrics
    """
    ensure_data_exists(data_dir)
    
    engagement_path = os.path.join(data_dir, ENGAGEMENT_FILE)
    df = pd.read_csv(engagement_path)
    
    return df


def load_quality(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """Load quality metrics data.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        DataFrame with title quality scores
    """
    ensure_data_exists(data_dir)
    
    quality_path = os.path.join(data_dir, QUALITY_FILE)
    df = pd.read_csv(quality_path)
    
    return df


def load_all_data(data_dir: str = DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all datasets.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        Tuple of (titles_df, engagement_df, quality_df)
    """
    titles_df = load_titles(data_dir)
    engagement_df = load_engagement(data_dir)
    quality_df = load_quality(data_dir)
    
    return titles_df, engagement_df, quality_df


def get_title_data(
    title_id: str,
    df_titles: pd.DataFrame,
    df_engagement: pd.DataFrame,
    df_quality: pd.DataFrame
) -> Tuple[pd.Series, pd.DataFrame, pd.Series]:
    """Get all data for a specific title.
    
    Args:
        title_id: Title identifier
        df_titles: Titles DataFrame
        df_engagement: Engagement DataFrame
        df_quality: Quality DataFrame
        
    Returns:
        Tuple of (title_row, engagement_df, quality_row)
    """
    title_row = df_titles[df_titles["title_id"] == title_id].iloc[0]
    engagement_df = df_engagement[df_engagement["title_id"] == title_id].copy()
    quality_row = df_quality[df_quality["title_id"] == title_id].iloc[0]
    
    return title_row, engagement_df, quality_row


def refresh_data(data_dir: str = DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Force regeneration of synthetic data.
    
    Args:
        data_dir: Directory to save data files
        
    Returns:
        Tuple of (titles_df, engagement_df, quality_df)
    """
    print("🔄 Regenerating synthetic data...")
    data_generation.save_synthetic_data(data_dir)
    print("✓ Data regeneration complete!")
    
    return load_all_data(data_dir)
