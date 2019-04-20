import pandas as pd
from .utils import DATA_DIR, load_raw_data

index_vars = ['year', 'team', 'opponent', 'date', 'game']
team_indicators = ['Goals', 'Catches', 'Ds', 'Turnovers', 'Drops', 'Throwaways', 'Goals_against',
                  'Hold_pct', 'Break_pct']
team_eoy_indicators = team_indicators + ['Win_pct'] # ['Win_pct', 'Hold_pct', 'Break_pct']
player_indicators  = ['Completions', 'Assists', 'Throwaways', 'Receptions', 'Goals', 'Drops', 'Ds',
                      'Turnovers', 'Plus_Minus', 'Points Played', 'Games Played']


# TODO - These functions taken from audl-pull, need to refactor!
def GetPlayers(df_in):
    return df_in['Lineup'].str.split(', ').apply(pd.Series).stack().unique()
def GetGamesPlayed(df_in,plyr):
    return df_in[df_in['Lineup'].str.contains(plyr,na=False)].groupby(['GameID']).ngroups
def GetPointsPlayed(df_in,plyr):
    return df_in[(df_in['Event Type']!='Cessation') & df_in['Lineup'].str.contains(plyr,na=False)].groupby(['GameID','PointID']).ngroups
def PlayStatsByPlayer(df_in):
    plyrs = GetPlayers(df_in)
    return pd.DataFrame([{'player': p,
                          'Games Played': GetGamesPlayed(df_in,p),
                          'Points Played': GetPointsPlayed(df_in,p)
                          } for p in plyrs])


def make_team_indicators(return_df = False):

    df = load_raw_data()

    # Make indicators
    dummies = pd.get_dummies(df['Action'])
    df = pd.concat([df, dummies], axis=1)
    df['Turnovers'] = df.Throwaway + df.Drop
    # For goals, we want to separate whether the team is on Offense or Defense
    df['Goals_against'] = 0
    df.loc[df['Event Type'] == 'Defense', 'Goals_against'] = df['Goal']
    df.loc[df['Event Type'] == 'Defense', 'Goal'] = 0
    
    is_goal = df['Action'] == "Goal"
    is_oline = df['Line'] == 'O'
    df.loc[(is_goal) & (is_oline) & (df['Event Type'] == 'Offense'), 'Hold_pct'] = 1
    df.loc[(is_goal) & (is_oline) & (df['Event Type'] == 'Defense'), 'Hold_pct'] = 0
    df.loc[(is_goal) & (~is_oline) & (df['Event Type'] == 'Offense'), 'Break_pct'] = 1
    df.loc[(is_goal) & (~is_oline) & (df['Event Type'] == 'Defense'), 'Break_pct'] = 0
    
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
    # df_wide = df.groupby(index_vars)[team_indicators].sum().reset_index()
    df_wide = pd.merge(
        df.groupby(index_vars)[[i for i in team_indicators if 'pct' not in i]].sum().reset_index(),
        df.groupby(index_vars)[[i for i in team_indicators if 'pct' in i]].mean().reset_index(),
        on=index_vars, how='outer')
    df_wide.to_csv(f'{DATA_DIR}/processed/team_indicators.csv', index=False)
    
    # Yearly team statistics
    game_over = df.Action == 'GameOver'
    scored_more_points = df['Our Score - End of Point'] > df['Their Score - End of Point']
    df.loc[(game_over) & (scored_more_points), 'Win_pct'] = 1
    df.loc[(game_over) & (~scored_more_points), 'Win_pct'] = 0
    df_final = pd.merge(
        df.groupby(['year', 'team'])[[i for i in team_eoy_indicators if 'pct' not in i]].sum().reset_index(),
        df.groupby(['year', 'team'])[[i for i in team_eoy_indicators if 'pct' in i]].mean().reset_index(),
        on=['year', 'team'], how='outer')
    df_final.to_csv(f'{DATA_DIR}/processed/team_indicators_EOY.csv', index=False)

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

    df_all = pd.concat([df_p, df_r, df_d], sort=False)

    inds = [i for i in player_indicators if i not in ['Turnovers', 'Plus_Minus', 'Points Played', 'Games Played']]
    df_wide = df_all.groupby(index_vars + ['player'])[inds].sum().reset_index()

    # Points played
    df_points = df.groupby('game').apply(PlayStatsByPlayer).reset_index().drop('level_1', axis=1)
    df_wide = pd.merge(df_wide, df_points)

    # Aggregates:
    df_wide['Turnovers'] = df_wide.Throwaways + df_wide.Drops
    df_wide['Plus_Minus'] = df_wide.Goals + df_wide.Assists + df_wide.Ds - df_wide.Turnovers

    df_wide.to_csv(f'{DATA_DIR}/processed/player_indicators.csv', index=False)

    if return_df:
        return df_wide

def save_all_goals(return_df=False):
    """Save all goals in format for Sanke plots"""
    df = load_raw_data()
    cols = ['team', 'year', 'Passer', 'Receiver', 'Line']
    df = df.loc[(df.Action == "Goal") & (df['Event Type'] == 'Offense')][cols].dropna(how='any')
    df.to_csv(f'{DATA_DIR}/processed/all_goals.csv', index=False)
    if return_df:
        return df


if __name__ == '__main__':
    make_team_indicators()
    make_player_indicators()
    save_all_goals()
