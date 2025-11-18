# 🎬 Magic Slate – Content ROI & Windowing Playbook

A comprehensive Python-powered analytics platform for streaming content planning and analysis, designed for Content Planning & Analysis teams at streaming companies.

## Overview

**Magic Slate** is a fully functional, self-contained Streamlit application that provides advanced analytics for:

- **Title-level Performance Analytics**: Deep dive into individual title metrics including engagement curves, quality scores, and financial ROI
- **Portfolio-level Insights**: Aggregate views by brand, genre, and platform to understand content strategy effectiveness
- **Windowing Strategy Simulation**: Model different release window scenarios (theatrical, PVOD, streaming, licensing) and their impact on total value
- **Greenlight Decision Support**: Forecast performance for new title concepts using comparable titles and scenario analysis

## Key Features

✨ **Fully Self-Contained**
- Generates realistic synthetic data programmatically (no manual uploads required)
- All analytics and calculations are fully implemented with real logic
- Ready to run end-to-end out of the box

🔢 **Real Analytics, No Placeholders**
- Complex engagement curve modeling with decay analysis
- Multi-window revenue modeling (theatrical, PVOD, streaming, licensing)
- NPV calculations with proper discounting
- Comparable title analysis for greenlight forecasting

📊 **Rich Interactive UI**
- 6 comprehensive Streamlit pages with interactive charts
- Filterable portfolio dashboards
- Scenario comparison tools
- Downloadable Excel reports

## Project Structure

```
/workspace/
├── data/                           # Generated CSV data files
│   ├── titles.csv
│   ├── title_engagement_proxies.csv
│   └── title_quality.csv
│
├── magicslate/                     # Core analytics backend
│   ├── __init__.py
│   ├── data_generation.py          # Synthetic data generation
│   ├── data_models.py              # Data schemas and models
│   ├── loaders.py                  # Data loading utilities
│   ├── assumptions.py              # Business assumptions & parameters
│   ├── metrics.py                  # Core calculation functions
│   ├── title_scorecard.py          # Per-title analytics
│   ├── portfolio_dashboard.py      # Portfolio-level analytics
│   ├── windowing_simulator.py      # Windowing scenarios
│   ├── greenlight_forecast.py      # Greenlight forecasting
│   └── exports.py                  # Excel export functionality
│
├── app/                            # Streamlit application
│   ├── streamlit_app.py            # Main entrypoint
│   └── pages/                      # Multi-page app
│       ├── 01_Overview.py          # Portfolio overview
│       ├── 02_Title_Explorer.py    # Individual title analytics
│       ├── 03_Portfolio_Dashboard.py  # Portfolio views
│       ├── 04_Windowing_Lab.py     # Windowing simulator
│       ├── 05_Greenlight_Studio.py # Greenlight forecasting
│       └── 06_Data_&_Assumptions.py  # Data & export
│
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **That's it!** The application will generate synthetic data automatically on first run.

## Usage

### Running the Application

From the project root directory, run:

```bash
streamlit run app/streamlit_app.py
```

The application will:
1. Automatically generate synthetic data if it doesn't exist
2. Load and cache the data
3. Compute analytics
4. Open in your default web browser (typically at `http://localhost:8501`)

### Navigating the App

The application has 6 main pages accessible from the sidebar:

#### 1. **Overview** 📊
- High-level portfolio summary
- Value by brand and genre
- Portfolio concentration analysis
- ROI distribution

#### 2. **Title Explorer** 🎬
- Select and analyze individual titles
- Engagement curves over time
- Quality metrics and reception
- Financial performance breakdown
- Classification badges

#### 3. **Portfolio Dashboard** 📊
- Filterable portfolio views
- Performance by brand, genre, platform, and classification
- Comparative analytics
- Top title identification

#### 4. **Windowing Lab** 🎞️
- Configure multiple windowing scenarios
- Compare theatrical, PVOD, streaming, and licensing strategies
- NPV analysis
- Strategic recommendations

#### 5. **Greenlight Studio** 💡
- Configure new title concepts
- Find comparable titles automatically
- Generate bear/base/bull forecasts
- Get greenlight recommendations
- Cost sensitivity analysis

