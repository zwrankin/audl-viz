import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from src.data.utils import division_dict
from src.data.utils import subset_years, apply_game_threshold, aggregate_rates, make_sankey_df
from src.visualization.utils import palette_df, palette, map_colors, tab_style, tab_selected_style

app = dash.Dash(__name__)

server = app.server

# TODO - how to best get from AUDL-pull
team_index_vars = ['year', 'team', 'opponent', 'date', 'game']
player_index_vars = ['year', 'team', 'player']

df_t = pd.read_csv('./data/processed/team_stats.csv')
df_t_wide = df_t.copy()
team_indicators = [i for i in df_t.columns if i not in team_index_vars]
team_eoy_indicators = team_indicators
# For now, it seems best to melt df_t here, but df_p within the callbacks to allow custom processing (e.g. apply_game_threshold)
df_t = df_t.melt(id_vars=team_index_vars, value_vars=team_indicators, var_name='indicator')
df_t = pd.merge(df_t, palette_df, how='outer').sort_values('team')
df_t['opponent_color1'] = df_t.opponent.transform(lambda x: map_colors(x, palette, 0))
df_t['opponent_color2'] = df_t.opponent.transform(lambda x: map_colors(x, palette, 1))

df_p = pd.read_csv('./data/processed/player_stats.csv')
player_indicators = [i for i in df_p.columns if i not in player_index_vars]
player_team = df_p[['player', 'year', 'team']].drop_duplicates()

df_eoy = pd.read_csv('./data/processed/team_stats_by_year.csv')

df_goals = pd.read_csv('./data/processed/all_goals.csv')

bottom_markdown_text = '''
Data downloaded from [AUDL-pull](https://github.com/dfiorino/audl-pull) (credit Dan Fiorino)  
Visualization by Zane Rankin (zwrankin@gmail.com) using Plotly and Dash - [Github](https://github.com/zwrankin/audl-viz)
'''

