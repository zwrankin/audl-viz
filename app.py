import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from src.data.process_team_indicators import index_vars, team_indicators, player_indicators
from src.data.utils import gini
from src.visualization.utils import palette_df, palette

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('./data/processed/team_indicators.csv')
df = df.melt(id_vars=index_vars, value_vars=team_indicators, var_name='indicator')
df = pd.merge(df, palette_df, how='outer').sort_values('team')

df_p = pd.read_csv('./data/processed/player_indicators.csv')
player_team = df_p[['player', 'year', 'team']].drop_duplicates()

df_g = pd.concat([pd.DataFrame(df_p.groupby(['team', 'year'])[i].apply(gini)) for i in player_indicators], axis=1)
## [df_g.rename(columns={i: i + '_gini'}, inplace=True) for i in player_indicators]
df_g.reset_index(inplace=True)

# Team records
df_wins = pd.read_csv('./data/processed/team_indicators_EOY.csv')

top_markdown_text = '''
###  AUDL Data Visualization V1
#### Zane Rankin, 2/7/2019
Using data downloaded from [AUDL-pull](https://github.com/dfiorino/audl-pull) by Dan Fiorino
Visualization using Plotly and Dash - [Github](https://github.com/zwrankin/audl-viz)
'''

gini_text = '''
As per [Wikipedia](https://en.wikipedia.org/wiki/Gini_coefficient), the **Gini coefficient** is a
"single number aimed at measuring the degree of inequality in a distribution," often applied to income inequality.  
A lower Gini coefficient for goals indicates a more even distribution of scoring, whereas a high value
indicates fewer players scoring more of the team's goals. 
'''


def subset_years(df, year):
    if year != 'All years':
        return df[df.year == year]
    else:
        return df


app.layout = html.Div([

    dcc.Markdown(children=top_markdown_text),

    html.H6('Season for Analysis'),
    dcc.RadioItems(
        id='year',
        options=[{'label': i, 'value': i} for i in [2014, 2015, 2016, 2017, 2018, 'All years']],
        value='All years',
        labelStyle={'display': 'inline-block'},
    ),

    dcc.Dropdown(
        id='team',
        options=[{'label': i, 'value': i} for i in df.team.sort_values().unique()],
        value='Atlanta Hustle'
    ),

    dcc.Tabs(id="tabs", style={
        'textAlign': 'center', 'margin': '48px 0', 'fontFamily': 'system-ui'}, children=[

        dcc.Tab(label='Overview', children=[
            html.Div([

                html.Div([

                    dcc.Dropdown(
                        id='xaxis-column',
                        options=[{'label': i, 'value': i} for i in team_indicators],
                        value='Goals'
                    ),
                    dcc.Dropdown(
                        id='yaxis-column',
                        options=[{'label': i, 'value': i} for i in team_indicators],
                        value='Goals_against'
                    ),
                ],
                    style={'width': '48%', 'display': 'inline-block'}),

                dcc.Graph(id='scatterplot'),

            ]),
        ]),
        dcc.Tab(label='Team Explorer', children=[
            html.Div([

                dcc.Graph(id='team-players'),

            ]),
        ]),
        dcc.Tab(label='Individual Leaderboard', children=[
            html.Div([
                dcc.Dropdown(
                    id='player-indicator',
                    options=[{'label': i, 'value': i} for i in player_indicators],
                    value='Goals'
                ),

                dcc.Graph(id='leaderboard'),

            ]),
        ]),

        dcc.Tab(label='Gini', children=[
            html.Div([

                dcc.Markdown(gini_text),

                html.Div([

                    dcc.Dropdown(
                        id='gini-indicator',
                        # options=[{'label': f'{i}_gini', 'value': f'{i}_gini'} for i in player_indicators],
                        options=[{'label': i, 'value': i} for i in player_indicators],
                        value='Goals'
                    ),
                    
                    dcc.Graph(id='gini-scatterplot'),
                ],
                    style={'width': '48%', 'display': 'inline-block'}),

                html.Div([
                        dcc.Graph(id='gini-players'),
                ],
                    style={'width': '48%', 'display': 'inline-block'}),

            ]),
        ]),
    ]),

])


@app.callback(
    Output('scatterplot', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('yaxis-column', 'value'),
     Input('year', 'value')])
