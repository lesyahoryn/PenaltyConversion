import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
import json
import argparse

## libraries in this project
from conversion_utils import *
from penaltyShootout import * 

pd.set_option('display.max_rows', None)


## Set up arg parse to change which tests we see the output of
parser = argparse.ArgumentParser(
                    prog='testConversions',
                    description='Different ways of playing with extra penalty conversion point')

parser.add_argument('--simpleTest', action='store_true')
parser.add_argument('--mcPenalties', action='store_true')
parser.add_argument('--year', type=str, help="choose any year 2005 to 2022")
args = parser.parse_args()

## first set up dataframes -- drop most of the columns in the one we downloaded
## TODO: make this run over several years
team_data_full = pd.read_csv('data/SerieA%s.csv'%args.year)
team_data = team_data_full[['Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR']].copy()

# points for home/away teams
point_mappings = {
  'Real':     { 'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':1}},
  'HomeWins': { 'Home': {'H': 3, 'A':0, 'D':2}, 'Away': {'H': 0, 'A':3, 'D':1}},
  'AwayWins': { 'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':2}},
  'Modified': { 'Home': {'H': 3, 'A':0, 'D':1, 'DH': 2, 'DA': 1}, 'Away': {'H': 0, 'A':3, 'D':1, 'DH': 1, 'DA': 2}},
}


if args.simpleTest:
  ## Start with the easiest test possible
  ##    First compute the scores the normal way to confirm we get the real ranking
  ##    Then assume either the home(away) team always wins the penalties and see how this changes things 

  ## setup result dataframe where we store the results of our tests
  rankings = pd.DataFrame()
  rankings['Team'] = team_data['HomeTeam'].unique()

  # I'll save some stats here to print out later and see how things change
  result_fom= {}
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
  rankings.hist(column=[mp for mp in point_mappings], range=[0,100])
  plt.savefig('plots/simpleTest%s.pdf'%args.year)


###--------------------------------------------------------
###--------------------------------------------------------
###--------------------------------------------------------


if args.mcPenalties:
  ## Now for something more real, let's give each time a team draws a 50/50 probability of winning

  # first assign the normal point mapping
  team_data['HomePoints'] = team_data['FTR'].map(point_mappings['Real']['Home'])
  team_data['AwayPoints'] = team_data['FTR'].map(point_mappings['Real']['Away'])

  ## Setup new dataframe to store results of our tests
  mc_results = pd.DataFrame()
  mc_results['Team'] = team_data['HomeTeam'].unique()
  mc_results = compute_rankings(team_data, mc_results, 'Real')
  nIters = 10
  result_fom = {}
  
  for i in range(0, nIters):
    tmpdf = team_data.copy()
    tmpdf['FTR'] = tmpdf['FTR'].map(lambda x: penaltyMap(x))
    tmpdf['HomePoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Home'])
    tmpdf['AwayPoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Away'])
    print(tmpdf.loc[[10]])
    
    mc_results = compute_rankings(tmpdf, mc_results, 'Modified%i'%i)
    mc_results, result_fom['Modified%i'%i] = compare_results(mc_results, 'Modified%i'%i, 'Real')

print(mc_results.sort_values('Real', ascending=False))
mc_results.hist(column = list(result_fom.keys()).append('Real'), range=[0,100])
plt.savefig('plots/mcTest%s.pdf'%args.year)
