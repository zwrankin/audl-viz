import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from src.data.process_team_indicators import index_vars, team_indicators, player_indicators
from src.data.utils import subset_years
from src.visualization.utils import palette_df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('./data/processed/team_indicators.csv')
df = df.melt(id_vars=index_vars, value_vars=team_indicators, var_name='indicator')
df = pd.merge(df, palette_df, how='outer').sort_values('team')

df_p = pd.read_csv('./data/processed/player_indicators.csv')
player_team = df_p[['player', 'year', 'team']].drop_duplicates()

# Team records
#df_wins = pd.read_csv('./data/processed/team_indicators_EOY.csv')

top_markdown_text = '''
###  AUDL Data Visualization Prototype
'''

bottom_markdown_text = '''
Data downloaded from [AUDL-pull](https://github.com/dfiorino/audl-pull) by Dan Fiorino  
Visualization by Zane Rankin using Plotly and Dash - [Github](https://github.com/zwrankin/audl-viz)
'''

app.layout = html.Div([

    dcc.Markdown(children=top_markdown_text),

    html.H6('Season for Analysis'),
    dcc.RadioItems(
        id='year',
        options=[{'label': i, 'value': i} for i in [2014, 2015, 2016, 2017, 2018, 'All years']],
        value=2018,
        labelStyle={'display': 'inline-block'},
    ),

    dcc.Tabs(id="tabs", style={
        'textAlign': 'center', 'margin': '48px 0', 'fontFamily': 'system-ui'}, children=[

        
        dcc.Tab(label='Leaderboard', children=[
            html.Div([
                dcc.Dropdown(
                    id='player-indicator',
                    options=[{'label': i, 'value': i} for i in player_indicators],
                    value='Goals'
                ),

                dcc.Graph(id='leaderboard'),

            ]),
        ]),
                        
        dcc.Tab(label='Team Explorer', children=[
            html.Div([
                    dcc.Dropdown(
                            id='team',
                            options=[{'label': i, 'value': i} for i in df.team.sort_values().unique()],
                            value='Atlanta Hustle'
                            ),
                            dcc.Dropdown(
                            id='player-indicators',
                            options=[{'label': i, 'value': i} for i in player_indicators],
                            multi=True,
                            value=['Plus_Minus', 'Goals', 'Assists', 'Ds', 'Turnovers']
                        ),

                dcc.Graph(id='team-players'),

            ]),
        ]),


    ]),
                        
    dcc.Markdown(children=bottom_markdown_text),

])
                

@app.callback(
    Output('leaderboard', 'figure'),
    [Input('player-indicator', 'value'),
     Input('year', 'value')])
def update_leaderboard(indicator, year):
    df1 = subset_years(df_p, year)

    dff = df1.groupby('player')[player_indicators].sum().reset_index()

    dff = dff.melt(id_vars='player', value_vars=player_indicators, var_name='indicator')
    n_players = 15
    dff = dff[dff.indicator == indicator]
    # Get correct team & color for specific year
    if year == 'All years':
        player_map = player_team[player_team['year'] == 2018]
    else:
        player_map = player_team[player_team['year'] == year]
    dff = pd.merge(player_map, dff)
    dff = pd.merge(dff, palette_df, how='outer').sort_values('value', ascending=False)[:n_players]
    dff = dff.sort_values('value', ascending=True)  # plotly seems to invert the order?

    return {
        'data': [go.Scatter(
            x=dff['value'],
            y=dff['player'],
            text=dff['team'],
            mode='markers',
            marker={
                'size': 15,
                'color': dff['color1'],
                'line': {'width': 3,
                         'color': dff['color2']}
            },
        )],
        'layout': go.Layout(
            # title=indicator,
            height=600,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
    }
    

@app.callback(
    Output('team-players', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value'),
     Input('player-indicators', 'value')])
def update_players(team, year, indicators):
    df1 = subset_years(df_p, year)

    df1 = df1[df1.team == team]
    dff = df1.groupby('player')[player_indicators].sum().reset_index()
    dff = dff.melt(id_vars='player', value_vars=indicators, var_name='indicator')
    
    dff['indicator'] = pd.Categorical(dff.indicator, indicators)
    dff = dff.sort_values(['indicator', 'player'], ascending=[False, True])

    return {
        'data': [go.Scatter(
            x=dff[dff.player == p]['value'],
            y=dff[dff.player == p]['indicator'],
            name=p,
            mode='markers+lines',
            marker={
                'size': 10,
                'opacity': 0.5,
                # 'line': {'width': 0}
            },
            line={'width': 0.4}
        ) for p in dff.player.unique()],
        'layout': go.Layout(
            title=team,
            height=600,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
