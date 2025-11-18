"""Data models and schemas for Magic Slate."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class WindowingScenario:
    """Configuration for a windowing strategy scenario."""
    scenario_name: str
    title_id: str
    theatrical_window_days: int
    pvod_window_days: int
    disney_plus_offset_days: int
    hulu_offset_days: int
    third_party_license_start_days: int
    third_party_license_fee: float


@dataclass
class NewTitleConcept:
    """Specification for a greenlight title concept."""
    concept_name: str
    brand: str
    genre: str
    content_type: str  # "Film" or "Series"
    season_number: Optional[int] = None
    episode_count: Optional[int] = None
    production_budget_estimate: float = 0.0
    marketing_spend_estimate: float = 0.0
    ip_familiarity: str = "New IP"  # "New IP", "Sequel", "Spin-off", "Franchise Core"
    star_power_score: int = 3  # 1-5
    buzz_potential_score: int = 50  # 0-100


@dataclass
class TitleScorecard:
    """Complete performance scorecard for a title."""
    title_id: str
    title_name: str
    brand: str
    genre: str
    platform_primary: str
    content_type: str
    
    # Engagement metrics
    total_hours_viewed: float
    peak_hours: float
    peak_week: int
    long_tail_share: float
    decay_rate: float
    
    # Quality metrics
    critic_score: float
    audience_score: float
    imdb_rating: float
    buzz_score: float
    
    # Financial metrics
    production_budget: float
    marketing_spend: float
    total_cost: float
    streaming_value: float
    ad_value: float
    theatrical_value: float
    pvod_value: float
    total_value: float
    roi: float
    cost_per_hour_viewed: float
    
    # Classification
    classification: str
