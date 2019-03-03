AUDL Data Visualization
==============================

Visualization of data from the American Ultimate Disc League (AUDL)

### Visualization (preliminary!)
**https://audl-viz.herokuapp.com/**  
Visualization built in [Dash](https://plot.ly/products/dash/) and hosted on [Heroku](https://www.heroku.com/).  
For a technical guide to Dash development, 
refer to my [Medium article](https://towardsdatascience.com/a-gentle-introduction-to-dash-development-and-deployment-f8b91990d3bd)

### Data 
Data is collected during each AUDL game using the UltiAnalytics app that then saves raw data to 
[UltiAnalytics](https://www.ultianalytics.com/index.html).  
Dan Fiorino wrote [audl-pull](https://github.com/dfiorino/audl-pull), 
a Python repo providing invaluable data cleaning and standardization.  
Within this repo, there is a [script](https://github.com/zwrankin/audl-viz/blob/master/src/data/process_team_indicators.py) 
that aggregates [audl-pull output](https://github.com/dfiorino/audl-pull/tree/master/output) 
into several csvs used in the visualization app. I wrote a 
[Notebook](https://github.com/zwrankin/audl-viz/blob/master/notebooks/2019_03_03_data_overview.ipynb) that explains these csvs. 