app.layout = html.Div([
    html.A([
        html.Img(
            src='/assets/audl_logo2.png',
            style=dict(height='35%', width='35%'))],
        href='https://www.theaudl.com'),

    # html.H6('Season'),
    dcc.RadioItems(
        id='year',
        options=[{'label': i, 'value': i} for i in [2014, 2015, 2016, 2017, 2018, 'All seasons']],
        value=2018,
        labelStyle={'display': 'inline-block'},
    ),

    dcc.Tabs(id="tabs", style={
        'textAlign': 'center', 'margin': '48px 0', 'fontFamily': 'system-ui'}, children=[

        dcc.Tab(label='TEAM EXPLORER', style=tab_style, selected_style=tab_selected_style, children=[
            html.Div([
                dcc.Dropdown(
                    id='team',
                    options=[{'label': i, 'value': i} for i in df_t.team.sort_values().unique()],
                    value='Atlanta Hustle',
                    style={'fontSize': 20, 'width': '70%', 'verticalAlign': 'middle'},
                ),

                dcc.Dropdown(
                    id='player-indicators',
                    options=[{'label': i, 'value': i} for i in player_indicators],
                    multi=True,
                    value=['Plus/Minus', 'Goals', 'Assists', 'Hockey Assists', 'Blocks', 'Turnovers'],
                    style={'width': '70%'}
                ),
                dcc.RadioItems(
                    id='rate-type',
                    options=[{'label': i, 'value': i} for i in ['count', 'per point', 'per game']],
                    value='count',
                    labelStyle={'display': 'inline-block'},
                ),
                daq.NumericInput(
                    id='min-games',
                    label='Minimum Games Played',
                    value=5,
                ),
                dcc.Graph(id='team-players'),

                daq.NumericInput(
                    id='sankey-n-players',
                    label='Players to display',
                    value=14,
                    max=30,
                ),

                html.Div(className='row', children=[
                    html.Div([
                        dcc.Graph(id='o-sankey'),
                        dcc.Graph(id='o-conversion'),
                    ], className='six columns'),
                    html.Div([
                        dcc.Graph(id='d-sankey'),
                        dcc.Graph(id='d-conversion'),
                    ], className='six columns'),
                ]),

                html.H6('Season Timeline'),
                dcc.Dropdown(
                    id='team-indicators',
                    options=[{'label': i, 'value': i} for i in team_indicators],
                    multi=True,
                    value=['Hold Rate', 'Break Rate'],
                    style={'width': '70%'}
                ),

                dcc.Graph(id='team-timeseries'),


            ]),
        ]),

        dcc.Tab(label='LEAGUE EXPLORER', style=tab_style, selected_style=tab_selected_style, children=[
            html.Div([
                # html.H5('Team Stats'),
                dcc.Dropdown(
                    id='team-eoy-indicators',
                    options=[{'label': i, 'value': i} for i in team_eoy_indicators],
                    multi=True,
                    value=['O-line Scoring Efficiency', 'Hold Rate', 'Break Rate', 'D-line Scoring Efficiency'],
                    style={'width': '70%'}
                ),
                # html.H6('Metric'),
                dcc.RadioItems(
                    id='metric',
                    options=[{'label': i, 'value': i} for i in ['rank', 'value']],
                    value='rank',
                    labelStyle={'display': 'inline-block'},
                ),
                dcc.Markdown('*Highest value is ranked #1*'),
                dcc.Graph(id='team-comparison'),

                # html.H6('Division'),
                dcc.RadioItems(
                    id='division',
                    options=[{'label': i, 'value': i} for i in division_dict.keys()],
                    value='East',
                    labelStyle={'display': 'inline-block'},
                ),
                dcc.Dropdown(
                    id='matchup-indicator',
                    options=[{'label': i, 'value': i} for i in team_indicators],
                    value='Hold Rate',
                    style={'width': '50%'}
                ),
                dcc.Graph(id='matchup-heatmap'),

            ]),
        ]),

        dcc.Tab(label='INDIVIDUAL LEADERBOARD', style=tab_style, selected_style=tab_selected_style, children=[
            html.Div([
                dcc.Dropdown(
                    id='player-indicator',
                    options=[{'label': i, 'value': i} for i in player_indicators],
                    value='Plus/Minus',
                    style={'width': '50%'}
                ),
                dcc.RadioItems(
                    id='rate-type1',
                    options=[{'label': i, 'value': i} for i in ['count', 'per point', 'per game']],
                    value='count',
                    labelStyle={'display': 'inline-block'},
                ),
                daq.NumericInput(
                    id='min-games1',
                    label='Minimum Games Played',
                    value=5,
                ),
                dcc.Graph(id='leaderboard'),

            ]),
        ]),

    ]),

    dcc.Markdown(children=bottom_markdown_text),

])


@app.callback(
    Output('matchup-heatmap', 'figure'),
    [Input('division', 'value'),
     Input('year', 'value'),
     Input('matchup-indicator', 'value')
     ])
def update_matchup_heatmap(division, year, indicator):
    df1 = subset_years(df_t_wide, year)

    teams = division_dict[division]
    opponents = division_dict[division]

    df1 = df1.loc[(df1.team.isin(teams)) & (df1.opponent.isin(opponents))]
    df1 = df1.groupby(['team', 'opponent'])[indicator].mean().reset_index()

    df1 = df1.sort_values(['team', 'opponent'], ascending=[False, True])  #

    return {
        'data': [go.Heatmap(z=round(df1[indicator], 2),
                            x=df1.opponent,
                            y=df1.team,
                            reversescale=True,
                            text=[indicator] * len(df1),
                            hoverinfo='z+text')],
        'layout': go.Layout(
            title=f'Average {indicator} by matchup',
            margin={'l': 200, 'b': 40, 't': 40, 'r': 40},
            yaxis=dict(title='Team'),
            xaxis=dict(title='Opponent')
        )
    }


