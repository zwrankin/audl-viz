import pandas as pd


def GetPlayers(df):
    return df['Lineup'].str.split(', ').apply(pd.Series).stack().unique()

def GetGamesPlayed(df):
    return df.groupby(['GameID']).ngroups
def GetQuartersPlayed(df):
    return df.groupby(['GameID','QuarterID']).ngroups
def GetPointsPlayed(df):
    return df[(df['Event Type']!='Cessation')].groupby(['GameID','PointID']).ngroups
def GetPossessionsPlayed(df):
    return df[(df['Event Type']=='Offense')].groupby(['GameID','PointID','PossessionID']).ngroups

def GetPointsWon(df):
    return df[(df['Event Type']=='Offense')&(df.Action=='Goal')].groupby(['GameID','PointID']).ngroups
def GetPointsLost(df):
    return df[(df['Event Type']=='Defense')&(df.Action=='Goal')].groupby(['GameID','PointID']).ngroups

def GetOPointsWon(df):
    return df[(df['Event Type']=='Offense')
              &(df.Action=='Goal')
              &(df.Line=='O')].groupby(['GameID','PointID']).ngroups
def GetOPointsLost(df):
    return df[(df['Event Type']=='Defense')
              &(df.Action=='Goal')
              &(df.Line=='O')].groupby(['GameID','PointID']).ngroups

def GetDPointsWon(df):
    return df[(df['Event Type']=='Offense')
              &(df.Action=='Goal')
              &(df.Line=='D')].groupby(['GameID','PointID']).ngroups
def GetDPointsLost(df):
    return df[(df['Event Type']=='Defense')
              &(df.Action=='Goal')
              &(df.Line=='D')].groupby(['GameID','PointID']).ngroups

def GetOPointsPlayed(df):
    return df[(df['Event Type']!='Cessation') & (df.Line=='O')].groupby(['GameID','PointID']).ngroups
def GetOPossessionsPlayed(df):
    return df[(df.Line=='O')&(df['Event Type']=='Offense')].groupby(['GameID','PointID','PossessionID']).ngroups
def GetOppOPossessionsPlayed(df):
    return df[(df.Line=='O')&(df['Event Type']=='Defense')].groupby(['GameID','PointID','PossessionID']).ngroups

def GetDPointsPlayed(df):
    return df[(df['Event Type']!='Cessation') & (df.Line=='D')].groupby(['GameID','PointID']).ngroups
def GetDPossessionsPlayed(df):
    return df[(df.Line=='D')&(df['Event Type']=='Offense')].groupby(['GameID','PointID','PossessionID']).ngroups
def GetOppDPossessionsPlayed(df):
    return df[(df.Line=='D')&(df['Event Type']=='Defense')].groupby(['GameID','PointID','PossessionID']).ngroups


def PlayStatsByPlayer(df_raw):
    plyrs = GetPlayers(df_raw)
    dfs = []
    for p in plyrs:
        df = df_raw[df_raw['Lineup'].str.contains(p,na=False)]
        df_p = pd.DataFrame({'player': p,
                             'Games Played': GetGamesPlayed(df),
                             'Quarters Played': GetQuartersPlayed(df),
                             'Points Played': GetPointsPlayed(df),
                             'Possessions Played': GetPossessionsPlayed(df),
                             'Points Played (Offense)': GetOPointsPlayed(df),
                             'Possessions Played (Offense)': GetOPossessionsPlayed(df),
                             'Opp Possessions Played (Offense)': GetOppOPossessionsPlayed(df),
                             'Points Played (Defense)': GetDPointsPlayed(df),
                             'Possessions Played (Defense)': GetOPossessionsPlayed(df),
                             'Opp Possessions Played (Defense)': GetOppDPossessionsPlayed(df),
                             'Points Won': GetPointsWon(df),
                             'Points Lost': GetPointsLost(df),
                             'Points Won (Offense)': GetOPointsWon(df),
                             'Points Lost (Offense)': GetOPointsLost(df),
                             'Points Won (Defense)': GetDPointsWon(df),
                             'Points Lost (Defense)': GetDPointsLost(df),
                             }, index=[0])
        # print(len(df_p))
        dfs.append(df_p)

    return pd.concat(dfs, ignore_index=True)


def calculate_conversion_rates(df):
    df['conversion rate (Offense)'] = df['Points Won (Offense)'] / df['Points Played (Offense)']
    df['conversion rate (Defense)'] = df['Points Won (Defense)'] / df['Points Played (Defense)']
    return df

# O-line conversion rate (% of O possessions scored)
#
# D-line conversion rate (% of D possessions scored)
#
# O-line block rate
#
# D-line block rate
#
# O-line clean conversion rate (% of O possessions without a turn)
#
# D-line opportunity rate (% of D lines that get at least one turn)
