# Architecture

```text
USDA public PDFs (3223, 3192)
          |
          v
       collectors
          |
          v
 raw document archive + provenance
          |
          v
 exact-series extraction + validation
          |
          v
        SQLite
          |
          v
 availability-aware feature engineering
          |
          v
 Persistence / Ridge / Random Forest
          |
          v
 archived forecasts -> later actual outcomes
          |
          v
 Streamlit dashboard + evaluation
```

All prediction inputs must have been received by 06:00 Asia/Tashkent. Archive each forecast before its target outcome arrives.