def update_graph(xaxis_column_name, yaxis_column_name, year):
    dff = subset_years(df, year)

    return {
        'data': [go.Scatter(
            x=dff[(dff['indicator'] == xaxis_column_name) & (dff['team'] == t)]['value'],
            y=dff[(dff['indicator'] == yaxis_column_name) & (dff['team'] == t)]['value'],
            text=dff[(dff['indicator'] == yaxis_column_name) & (dff['team'] == t)]['game'],
            name=str(t),
            mode='markers',
            marker={
                'size': 15,
                'color': dff[(dff['indicator'] == yaxis_column_name) & (dff['team'] == t)]['color1'],
                'line': {'width': 3,
                         'color': dff[(dff['indicator'] == yaxis_column_name) & (dff['team'] == t)]['color2']}
            }
        ) for t in dff.team.unique()],
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
            },
            yaxis={
                'title': yaxis_column_name,
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            height=600,
            hovermode='closest'
        )
    }


@app.callback(
    Output('gini-scatterplot', 'figure'),
    [Input('gini-indicator', 'value'),
     Input('year', 'value')])
def update_gini(gini_ind, year):
    # Team Record
    dff = subset_years(df_wins, year)

    # Gini coefficients
    df_gini = subset_years(df_g, year)

    dff = pd.merge(dff, df_gini)
    dff = pd.merge(dff, palette_df, how='outer')
    dff['team_year'] = dff.year.map(str) + ' ' + dff.team

    return {
        'data': [go.Scatter(
            x=dff[gini_ind],
            y=dff['Win_pct'],
            text=dff.team_year,
            # name=str(t),
            mode='markers',
            marker={
                'size': 15,
                'color': dff['color1'],
                'line': {'width': 3,
                         'color': dff['color2']}
            }
        )],
        'layout': go.Layout(
            xaxis={
                'title': f'{gini_ind} gini coefficient',
            },
            yaxis={
                'title': 'Win Percentage',
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            height=600,
            hovermode='closest'
        )
    }


@app.callback(
    Output('gini-players', 'figure'),
    [Input('gini-indicator', 'value'),
     Input('team', 'value'),
     Input('year', 'value')])
def update_gini_players(indicator, team, year):
    df1 = subset_years(df_p, year)
    # df1 = df1[df1.team == team]

    dff = df1.groupby('player')[player_indicators].sum().reset_index()

    dff = dff.melt(id_vars='player', value_vars=player_indicators, var_name='indicator')
    # n_players = 30
    dff = dff[dff.indicator == indicator]
    # Get correct team & color for specific year
    if year == 'All years':
        player_map = player_team[player_team['year'] == 2018]
    else:
        player_map = player_team[player_team['year'] == year]
    dff = pd.merge(player_map, dff)
    dff = pd.merge(dff, palette_df, how='outer').sort_values('value', ascending=False) # [:n_players]
    dff = dff.sort_values(['team', 'value'], ascending=True)  # plotly seems to invert the order?
    dff['player_rank'] = dff.groupby('team')['value'].rank(ascending=False)
    dff['player_team'] = dff['player'] + '_' + dff['team']

    return {
        'data': [go.Scatter(
            x=dff[dff.team == team]['value'],
            y=dff[dff.team == team]['player_rank'],
            text=dff[dff.team == team]['player_team'],
            name=team,
            mode='markers+lines',
            line={'color': palette[team][1] if team in palette.keys() else 'black'},
            marker={
                'size': 5,
                'color': dff[dff.team == team]['color1'],
                # 'line': {'width': 2,
                #          'color': dff[dff.team == team]['color2']}
            },
        ) for team in dff.team.unique()],
        'layout': go.Layout(
            # title=indicator,
            xaxis={
                'title': indicator,
            },
            yaxis={
                'title': 'Player Rank',
            },
            height=600,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
    }

    

@app.callback(
    Output('team-players', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value')])
def update_players(team, year):
    df1 = subset_years(df_p, year)

    df1 = df1[df1.team == team]
    dff = df1.groupby('player')[player_indicators].sum().reset_index()
    dff = dff.melt(id_vars='player', value_vars=player_indicators, var_name='indicator')

    return {
        'data': [go.Scatter(
            x=dff[dff.player == p]['value'],
            y=dff[dff.player == p]['indicator'],
            name=p,
            mode='markers',
            marker={
                'size': 10,
                'opacity': 0.5,
                # 'color': dff['color1'],
                # 'line': {'width': 3,
                #          'color': dff['color2']}
            },
        ) for p in dff.player.unique()],
        'layout': go.Layout(
            title=team,
            height=600,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
    }


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
            title=indicator,
            height=600,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
