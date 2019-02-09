import os
import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = str(Path(__file__).parent.parent.parent/'data')


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
