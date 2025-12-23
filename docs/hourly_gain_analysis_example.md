# Hourly Gain Analysis - Example Output

This file demonstrates the expected output format of the `hourly_gain_analysis.py` script.

## Text Output Example

```
================================================================================
HOURLY GAIN/LOSS ANALYSIS: SPY
Analysis Period: Last 10 years
================================================================================

Hour (UTC)   Avg Gain %   Total Bars   Positive     Negative    
--------------------------------------------------------------------------------
09:00-09:59      0.0523         2520        1340         1180   
10:00-10:59      0.0412         2520        1310         1210   
11:00-11:59      0.0235         2520        1290         1230   
12:00-12:59      0.0189         2520        1275         1245   
13:00-13:59     -0.0087         2520        1240         1280   
14:00-14:59      0.0823         2520        1380         1140   
15:00-15:59      0.0654         2520        1355         1165   
16:00-16:59      0.0321         2520        1305         1215   
17:00-17:59      0.0189         2520        1285         1235   
18:00-18:59      0.0145         2520        1270         1250   
19:00-19:59     -0.0123         2520        1235         1285   
20:00-20:59      0.0078         2520        1260         1260   
================================================================================

KEY INSIGHTS:
  • Best hour: 14:00-14:59 (avg 0.0823%)
  • Worst hour: 19:00-19:59 (avg -0.0123%)

================================================================================
HOURLY GAIN/LOSS ANALYSIS: QQQ
Analysis Period: Last 10 years
================================================================================

Hour (UTC)   Avg Gain %   Total Bars   Positive     Negative    
--------------------------------------------------------------------------------
09:00-09:59      0.0687         2520        1360         1160   
10:00-10:59      0.0534         2520        1330         1190   
11:00-11:59      0.0312         2520        1300         1220   
12:00-12:59      0.0245         2520        1285         1235   
13:00-13:59     -0.0102         2520        1250         1270   
14:00-14:59      0.1043         2520        1400         1120   
15:00-15:59      0.0823         2520        1375         1145   
16:00-16:59      0.0412         2520        1315         1205   
17:00-17:59      0.0245         2520        1295         1225   
18:00-18:59      0.0189         2520        1280         1240   
19:00-19:59     -0.0156         2520        1245         1275   
20:00-20:59      0.0101         2520        1265         1255   
================================================================================

KEY INSIGHTS:
  • Best hour: 14:00-14:59 (avg 0.1043%)
  • Worst hour: 19:00-19:59 (avg -0.0156%)
```

## CSV Output Example

File: `results/hourly_analysis_spy.csv`

```csv
hour_utc,avg_gain_pct,total_count,positive_count,negative_count
9,0.0523,2520,1340,1180
10,0.0412,2520,1310,1210
11,0.0235,2520,1290,1230
12,0.0189,2520,1275,1245
13,-0.0087,2520,1240,1280
14,0.0823,2520,1380,1140
15,0.0654,2520,1355,1165
16,0.0321,2520,1305,1215
17,0.0189,2520,1285,1235
18,0.0145,2520,1270,1250
19,-0.0123,2520,1235,1285
20,0.0078,2520,1260,1260
```

## Key Observations from Example Data

1. **Best Performing Hours (UTC):**
   - For SPY: 14:00-14:59 (avg +0.0823%)
   - For QQQ: 14:00-14:59 (avg +0.1043%)
   - This corresponds to 9:00-9:59 AM ET (market open hour)

2. **Worst Performing Hours (UTC):**
   - For SPY: 19:00-19:59 (avg -0.0123%)
   - For QQQ: 19:00-19:59 (avg -0.0156%)
   - This corresponds to 2:00-2:59 PM ET (afternoon session)

3. **Volatility Patterns:**
   - Higher positive counts during opening hours (14:00-15:00 UTC)
   - More balanced positive/negative distribution in afternoon
   - Tech-heavy QQQ shows larger percentage swings than SPY

4. **Trading Implications:**
   - Consider timing entries/exits based on historical patterns
   - Opening hour (14:00 UTC / 9:00 AM ET) shows strongest upward bias
   - Late afternoon (19:00 UTC / 2:00 PM ET) shows slight negative bias

## Usage Notes

**Important:** These are example statistics for demonstration purposes only. 
Actual results will vary based on:
- The specific time period analyzed
- Market conditions during that period
- The symbols chosen for analysis
- Data quality and completeness from Alpaca

**Time Zone Note:** All times are in UTC. To convert to ET (US Eastern Time):
- ET = UTC - 5 hours (EST during winter)
- ET = UTC - 4 hours (EDT during summer)

Example: 14:00 UTC = 9:00 AM ET (market open)

**Interpretation Caveats:**
- Past performance does not guarantee future results
- Hourly patterns can change over time due to market structure changes
- These statistics reflect historical averages and may not apply to current conditions
- Always validate with recent data before making trading decisions
