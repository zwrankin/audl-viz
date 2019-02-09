import pandas as pd
from .utils import DATA_DIR, load_raw_data

index_vars = ['year', 'team', 'opponent', 'date', 'game']
team_indicators = ['Goals', 'Catches', 'Ds', 'Turnovers', 'Drops', 'Throwaways', 'Goals_against']
player_indicators  = ['Completions', 'Assists', 'Throwaways', 'Receptions', 'Goals', 'Drops', 'Ds', 'Turnovers', 'Plus_Minus']

def make_team_indicators(return_df = False):

    df = load_raw_data()

    # Yearly team statistics, starting with total wins, losses
    df_final = df[df.Action == 'GameOver']
    df_final['Wins'] = 0
    df_final['Losses'] = 0
    df_final.loc[df_final['Our Score - End of Point'] < df_final['Their Score - End of Point'], 'Losses'] = 1
    df_final.loc[df_final['Our Score - End of Point'] > df_final['Their Score - End of Point'], 'Wins'] = 1
    df_final = df_final.groupby(['team', 'year'])['Wins', 'Losses'].sum().reset_index()
    df_final['Win_pct'] = df_final.Wins / (df_final.Wins + df_final.Losses) * 100

    df_final.to_csv(f'{DATA_DIR}/processed/team_indicators_EOY.csv', index=False)


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
    df_wide = df.groupby(index_vars)[team_indicators].sum().reset_index()
    df_wide.to_csv(f'{DATA_DIR}/processed/team_indicators.csv', index=False)

    if return_df:
        return df_wide


def make_player_indicators(return_df=False):

    df = load_raw_data()
    # Make index
    df.rename(columns={'Teamname': 'team', 'Opponent': 'opponent'}, inplace=True)
    df['game'] = df.team + "_" + df.opponent + "_" + df.date.map(str)

    # For now, I won't track stats of missing, because all relevant ones (e.g. Goals) should be present
    # df.Passer.fillna('UNKNOWN_OR_NONE', inplace=True)
    # df.Receiver.fillna('UNKNOWN_OR_NONE', inplace=True)

    # Passer-based stats
    df_p = df.copy()
    df_p['player'] = df['Passer']
    df_p['Completions'] = 0
    df_p['Assists'] = 0
    df_p['Throwaways'] = 0
    df_p.loc[df_p['Action'] == 'Catch', 'Completions'] = 1
    df_p.loc[df_p['Action'] == 'Goal', 'Assists'] = 1
    df_p.loc[df_p['Action'] == 'Throwaway', 'Throwaways'] = 1

    # Receiver-based stats (goals, drops)
    df_r = df.copy()
    df_r['player'] = df['Receiver']
    df_r['Goals'] = 0
    df_r['Drops'] = 0
    df_r['Receptions'] = 0
    df_r.loc[df_r['Action'] == 'Catch', 'Receptions'] = 1
    df_r.loc[df_r['Action'] == 'Goal', 'Goals'] = 1
    df_r.loc[df_r['Action'] == 'Drop', 'Drops'] = 1

    # Defensive stats
    df_d = df.copy()
    df_d['player'] = df['Defender']
    df_d['Ds'] = 0
    df_d.loc[df_r['Action'] == 'D', 'Ds'] = 1

    # TODO - Points Played

    df_all = pd.concat([df_p, df_r, df_d], sort=False)

    inds  = player_indicators(['Turnovers', 'Plus_Minus'])
    df_wide = df_all.groupby(index_vars + ['player'])[inds].sum().reset_index()

    # Aggregates:
    df_wide['Turnovers'] = df_wide.Throwaways + df_wide.Drops
    df_wide['Plus_Minus'] = df_wide.Goals + df_wide.Assists + df_wide.Ds - df_wide.Turnovers

    df_wide.to_csv(f'{DATA_DIR}/processed/player_indicators.csv', index=False)

    if return_df:
        return df_wide




if __name__ == '__main__':
    make_team_indicators()
    make_player_indicators()
