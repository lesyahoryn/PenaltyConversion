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
parser.add_argument('--years', type=str, help='choose any years 2005 to 2022 in comma separated list, if nothing is given will do all years')
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

team_data = {}
ranks = {}
scores = {}
foms = {}
mc_ranks = {}
mc_scores = {}
mc_foms = {}
years_to_plot = []

plotPathSummary = './plots/summary'
if not os.path.exists(plotPathSummary): os.makedirs(plotPathSummary)

for yr  in range(2005,2023):

  year = str(yr)
  if args.years is not None and str(year) not in args.years: continue

  print("Running year", year)
  years_to_plot.append(year)

  ## first set up dataframes -- drop most of the columns in the one we downloaded
  team_data_full = pd.read_csv('data/SerieA%s.csv'%year)
  team_data[year] = team_data_full[['Date','HomeTeam','AwayTeam','FTHG','FTAG','FTR']].copy()

  plotPath = './plots/'+year
  if not os.path.exists(plotPath): os.makedirs(plotPath)

  ###--------------------------------------------------------
  ### Learn some stuff about how the different teams did in this year
  ###  in particular some stuff that impacts how the new rule would change things
  ###  - Number of draws per team
  ###--------------------------------------------------------
  if args.dumpStats:
    
    team_data_draws = team_data[year][team_data[year]['FTR'] == 'D']

    # I should do this in a more panda-y way, but it is low priority for me at the moment.
    print('Draws per team in ', year)
    for team in team_data[year]['HomeTeam'].unique().tolist():
      print(team, len(team_data_draws[ team_data_draws['HomeTeam'] == team]) + len(team_data_draws[ team_data_draws['AwayTeam'] == team]) )
    print('\n')


  ###--------------------------------------------------------
  ### Start with some sanity checks and simplest modification possible
  ###  - First compute the scores with standard point allocation, 
  ###    and confirm that I reproduce the real result table (ignoring disciplinary point changes)
  ###  - Assign an extra point to one team in the draw, for now always assign to either home or away
  ###  - Define some figures of merit (FOM) to compare to real result
  ###--------------------------------------------------------
  if args.simpleTest:

    ## setup result dataframe where we store the results of our tests
    scores[year] = newTeamDFWithRealScore(team_data[year])  # total score
    ranks[year] = newTeamDFWithRealScore(team_data[year])  # total score
    ranks[year]['RealRank'] = scores[year]['Real'].rank(ascending=False, method='max')
    ranks[year] = ranks[year].drop('Real', axis=1)


    # I'll save some stats here to print out later and see how things change
    foms[year]= {}
    # apply them and save results in df
    for mapping in ['HomeWins', 'AwayWins']:

      team_data[year]['HomePoints'] = team_data[year]['FTR'].map(point_mappings[mapping]['Home'])
      team_data[year]['AwayPoints'] = team_data[year]['FTR'].map(point_mappings[mapping]['Away'])

      scores[year] = compute_score(team_data[year], scores[year], mapping)
      scores[year], foms[year][mapping] = compare_results(scores[year], mapping, 'Real')
      ranks[year]['%sRank'%mapping] = scores[year][mapping].rank(ascending=False, method='max')

    print(ranks[year])
    print(scores[year])
    #print(json.dumps(foms[year], indent=4))
    scores[year].hist(column=['Real', 'HomeWins', 'AwayWins'], range=[0,100])
    plt.savefig(plotPath+'/simpleTest.pdf')


  ###--------------------------------------------------------
  ### Now let's study the idea bit more scientifically -
  ###  - Simulate the penalty shoot out -- 5 penalties then sudden death
  ###  - Each penalty has flat 50% chance of success 
  ###  - Run the season many times and statistically study result
  ###--------------------------------------------------------
  if args.mcPenalties:

    ## Setup new dataframe to store results of our tests
    mc_foms[year] = {}
    mc_scores[year] = newTeamDFWithRealScore(team_data[year])  #total score
    mc_scores[year], mc_foms[year]['Real'] = compare_results(mc_scores[year], 'Real', 'Real')
    
    mc_ranks[year] = newTeamDFWithRealScore(team_data[year])  #rank 
    mc_ranks[year]['RealRank'] = mc_ranks[year]['Real'].rank(ascending=False, method='max')
    mc_ranks[year] = mc_ranks[year].drop('Real', axis=1)

    ## Perform the simulation 
    nIters = 1000
    ranks = {}
    for i in range(0, nIters):
      tmpdf = team_data[year].copy()

      # Redo the FTR column so that if there is a draw, we simulate a penalty shootout. 
      tmpdf['FTR'] = tmpdf['FTR'].map(lambda x: penaltyMap(x))
      
      # Compute the points again now that we've updated the table
      tmpdf['HomePoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Home'])
      tmpdf['AwayPoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Away'])
      
      # Compute and save the scores for this iteration
      mc_scores[year] = compute_score(tmpdf, mc_scores[year], 'Modified%i'%i)
      mc_scores[year], mc_foms[year]['Modified%i'%i] = compare_results(mc_scores[year], 'Modified%i'%i, 'Real')

      # save the season rank as well
      ranks['Modified%i'%i] = mc_scores[year]['Modified%i'%i].rank(ascending=False, method='max').to_list()

    # This is a more performant way to add in the ranks, will update the scores as well if I can.
    mc_ranks[year] = pd.concat([mc_ranks[year], pd.DataFrame(ranks)], axis=1)

    # Plot score distribution per team 
    axes = mc_scores[year].set_index('Team').T.hist(column = mc_scores[year]['Team'].to_list(), figsize = (14,16))
    for ax in axes.flatten():
      ax.axvline( x = mc_scores[year].set_index('Team')['Real'][ax.get_title()], color='black' , label='Actual Result')
      ax.legend(loc='upper right')
      ymin, ymax = ax.get_ylim()
      ax.set_ylim( ymin, ymax*1.5 )
      ax.set_xlabel("Season Score")
      ax.set_ylabel("Entries")
    plt.savefig(plotPath+'/mcTest_team_scores.pdf')
    plt.close()

    # Plot rank distribution per team 
    axes = mc_ranks[year].set_index('Team').T.hist(column = mc_scores[year]['Team'].to_list(), figsize = (14,16))
    for ax in axes.flatten():
      ax.axvline( x = mc_ranks[year].set_index('Team')['RealRank'][ax.get_title()], color='black' , label='Actual Result')
      ax.legend(loc='upper right')
      ymin, ymax = ax.get_ylim()
      ax.set_ylim( ymin, ymax*1.5 )
      ax.set_xlabel("Season Rank")
      ax.set_ylabel("Entries") 
    plt.savefig(plotPath+'/mcTest_teams_ranks.pdf')
    plt.close()

    # Plot aggregate FOMs defined in compare_results in penaltyUtils.py
    foms_to_plot = list(mc_foms[year]['Real'].keys())
    plt.figure(figsize=(8,6)) # reset default
    for f in foms_to_plot:
      if 'spread' not in f: continue
      if 'change' in f: lab = 'change  in spread in ' + f.split("_")[-1] + '(test - real)'
      else: lab = 'change  in spread in ' + f.split("_")[-1] + '(test - real)'
      
      plt.hist( [ mc_foms[year][z][f] for z in mc_foms[year] ], label=lab )
      plt.axvline( x = mc_foms[year]['Real'][f], color='black' , label='Actual Result')
      plt.legend(loc='upper right')
      plt.savefig(plotPath+'/mcTest_%s.pdf'%f)
      plt.close()



## Now for some summary plotting to decide if my idea is a good one
# TODO: I would like a better way to visualize how much the ranking changes
bins = np.linspace(-10, 10, 15)
colors = plt.cm.jet(np.linspace(0,1,len(years_to_plot)))

foms_to_plot = list(mc_foms[year]['Real'].keys())
for f in foms_to_plot:
  if 'change' not in f: continue
  for i, year in enumerate(years_to_plot):
    plt.hist( [mc_foms[year][z][f] for z in mc_foms[year]], bins, linewidth=1.2, facecolor='none', histtype = 'step', label=year, edgecolor=colors[i])
    #plt.hist( [mc_foms[year][z][f] for z in mc_foms[year]], bins, alpha=0.5, label=year, color=colors[i])
  
  plt.axvline(x=0, color='black')
  plt.legend(loc='upper right')
  plt.title(f.split('_')[-1])
  plt.xlabel('Change in spread (test - Real)')
  plt.ylabel('Events')
  plt.savefig(plotPathSummary+'/compare_%s.pdf'%f)
  plt.close()







