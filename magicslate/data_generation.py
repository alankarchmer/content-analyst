"""Synthetic data generation for Magic Slate.

This module creates realistic synthetic datasets for:
- Title catalog with metadata
- Engagement curves (weekly hours viewed)
- Quality and buzz metrics
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple


# Set random seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


# Configuration
NUM_TITLES = 40
BRANDS = ["Marvel", "Star Wars", "Pixar", "Disney Animation", "FX", "General Entertainment", "National Geographic"]
GENRES = ["Animation", "Kids", "Drama", "Comedy", "Reality", "Docuseries", "Action", "Sci-Fi", "Fantasy"]
CONTENT_TYPES = ["Film", "Series"]
PLATFORMS = ["Disney+", "Hulu"]


def generate_title_names(n: int) -> list:
    """Generate realistic-sounding title names."""
    prefixes = ["Star", "Kingdom", "Chronicles", "Tales", "Legend", "Mystery", "Secret", "Rise", "Fall", 
                "Quest", "Journey", "Dreams", "Shadows", "Light", "Dark", "Beyond", "Lost", "Found"]
    suffixes = ["Voyage", "Dreams", "Empire", "Realm", "Legends", "Heroes", "Warriors", "Guardians",
                "Chronicles", "Saga", "Adventures", "Mysteries", "Tales", "Stories", "Files", "Archives"]
    modifiers = ["Nova", "Prime", "Elite", "Ultimate", "Origins", "Reborn", "Awakening", "Rising",
                 "Legacy", "Destiny", "Eternal", "Infinite", "Hidden", "Forbidden"]
    
    names = []
    used_names = set()
    
    for i in range(n):
        while True:
            template = np.random.choice(["prefix_suffix", "prefix_modifier", "prefix_suffix_modifier"])
            
            if template == "prefix_suffix":
                name = f"{np.random.choice(prefixes)} {np.random.choice(suffixes)}"
            elif template == "prefix_modifier":
                name = f"{np.random.choice(prefixes)}: {np.random.choice(modifiers)}"
            else:
                name = f"{np.random.choice(prefixes)} {np.random.choice(suffixes)}: {np.random.choice(modifiers)}"
            
            if name not in used_names:
                names.append(name)
                used_names.add(name)
                break
    
    return names


def generate_titles_dataframe(n: int = NUM_TITLES) -> pd.DataFrame:
    """Generate synthetic title catalog with metadata.
    
    Args:
        n: Number of titles to generate
        
    Returns:
        DataFrame with title metadata
    """
    np.random.seed(RANDOM_SEED)
    
    titles = []
    title_names = generate_title_names(n)
    
    for i, name in enumerate(title_names):
        title_id = f"T{i+1:04d}"
        brand = np.random.choice(BRANDS)
        content_type = np.random.choice(CONTENT_TYPES, p=[0.3, 0.7])  # More series than films
        
        # Platform distribution based on brand
        if brand in ["Marvel", "Star Wars", "Pixar", "Disney Animation"]:
            platform = "Disney+"
        elif brand == "FX":
            platform = "Hulu"
        else:
            platform = np.random.choice(PLATFORMS)
        
        # Genre based on brand
        if brand == "Pixar":
            genre = "Animation"
        elif brand == "Marvel":
            genre = np.random.choice(["Action", "Sci-Fi", "Fantasy"])
        elif brand == "Star Wars":
            genre = np.random.choice(["Sci-Fi", "Action", "Fantasy"])
        elif brand == "National Geographic":
            genre = "Docuseries"
        else:
            genre = np.random.choice(GENRES)
        
        # Budget tier (brand influences this)
        if brand in ["Marvel", "Star Wars"]:
            budget_tier = np.random.choice(["Medium", "High"], p=[0.3, 0.7])
        elif brand == "Pixar":
            budget_tier = np.random.choice(["Medium", "High"], p=[0.5, 0.5])
        else:
            budget_tier = np.random.choice(["Low", "Medium", "High"], p=[0.4, 0.4, 0.2])
        
        # Budget amounts (in millions)
        if content_type == "Film":
            if budget_tier == "Low":
                production_budget = np.random.uniform(5, 20)
            elif budget_tier == "Medium":
                production_budget = np.random.uniform(20, 80)
            else:
                production_budget = np.random.uniform(80, 200)
        else:  # Series
            if budget_tier == "Low":
                production_budget = np.random.uniform(2, 8)
            elif budget_tier == "Medium":
                production_budget = np.random.uniform(8, 30)
            else:
                production_budget = np.random.uniform(30, 100)
        
        # Marketing spend (20-60% of production)
        marketing_pct = np.random.uniform(0.2, 0.6)
        marketing_spend = production_budget * marketing_pct
        
        # Series-specific
        season_number = None
        episode_count = None
        if content_type == "Series":
            season_number = np.random.choice([1, 1, 1, 2, 2, 3])  # Weighted toward season 1
            episode_count = np.random.randint(6, 13)
        
        # Release dates (within last 2 years)
        base_date = datetime.now() - timedelta(days=np.random.randint(0, 730))
        
        # Theatrical release (only some films)
        theatrical_date = None
        pvod_date = None
        if content_type == "Film" and budget_tier in ["Medium", "High"] and np.random.rand() > 0.3:
            theatrical_date = base_date
            if np.random.rand() > 0.5:  # Some have PVOD
                pvod_date = theatrical_date + timedelta(days=np.random.randint(17, 45))
        
        # Streaming release
        if theatrical_date:
            streaming_offset = np.random.randint(45, 120)
            streaming_date = theatrical_date + timedelta(days=streaming_offset)
        else:
            streaming_date = base_date
        
        disney_plus_date = streaming_date if platform == "Disney+" else None
        hulu_date = streaming_date if platform == "Hulu" else None
        
        titles.append({
            "title_id": title_id,
            "title_name": name,
            "brand": brand,
            "platform_primary": platform,
            "genre": genre,
            "content_type": content_type,
            "season_number": season_number,
            "episode_count": episode_count,
            "release_theatrical_date": theatrical_date.strftime("%Y-%m-%d") if theatrical_date else None,
            "release_pvod_date": pvod_date.strftime("%Y-%m-%d") if pvod_date else None,
            "release_disney_plus_date": disney_plus_date.strftime("%Y-%m-%d") if disney_plus_date else None,
            "release_hulu_date": hulu_date.strftime("%Y-%m-%d") if hulu_date else None,
            "production_budget_tier": budget_tier,
            "estimated_production_budget": production_budget,
            "estimated_marketing_spend": marketing_spend,
        })
    
    return pd.DataFrame(titles)


def generate_engagement_curve(
    title_id: str,
    brand: str,
    content_type: str,
    budget_tier: str,
    quality_latent: float,
    weeks: int = 24
) -> pd.DataFrame:
    """Generate synthetic engagement curve for a title.
    
    Args:
        title_id: Title identifier
        brand: Title brand
        content_type: "Film" or "Series"
        budget_tier: "Low", "Medium", or "High"
        quality_latent: Underlying quality factor (affects peak and longevity)
        weeks: Number of weeks to simulate
        
    Returns:
        DataFrame with weekly engagement metrics
    """
    # Base peak hours influenced by multiple factors
    brand_multipliers = {
        "Marvel": 1.8,
        "Star Wars": 1.7,
        "Pixar": 1.5,
        "Disney Animation": 1.3,
        "FX": 1.1,
        "General Entertainment": 1.0,
        "National Geographic": 0.8,
    }
    
    budget_multipliers = {
        "Low": 0.5,
        "Medium": 1.0,
        "High": 2.0,
    }
    
    content_multipliers = {
        "Film": 1.2,
        "Series": 1.0,
    }
    
    base_peak = 10_000_000  # 10M hours base
    peak_hours = base_peak * brand_multipliers.get(brand, 1.0) * \
                 budget_multipliers.get(budget_tier, 1.0) * \
                 content_multipliers.get(content_type, 1.0) * \
                 (0.5 + quality_latent)  # Quality factor
    
    # Add noise
    peak_hours *= np.random.uniform(0.7, 1.3)
    
    # Peak timing (week 1-3 typically)
    peak_week = np.random.randint(1, 4)
    
    # Generate curve
    engagement_data = []
    
    for week in range(weeks):
        if week < peak_week:
            # Ramp up to peak
            hours = peak_hours * (week / peak_week) * np.random.uniform(0.8, 1.2)
        elif week == peak_week:
            hours = peak_hours
        else:
            # Decay after peak
            # Decay rate influenced by quality (better content has slower decay)
            decay_rate = 0.15 * (1.0 - quality_latent * 0.3)
            weeks_since_peak = week - peak_week
            hours = peak_hours * np.exp(-decay_rate * weeks_since_peak)
            hours *= np.random.uniform(0.85, 1.15)  # Add noise
        
        # Top 10 rank (inverse relationship with hours, with threshold)
        if hours > peak_hours * 0.6:
            top10_rank = np.random.randint(1, 4)
        elif hours > peak_hours * 0.3:
            top10_rank = np.random.randint(3, 8)
        elif hours > peak_hours * 0.15:
            top10_rank = np.random.randint(7, 11)
        else:
            top10_rank = None
        
        # Search index (correlated with hours but with independent noise)
        search_index = hours / 1_000_000 * np.random.uniform(0.8, 1.5)
        
        engagement_data.append({
            "title_id": title_id,
            "week_number": week,
            "proxy_hours_viewed": max(0, hours),
            "top10_rank": top10_rank,
            "search_index": search_index,
        })
    
    return pd.DataFrame(engagement_data)


def generate_title_quality(
    title_id: str,
    brand: str,
    budget_tier: str,
    quality_latent: float
) -> dict:
    """Generate quality and buzz metrics for a title.
    
    Args:
        title_id: Title identifier
        brand: Title brand
        budget_tier: Budget tier
        quality_latent: Underlying quality factor
        
    Returns:
        Dictionary with quality metrics
    """
    # Quality scores correlated with latent quality
    base_quality = 50 + quality_latent * 40  # Map 0-1 to 50-90
    
    # Brand and budget influence
    brand_bonus = {"Marvel": 5, "Star Wars": 5, "Pixar": 10}.get(brand, 0)
    budget_bonus = {"Low": -5, "Medium": 0, "High": 5}.get(budget_tier, 0)
    
    # Critic score (0-100)
    critic_score = base_quality + brand_bonus + budget_bonus + np.random.normal(0, 10)
    critic_score = np.clip(critic_score, 20, 95)
    
    # Audience score (typically higher than critics, more variance)
    audience_score = critic_score + np.random.normal(5, 8)
    audience_score = np.clip(audience_score, 25, 98)
    
    # IMDB rating (0-10, scaled)
    imdb_rating = critic_score / 10.0 + np.random.normal(0, 0.5)
    imdb_rating = np.clip(imdb_rating, 3.0, 9.5)
    
    # Buzz score (correlated with quality and budget)
    buzz_base = quality_latent * 60 + 20
    buzz_budget_bonus = {"Low": 0, "Medium": 10, "High": 20}.get(budget_tier, 0)
    buzz_score = buzz_base + buzz_budget_bonus + np.random.normal(0, 12)
    buzz_score = np.clip(buzz_score, 10, 95)
    
    return {
        "title_id": title_id,
        "critic_score": round(critic_score, 1),
        "audience_score": round(audience_score, 1),
        "imdb_rating": round(imdb_rating, 1),
        "buzz_score": round(buzz_score, 1),
    }


def generate_all_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate complete synthetic dataset.
    
    Returns:
        Tuple of (titles_df, engagement_df, quality_df)
    """
    np.random.seed(RANDOM_SEED)
    
    # Generate titles
    titles_df = generate_titles_dataframe(NUM_TITLES)
    
    # Generate quality latent variables for each title
    quality_latents = np.random.beta(5, 3, NUM_TITLES)  # Skewed toward higher quality
    
    # Generate engagement curves
    all_engagement = []
    quality_records = []
    
    for idx, row in titles_df.iterrows():
        quality_latent = quality_latents[idx]
        
        # Generate engagement
        engagement_df = generate_engagement_curve(
            title_id=row["title_id"],
            brand=row["brand"],
            content_type=row["content_type"],
            budget_tier=row["production_budget_tier"],
            quality_latent=quality_latent,
            weeks=24
        )
        all_engagement.append(engagement_df)
        
        # Generate quality
        quality = generate_title_quality(
            title_id=row["title_id"],
            brand=row["brand"],
            budget_tier=row["production_budget_tier"],
            quality_latent=quality_latent
        )
        quality_records.append(quality)
    
    engagement_df = pd.concat(all_engagement, ignore_index=True)
    quality_df = pd.DataFrame(quality_records)
    
    return titles_df, engagement_df, quality_df


def save_synthetic_data(data_dir: str = "data") -> None:
    """Generate and save synthetic data to CSV files.
    
    Args:
        data_dir: Directory to save CSV files
    """
    import os
    
    os.makedirs(data_dir, exist_ok=True)
    
    titles_df, engagement_df, quality_df = generate_all_data()
    
    titles_df.to_csv(f"{data_dir}/titles.csv", index=False)
    engagement_df.to_csv(f"{data_dir}/title_engagement_proxies.csv", index=False)
    quality_df.to_csv(f"{data_dir}/title_quality.csv", index=False)
    
    print(f"✓ Generated {len(titles_df)} titles")
    print(f"✓ Generated {len(engagement_df)} engagement records")
    print(f"✓ Generated {len(quality_df)} quality records")
    print(f"✓ Data saved to {data_dir}/")


if __name__ == "__main__":
    save_synthetic_data()
