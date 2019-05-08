import os
import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = str(Path(__file__).parent.parent.parent/'data')

division_dict = {
    'East': ['DC Breeze', 'Montreal Royal', 'New York Empire',
             'Philadelphia Phoenix', 'Rochester Dragons', 'Toronto Rush', 'Ottawa Outlaws'],
    'Midwest': ['Chicago Wildfire', 'Detroit Mechanix', 'Indianapolis AlleyCats', 'Minnesota Wind Chill',
                'Pittsburgh Thunderbirds', 'Madison Radicals', 'Cincinnati Revolution'],
    'South': ['Atlanta Hustle', 'Charlotte Express', 'Jacksonville Cannons', 'Nashville NightWatch',
              'Austin Sol', 'Dallas Roughnecks', 'Tampa Bay Cannons'],
    'West': ['Salt Lake Lions', 'Seattle Cascades', 'San Francisco FlameThrowers', 'San Jose Spiders',
             'San Diego Growlers', 'Seattle Raptors', 'Vancouver Riptide', 'Los Angeles Aviators'],
}


def load_raw_data():
    files = os.listdir(f'{DATA_DIR}/raw')
    df = pd.concat([pd.read_csv(f'{DATA_DIR}/raw/{f}') for f in files])
    df = clean_dates(df, 'Date/Time')

    # Make index
    df.rename(columns={'Teamname': 'team', 'Opponent': 'opponent'}, inplace=True)
    df['game'] = df.team + "_" + df.opponent + "_" + df.date.map(str)

    return df.reset_index()

def clean_dates(df, colname):
    df['datetime'] = pd.to_datetime(df[colname])
    df['date'] = df.datetime.dt.date
    df['year'] = df.datetime.dt.year
    return df


def subset_years(df, year):
    if year != 'All years':
        return df[df.year == year]
    else:
        return df


def apply_game_threshold(df, n_games=1):
    total_games = df.groupby('player')['Games Played'].sum().reset_index().rename({'Games Played': 'total_games'}, axis=1)
    df = pd.merge(df, total_games)
    return df.loc[df.total_games >= n_games].drop('total_games', axis=1)


def aggregate_rates(df, indicators, rate_type='count'):
    if rate_type == 'count':
        pass
    elif rate_type == 'per game':
        for i in indicators:
            df[i] = df[i] / df['Games Played']
    elif rate_type == 'per point':
        for i in indicators:
            df[i] = df[i] / df['Points Played']
    return df


def list_top_occurences(values, n):
    return values.value_counts()[:n].index.tolist()


def make_sankey_df(df, team='Chicago Wildfire', year=2018, line='O', n_players=14):
    """df must have Passer, Receiver, Line"""
    df = subset_years(df, year)
    df = df.loc[df.team == team]
    if line != 'both':
        df = df.loc[df.Line == line]
    df = df[['Passer', 'Receiver']]

    top_assists = list_top_occurences(df.Passer, n_players)
    df['Passer'] = df.Passer.transform(lambda x: x if x in top_assists else "Other")
    top_goals = list_top_occurences(df.Receiver, n_players)
    df['Receiver'] = df.Receiver.transform(lambda x: x if x in top_goals else "Other")

    # There's a bug where plotly sankeys can't handle circularity, so add suffixes to make entities different
    # https://community.plot.ly/t/sankey-diagram-handling-circularity-error/15102/3
    df['Receiver'] = df.Receiver + ' '
    return df.groupby(['Passer', 'Receiver']).agg(lambda x: len(x)).reset_index().rename(columns={0:'Value'})


def gini(x):
    """
    Calculates the gini coefficient of a series
    # https://stackoverflow.com/questions/39512260/calculating-gini-coefficient-in-python-numpy
    # https://en.wikipedia.org/wiki/Gini_coefficient
    :param x:
    :return:
    """

    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    # Relative mean absolute difference
    rmad = mad/np.mean(x)
    # Gini coefficient
    g = 0.5 * rmad
    return g
