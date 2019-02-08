import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from src.data.process_team_indicators import index_vars, indicators

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('./data/processed/team_indicators.csv')
df = df.melt(id_vars=index_vars, value_vars=indicators, var_name='indicator')

available_indicators = list(df.indicator.unique())

top_markdown_text = '''
###  AUDL Data Visualization V1
#### Zane Rankin, 2/7/2019
Using data downloaded from [AUDL-pull](https://github.com/dfiorino/audl-pull) by Dan Fiorino
'''

app.layout = html.Div([
    # HEADER
    dcc.Markdown(children=top_markdown_text),

    html.Div([

        html.Div([
            dcc.RadioItems(
                id='year',
                options=[{'label': i, 'value': i} for i in df.year.unique()],
                value=2018,
                labelStyle={'display': 'inline-block'},
            ),
            dcc.Dropdown(
                id='xaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='Goals'
            ),
            dcc.Dropdown(
                id='yaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='Goals_against'
            ),
        ],
            style={'width': '48%', 'display': 'inline-block'}),

        dcc.Graph(id='scatterplot'),

    ])
])


@app.callback(
    dash.dependencies.Output('scatterplot', 'figure'),
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
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
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


if __name__ == '__main__':
    app.run_server(debug=True)
