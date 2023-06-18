import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
import json
import argparse

## libraries in this project
from penaltyUtils import *
from penaltyShootout import * 

parser = argparse.ArgumentParser(
                    prog='testConversions',
                    description='Different ways of playing with extra penalty conversion point')

parser.add_argument('--simpleTest', action='store_true', help='run simple application of new rule' )
parser.add_argument('--mcPenalties', action='store_true', help='run Monte Carlo simulation of new rule')
parser.add_argument('--dumpStats', action='store_true', help='Print out some information about teams in this year')
parser.add_argument('--year', type=str, help='choose any year 2005 to 2022')
args = parser.parse_args()

# Possible points for game results
# H: home win, A: away win D: draw
# my addition: DA: draw with away winning penalties, DH: draw with home winning penalties
point_mappings = {
  'Real':     { 'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':1}},
  'HomeWins': { 'Home': {'H': 3, 'A':0, 'D':2}, 'Away': {'H': 0, 'A':3, 'D':1}},
  'AwayWins': { 'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':2}},
  'Modified': { 'Home': {'H': 3, 'A':0, 'D':1, 'DH': 2, 'DA': 1}, 'Away': {'H': 0, 'A':3, 'D':1, 'DH': 1, 'DA': 2}},
}

## first set up dataframes -- drop most of the columns in the one we downloaded
## TODO: make this run over several years
team_data_full = pd.read_csv('data/SerieA%s.csv'%args.year)
team_data = team_data_full[['Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR']].copy()

plotPath = './plots/'+args.year
if not os.path.exists(plotPath): os.makedirs(plotPath)

###--------------------------------------------------------
### Learn some stuff about how the different teams did in this year
###  in particular some stuff that impacts how the new rule would change things
###  - Number of draws per team
###--------------------------------------------------------
if args.dumpStats:
  
  team_data_draws = team_data[team_data['FTR'] == 'D']

  # there should be a way to do this in a more panda-y way, but it is low priority for me at the moment.
  for team in team_data['HomeTeam'].unique().tolist():
    print(team, len(team_data_draws[ team_data_draws['HomeTeam'] == team]) + len(team_data_draws[ team_data_draws['AwayTeam'] == team]) )


###--------------------------------------------------------
### Start with some sanity checks and simplest modification possible
###  - First compute the scores with standard point allocation, 
###    and confirm that I reproduce the real result table (ignoring disciplinary point changes)
###  - Assign an extra point to one team in the draw, for now always assign to either home or away
###  - Define some figures of merit (FOM) to compare to real result
###--------------------------------------------------------
if args.simpleTest:

  ## setup result dataframe where we store the results of our tests
  scores = newTeamDFWithRealScore(team_data)  # total score
  ranks = newTeamDFWithRealScore(team_data)  # total score
  ranks['RealRank'] = scores['Real'].rank(ascending=False, method='max')
  ranks = ranks.drop('Real', axis=1)


  # I'll save some stats here to print out later and see how things change
  result_fom= {}
  # apply them and save results in df
  for mapping in ['HomeWins', 'AwayWins']:

    team_data['HomePoints'] = team_data['FTR'].map(point_mappings[mapping]['Home'])
    team_data['AwayPoints'] = team_data['FTR'].map(point_mappings[mapping]['Away'])

    scores = compute_score(team_data, scores, mapping)
    scores, result_fom[mapping] = compare_results(scores, mapping, 'Real')
    ranks['%sRank'%mapping] = scores[mapping].rank(ascending=False, method='max')

  print(ranks)
  print(scores)
  #print(json.dumps(result_fom, indent=4))
  scores.hist(column=['Real', 'HomeWins', 'AwayWins'], range=[0,100])
  plt.savefig(plotPath+'/simpleTest.pdf')


###--------------------------------------------------------
### Now let's study the idea bit more scientifically -
###  - Simulate the penalty shoot out -- 5 penalties then sudden death
###  - Each penalty has flat 50% chance of success 
###  - Run the season many times and statistically study result
###--------------------------------------------------------
if args.mcPenalties:

  ## Setup new dataframe to store results of our tests
  result_fom = {}
  mc_scores = newTeamDFWithRealScore(team_data)  #total score
  mc_scores, result_fom['Real'] = compare_results(mc_scores, 'Real', 'Real')
  
  mc_ranks = newTeamDFWithRealScore(team_data)  #rank 
  mc_ranks['RealRank'] = mc_ranks['Real'].rank(ascending=False, method='max')
  mc_ranks = mc_ranks.drop('Real', axis=1)

  ## Perform the simulation 
  nIters = 1000
  ranks = {}
  for i in range(0, nIters):
    tmpdf = team_data.copy()

    # Redo the FTR column so that if there is a draw, we simulate a penalty shootout. 
    tmpdf['FTR'] = tmpdf['FTR'].map(lambda x: penaltyMap(x))
    
    # Compute the points again now that we've updated the table
    tmpdf['HomePoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Home'])
    tmpdf['AwayPoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Away'])
    
    # Compute and save the scores for this iteration
    mc_scores = compute_score(tmpdf, mc_scores, 'Modified%i'%i)
    mc_scores, result_fom['Modified%i'%i] = compare_results(mc_scores, 'Modified%i'%i, 'Real')

    # save the season rank as well
    ranks['Modified%i'%i] = mc_scores['Modified%i'%i].rank(ascending=False, method='max').to_list()

  # This is a more performant way to add in the ranks, will update the scores as well if I can.
  mc_ranks = pd.concat([mc_ranks, pd.DataFrame(ranks)], axis=1)

  # Plot score distribution per team 
  mc_scores.set_index('Team').T.hist(column = mc_scores['Team'].to_list(), figsize = (16,18))
  plt.savefig(plotPath+'/mcTest_team_scores.pdf')
  plt.clf()

  # Plot rank distribution per team 
  mc_ranks.set_index('Team').T.hist(column = mc_scores['Team'].to_list(), figsize = (16,18), )
  plt.savefig(plotPath+'/mcTest_teams_ranks.pdf')
  plt.clf()

  # Plot aggregate FOMs defined in compare_results in penaltyUtils.py
  foms = list(result_fom['Real'].keys())
  plt.figure(figsize=(8,6))
  for f in foms:
    if 'spread' not in f: continue
    plt.hist( [ result_fom[y][f] for y in result_fom ], label='spread in ' + f.split("_")[-1] )
    plt.axvline( x = result_fom['Real'][f], color='black' , label='Actual Result')
    plt.legend(loc='upper right')
    plt.savefig(plotPath+'/mcTest_%s.pdf'%f)
    plt.clf()