@app.callback(
    Output('o-conversion', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value')])
def update_o_conversion(team, year):
    return make_conversion_plot(team, year, line='O')


@app.callback(
    Output('d-conversion', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value')])
def update_d_conversion(team, year):
    return make_conversion_plot(team, year, line='D')


@app.callback(
    Output('o-sankey', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value'),
     Input('sankey-n-players', 'value')])
def update_o_sankey(team, year, n_players):
    return make_sankey(team, year, n_players, line='O')


@app.callback(
    Output('d-sankey', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value'),
     Input('sankey-n-players', 'value')])
def update_d_sankey(team, year, n_players):
    return make_sankey(team, year, n_players, line='D')


@app.callback(
    Output('leaderboard', 'figure'),
    [Input('player-indicator', 'value'),
     Input('year', 'value'),
     Input('rate-type1', 'value'),
     Input('min-games1', 'value')])
def update_leaderboard(indicator, year, rate_type, min_games):
    df1 = subset_years(df_p, year)
    df1 = apply_game_threshold(df1, n_games=min_games)

    dff = df1.groupby('player')[player_indicators].sum().reset_index()
    dff = aggregate_rates(dff, player_indicators, rate_type)

    dff = dff.melt(id_vars='player', value_vars=player_indicators, var_name='indicator')
    n_players = 20
    dff = dff[dff.indicator == indicator]
    # Get correct team & color for specific year
    if year == 'All seasons':
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
     Input('player-indicators', 'value'),
     Input('min-games', 'value'),
     Input('rate-type', 'value'),
     Input('team-players', 'hoverData'),
     Input('team-players', 'clickData')])
def update_players(team, year, indicators, min_games, rate_type, hover_data, click_data):
    df1 = subset_years(df_p, year)

    df1 = df1[df1.team == team]
    df1 = apply_game_threshold(df1, n_games=min_games)
    dff = df1.groupby('player')[player_indicators].sum().reset_index()
    dff = aggregate_rates(dff, player_indicators, rate_type)
    dff = dff.melt(id_vars='player', value_vars=indicators, var_name='indicator')

    dff['indicator'] = pd.Categorical(dff.indicator, indicators)
    dff = dff.sort_values(['indicator', 'player'], ascending=[False, True])

    players = dff.player.unique()

    if hover_data:
        i = hover_data['points'][0]['curveNumber']
    elif click_data:
        i = click_data['points'][0]['curveNumber']
    else:
        i = 0
    opacities = [0.5] * len(players)
    marker_sizes = [10] * len(players)
    line_widths = [0.4] * len(players)
    opacities[i] = 1
    marker_sizes[i] = 20
    line_widths[i] = 2

    return {
        'data': [go.Scatter(
            x=dff[dff.player == p]['value'],
            y=dff[dff.player == p]['indicator'],
            name=p,
            mode='markers+lines',
            marker={
                'size': marker_sizes[i],
                'opacity': opacities[i],
                # 'line': {'width': 0}
            },
            line={'width': line_widths[i]}
        ) for i, p in enumerate(players)],
        'layout': go.Layout(
            # title=team,
            height=80 + 80*len(indicators),
            margin={'l': 120, 'b': 40, 't': 40, 'r': 40},
            hovermode='closest'
        )
    }


@app.callback(
    Output('team-timeseries', 'figure'),
    [Input('team', 'value'),
     Input('year', 'value'),
     Input('team-indicators', 'value')
     ])
def update_team_timeseries(team, year, indicators):
    df1 = subset_years(df_t, year)

    df1 = df1[df1.team == team]

    dff = df1.sort_values(['indicator', 'date'], ascending=[False, True])

    return {
        'data': [go.Scatter(
            x=dff[dff.indicator == i]['date'],
            y=dff[dff.indicator == i]['value'],
            name=i,
            text=dff['opponent'],
            mode='lines+markers',
            marker={
                'size': 15,
                # 'opacity': 0.5,
                'color': dff['opponent_color1'],
                'line': {'width': 3,
                         'color': dff['opponent_color2']}
            },
            line={'width': 3}
        ) for i in indicators],
        'layout': go.Layout(
            # title=team,
            height=400,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 40},
            hovermode='closest'
        )
    }


@app.callback(
    Output('team-comparison', 'figure'),
    [Input('year', 'value'),
     Input('team-eoy-indicators', 'value'),
     Input('metric', 'value'),
     Input('team-comparison', 'hoverData'),
     Input('team-comparison', 'clickData')])
def update_team_comparison(year, indicators, metric, hover_data, click_data):
    df1 = subset_years(df_eoy, year)

    dff = df1.melt(id_vars='team', value_vars=indicators, var_name='indicator')

    dff['indicator'] = pd.Categorical(dff.indicator, indicators)
    dff = pd.merge(dff, palette_df, how='outer')
    dff = dff.sort_values(['indicator', 'team'], ascending=[False, True])
    dff["rank"] = dff.groupby("indicator")["value"].rank("min", ascending=False)

    if hover_data:
        i = hover_data['points'][0]['curveNumber']
    elif click_data:
        i = click_data['points'][0]['curveNumber']
    else:
        i = 0
    marker_sizes = [10] * len(dff.team.unique())
    line_widths = [0.4] * len(dff.team.unique())
    marker_sizes[i] = 20
    line_widths[i] = 2

    metric2 = "value"
    if metric == "value":
        metric2 = "rank"

    return {
        'data': [go.Scatter(
            x=dff[dff.team == t][metric],
            y=dff[dff.team == t]['indicator'],
            name=t,
            text=round(dff[dff.team == t][metric2], 2), 
            mode='markers+lines',
            marker={
                'size': marker_sizes[i],  # 10
                'color': dff[dff.team == t]['color1'],
                'line': {'width': 2,
                         'color': dff[dff.team == t]['color2']}
            },
            line={'width': line_widths[i], 'color': map_colors(t, palette, 1)}
        ) for i, t in enumerate(dff.team.unique())],
        'layout': go.Layout(
            # title=team,
            xaxis=dict(title=metric, titlefont=dict(size=18)),
            height=200 + 100*len(indicators),
            margin={'l': 200, 'b': 40, 't': 40, 'r': 40},
            hovermode='closest'
        )
    }


def make_sankey(team, year, n_players, line):
    """TODO - refactor so easier to move to viz utils, for now it has too many dependencies"""
    data = make_sankey_df(df_goals, team, year, line, n_players=n_players)
    # Plotly sankey needs numeric ids, not names
    players = set(data.Passer.tolist() + data.Receiver.tolist())
    player_dict = {j: i for i, j in enumerate(players)}
    data['Source'] = data.Passer.map(player_dict)
    data['Target'] = data.Receiver.map(player_dict)
    title = 'Goals'
    if line == 'O':
        title = "Holds"
    elif line == 'D':
        title = "Breaks"
    data_trace = dict(
        type='sankey',
        node=dict(
            # pad = 15,
            # thickness = 15,
            # line = dict(
            #     color = "black",
            #     width = 0.5
            # ),
            label=list(player_dict.keys()),
        ),
        link=dict(
            source=data['Source'],
            target=data['Target'],
            value=data['Value'],
        ))

    return {
        'data': [data_trace],
        'layout': go.Layout(
            title=title,
            height=700,  # width=600,
            # margin={'l': 120, 'b': 40, 't': 40, 'r': 0},
            hovermode='closest'
        )
    }


def make_conversion_plot(team, year, line):
    """TODO - refactor so easier to move to viz utils, for now it has too many dependencies"""
    df1 = subset_years(df_p, year)

    df1 = df1[df1.team == team]

    # Todo - add this to player indicators?
    df1['Proportion Offensive'] = df1[f'O Points Played'] / df1['Points Played']

    title = ""
    if line == 'O':
        title = "Offense"
    elif line == 'D':
        title = "Defense"

    return {
        'data': [go.Scatter(
            x=df1[f'{line} Points Played'],
            y=df1[f'{line}-line Scoring Efficiency'],
            # name=p,
            mode='markers',
            marker=dict(
                color=df1['Proportion Offensive'],
                colorscale='RdBu',
                reversescale=True,
                showscale=True,
                colorbar=dict(
                    title='% Offensive',
                ),
            ),
            text=df1['player'],
            # 'size': 10,
            # 'opacity': 0.5,
            # 'line': {'width': 0}
            # line={'width': 0.4}
        )],
        'layout': go.Layout(
            # title=title,
            height=400,
            margin={'l': 120, 'b': 40, 't': 40, 'r': 40},
            hovermode='closest',
            yaxis=dict(
                range=[0, 1],
                title=f'{line}-line Scoring Efficiency',
            ),
            xaxis=dict(title=f'Points Played ({line})')
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
