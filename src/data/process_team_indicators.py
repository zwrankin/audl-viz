import pandas as pd
from .utils import DATA_DIR, load_raw_data

index_vars = ['year', 'team', 'opponent', 'date', 'game']
indicators = ['Goals', 'Catches', 'Ds', 'Turnovers', 'Drops', 'Throwaways', 'Goals_against']

def make_team_indicators():

    df = load_raw_data()

    # Make index
    df['datetime'] = pd.to_datetime(df['Date/Time'])
    df['date'] = df.datetime.dt.date
    df['year'] = df.datetime.dt.year
    df.rename(columns={'Teamname':'team', 'Opponent':'opponent'}, inplace=True)
    df['game'] = df.team + "_" + df.opponent + "_" + df.date.map(str)

    # Make indicators
    dummies = pd.get_dummies(df['Action'])
    df = pd.concat([df, dummies], axis=1)
    df['Turnovers'] = df.Throwaway + df.Drop
    # For goals, we want to separate whether the team is on Offense or Defense
    df['Goals_against'] = 0
    df.loc[df['Event Type'] == 'Defense', 'Goals_against'] = df['Goal']
    df.loc[df['Event Type'] == 'Defense', 'Goal'] = 0
    # Let's be intensional with indicator names
    rename_ind_dict = {
        'Goal': 'Goals',
        'Catch': 'Catches',
        'D': 'Ds',
        'Drop': 'Drops',
        'Throwaway': 'Throwaways',
    }
    df.rename(columns=rename_ind_dict, inplace=True)

    # Reshape wide and save - NOTE that normally I'd do hdf but was having dash compatability issues so csv it is
    df_wide = df.groupby(index_vars)[indicators].sum().reset_index()
    df_wide.to_csv(f'{DATA_DIR}/processed/team_indicators.csv', index=False)


if __name__ == '__main__':
    make_team_indicators()
