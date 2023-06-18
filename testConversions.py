import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
import json

from conversion_utils import *
pd.set_option('display.max_rows', None)


## first set up dataframes -- drop most of the columns in the one we downloaded
## setup result dataframe where we store the results of our tests
team_data_full = pd.read_csv('data/SerieA2022.csv')
team_data = team_data_full[['Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR']].copy()
rankings = pd.DataFrame()
rankings['Team'] = team_data['HomeTeam'].unique()

# I'll save some stats here
result_fom= {}


## Start with the easiest test possible
##    First compute the scores the normal way to confirm we get the real ranking
##    Then assume either the home(away) team always wins the penalties and see how this changes things 

# points for home/away teams
point_mappings = {
  'Real': { 'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':1}},
  'HomeWins': { 'Home': {'H': 3, 'A':0, 'D':2}, 'Away': {'H': 0, 'A':3, 'D':1}},
  'AwayWins': { 'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':2}},
}

# apply them and save results in df
for mapping in point_mappings:

  team_data['HomePoints'] = team_data['FTR'].map(point_mappings[mapping]['Home'])
  team_data['AwayPoints'] = team_data['FTR'].map(point_mappings[mapping]['Away'])

  rankings = compute_rankings(team_data, rankings, mapping)
  rankings, result_fom[mapping] = compare_results(rankings, mapping, 'Real')


print(result_fom)  
# print and plot comparison
print(rankings.sort_values('Real', ascending=False))
print(json.dumps(result_fom, indent=4))
rankings.hist(column=[mp for mp in point_mappings],range=[0,100])
plt.savefig('plots/default.pdf')




###--------------------------------------------------------
###--------------------------------------------------------
###--------------------------------------------------------

## Now for something more real, let's give each time a team draws a 50/50 probability of winning

# first assign the normal point mapping
team_data['HomePoints'] = team_data['FTR'].map(point_mappings['Real']['Home'])
team_data['AwayPoints'] = team_data['FTR'].map(point_mappings['Real']['Away'])




