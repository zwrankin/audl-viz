import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from src.data.process_team_indicators import index_vars, team_indicators, player_indicators
from src.visualization.utils import palette_df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('./data/processed/team_indicators.csv')
df = df.melt(id_vars=index_vars, value_vars=team_indicators, var_name='indicator')
df = pd.merge(df, palette_df, how='outer').sort_values('team')

df_p = pd.read_csv('./data/processed/player_indicators.csv')
player_team = df_p[['player', 'year', 'team']].drop_duplicates()

top_markdown_text = '''
###  AUDL Data Visualization V1
#### Zane Rankin, 2/7/2019
Using data downloaded from [AUDL-pull](https://github.com/dfiorino/audl-pull) by Dan Fiorino
'''

app.layout = html.Div([
    # HEADER
    dcc.Markdown(children=top_markdown_text),

    dcc.RadioItems(
        id='year',
        options=[{'label': i, 'value': i} for i in df.year.unique()],
        value=2018,
        labelStyle={'display': 'inline-block'},
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
    ]),

])


@app.callback(
    Output('scatterplot', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('yaxis-column', 'value'),
     Input('year', 'value')])
def update_graph(xaxis_column_name, yaxis_column_name, year):
    dff = df[df.year == year]

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
    Output('leaderboard', 'figure'),
    [Input('player-indicator', 'value'),
     Input('year', 'value')])
def update_leaderboard(indicator, year):
    dff = df_p[df_p.year == year].groupby('player')[player_indicators].sum().reset_index()
    dff = dff.melt(id_vars='player', value_vars=player_indicators, var_name='indicator')
    n_players = 15
    dff = dff[dff.indicator == indicator]
    # Get correct team & color for specific year
    dff = pd.merge(player_team[player_team['year'] == year], dff)
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