#### 6. **Data & Assumptions** 📁
- View raw data
- Review business assumptions
- Export to Excel
- Regenerate synthetic data

## Synthetic Data

The application generates realistic synthetic data including:

- **40 titles** with diverse metadata (brand, genre, platform, budget tier)
- **Engagement curves** with realistic decay patterns over 24 weeks
- **Quality scores** (critic, audience, IMDB, buzz) correlated with performance
- **Financial metrics** based on parametric models

Data generation is:
- **Reproducible**: Uses fixed random seed
- **Realistic**: Based on industry patterns and correlations
- **Comprehensive**: Covers films and series across multiple brands

## Business Logic

### Core Assumptions

The analytics are driven by realistic business assumptions:

- **Streaming ARPU**: Disney+ $7.99/month, Hulu $12.99/month
- **Engagement Conversion**: Modeled acquisition and retention impact
- **Windowing**: Cannibalization factors for early streaming
- **Theatrical Performance**: Budget tier-based box office models
- **Discount Rate**: 10% annual for NPV calculations

### Key Calculations

**Title Scorecard**:
- Engagement metrics (peak, decay, long-tail)
- Quality aggregation
- Value = streaming + ad + theatrical + PVOD
- ROI = (Value - Cost) / Cost
- Classification (Tentpole, Workhorse, Niche Gem, etc.)

**Windowing Simulation**:
- Multi-window revenue modeling
- Cannibalization effects
- NPV with time value of money
- Scenario comparison

**Greenlight Forecast**:
- Comparable title selection (similarity scoring)
- Performance distribution analysis
- Bear/base/bull scenarios
- Concept-specific adjustments

## Excel Export

The Data & Assumptions page allows exporting a comprehensive Excel workbook with:

- All business assumptions
- Complete title catalog
- Engagement data (sample)
- Quality metrics
- Computed scorecards
- Portfolio summaries by brand, genre, platform
- Top 20 titles and concentration metrics

## Advanced Usage

### Customizing Assumptions

Edit `magicslate/assumptions.py` to adjust:
- ARPU values
- Conversion rates
- Cannibalization factors
- Classification thresholds

### Regenerating Data

Use the "Refresh Data" feature in the Data & Assumptions page to generate a new synthetic dataset with different random values.

### Extending the Platform

The modular architecture makes it easy to:
- Add new metrics in `metrics.py`
- Create new portfolio views in `portfolio_dashboard.py`
- Add new pages to the Streamlit app
- Integrate real data sources by modifying `loaders.py`

## Technical Details

### Technology Stack

- **Python 3.8+**: Core language
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Plotly**: Interactive visualizations
- **XlsxWriter/OpenPyXL**: Excel export

### Performance

- **Data caching**: Streamlit's `@st.cache_data` for fast page loads
- **Lazy computation**: Analytics computed on-demand
- **Efficient aggregations**: Pandas groupby operations

### Code Quality

- **Fully implemented**: No TODOs or pseudocode
- **Documented**: Comprehensive docstrings
- **Modular**: Clear separation of concerns
- **Type hints**: Enhanced code clarity

## Troubleshooting

### "No module named 'magicslate'"

Make sure you're running the app from the project root directory:
```bash
cd /workspace
streamlit run app/streamlit_app.py
```

### Data not generating

Check that you have write permissions in the `data/` directory. The app will create this directory automatically.

### Excel export not working

Ensure both `xlsxwriter` and `openpyxl` are installed:
```bash
pip install xlsxwriter openpyxl
```

## Future Enhancements

Potential extensions:
- Integration with real data sources (Snowflake, BigQuery, etc.)
- Machine learning models for performance prediction
- A/B testing simulation
- Budget optimization tools
- Multi-year portfolio planning
- Competitive benchmarking

## License

This project is provided as-is for educational and demonstration purposes.

## Contact

For questions or feedback about Magic Slate, please reach out to your Content Planning & Analysis team.

---

**Built with ❤️ using Python and Streamlit**
