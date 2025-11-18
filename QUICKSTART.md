# 🚀 Quick Start Guide

Get Magic Slate up and running in 3 simple steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- numpy
- pandas
- plotly
- streamlit
- xlsxwriter
- openpyxl

## Step 2: Run the Application

```bash
streamlit run app/streamlit_app.py
```

The app will:
1. Automatically generate synthetic data on first run
2. Open in your browser at `http://localhost:8501`

## Step 3: Explore!

Navigate through the 6 pages using the sidebar:

1. **Overview** - Portfolio summary and KPIs
2. **Title Explorer** - Analyze individual titles
3. **Portfolio Dashboard** - Aggregate views with filters
4. **Windowing Lab** - Simulate release strategies
5. **Greenlight Studio** - Forecast new title concepts
6. **Data & Assumptions** - View data and export Excel

## First-Time Users: Recommended Flow

1. Start at **Overview** to understand the portfolio
2. Go to **Title Explorer** and select a few titles to see detailed analytics
3. Visit **Portfolio Dashboard** and use filters to explore different views
4. Try **Windowing Lab** with a film to compare release strategies
5. Experiment with **Greenlight Studio** to forecast a new title

## Tips

- **Filters**: Use the sidebar filters on Portfolio Dashboard to focus on specific segments
- **Export**: Use the Data & Assumptions page to download a comprehensive Excel report
- **Refresh**: Regenerate synthetic data anytime from the Data & Assumptions page

## Troubleshooting

### Port already in use?
```bash
streamlit run app/streamlit_app.py --server.port 8502
```

### Need help?
Check the full README.md for detailed documentation.

---

**Enjoy using Magic Slate! 🎬✨**
