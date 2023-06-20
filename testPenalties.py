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

team_data, ranks, scores, foms, mc_ranks, mc_scores, mc_foms, rank_changes, score_changes = ({} for i in range(9))
rank_changes['all'] = []
score_changes['all'] = []
years_to_plot = []

plotPathSummary = './plots/summary'
if not os.path.exists(plotPathSummary): os.makedirs(plotPathSummary)

## Datasets are per year, so do processing per year
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

    # I should do this in a more panda-y way, but it is low priority for me at the moment
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
    ranks[year] = newTeamDFWithRealScore(team_data[year])  # rank 1-20
    ranks[year]['RealRank'] = scores[year]['Real'].rank(ascending=False, method='max')
    ranks[year] = ranks[year].drop('Real', axis=1)


    # I'll save some stats here to plot later and see how things change
    foms[year]= {}
    # apply them and save results in df
    for mapping in ['HomeWins', 'AwayWins']:

      team_data[year]['HomePoints'] = team_data[year]['FTR'].map(point_mappings[mapping]['Home'])
      team_data[year]['AwayPoints'] = team_data[year]['FTR'].map(point_mappings[mapping]['Away'])

      scores[year] = compute_score(team_data[year], scores[year], mapping)
      foms[year][mapping] = compare_results(scores[year], mapping, 'Real')
      ranks[year]['%sRank'%mapping] = scores[year][mapping].rank(ascending=False, method='max')

    print(ranks[year])
    print(scores[year])
    #print(json.dumps(foms[year], indent=4))  #uncomment to dump the foms
    
    # plot score distribution
    scores[year].hist(column=['Real', 'HomeWins', 'AwayWins'], range=[0,100])
    plt.savefig(plotPath+'/simpleTest.pdf')

    scores[year].to_csv(plotPath+'/simpleScores.csv')
    ranks[year].to_csv(plotPath+'/simpleRanks.csv')


  ###--------------------------------------------------------
  ### Now let's study the idea bit more scientifically -
  ###  - Simulate the penalty shoot out -- 5 penalties then sudden death
  ###  - Each penalty has flat 50% chance of success 
  ###  - Run the season many times and statistically study result
  ###--------------------------------------------------------
  if args.mcPenalties:

    ## Setup new dataframe to store results of our tests
    mc_foms[year] = {}
    rank_changes[year], score_changes[year] = ([] for i in range(2))

    # Set up score dataframe and save foms for Real result
    mc_scores[year] = newTeamDFWithRealScore(team_data[year])  #total score
    mc_foms[year]['Real'] = compare_results(mc_scores[year], 'Real', 'Real')
    
    # Set up rank dataframe
    mc_ranks[year] = newTeamDFWithRealScore(team_data[year])  #rank 
    mc_ranks[year]['RealRank'] = mc_ranks[year]['Real'].rank(ascending=False, method='max')
    mc_ranks[year] = mc_ranks[year].drop('Real', axis=1)

    ## Perform the simulation 
    nIters = 1000
    ranks = {}
    for i in range(0, nIters):

      tmpdf = team_data[year].copy()

      # This is the actual simulation -- if 'D' is the full time result, go to a penalty shootout! 
      tmpdf['FTR'] = tmpdf['FTR'].map(lambda x: penaltyMap(x))
      
      # Compute the points again now that we've updated the table
      tmpdf['HomePoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Home'])
      tmpdf['AwayPoints'] = tmpdf['FTR'].map(point_mappings['Modified']['Away'])
      
      # Compute and save the scores for this iteration
      mc_scores[year] = compute_score(tmpdf, mc_scores[year], 'Modified%i'%i)
      mc_foms[year]['Modified%i'%i] = compare_results(mc_scores[year], 'Modified%i'%i, 'Real')
    
      # save the season rank as well
      ranks['Modified%i'%i] = mc_scores[year]['Modified%i'%i].rank(ascending=False, method='max').to_list()
      rank_changes[year].extend(mc_ranks[year]['RealRank'].sub( mc_scores[year]['Modified%i'%i].rank(ascending=False, method='max')).to_list()  ) 
      score_changes[year].extend( mc_scores[year]['Modified%i'%i].sub(mc_scores[year]['Real']).to_list()  )


    # This is a more performant way to add in the ranks, will update the scores as well if I can.
    mc_ranks[year] = pd.concat([mc_ranks[year], pd.DataFrame(ranks)], axis=1)

    score_changes['all'].extend(score_changes[year])
    rank_changes['all'].extend(rank_changes[year])

    mc_scores[year].to_csv(plotPath+'/mcTest_scores.csv')
    mc_ranks[year].to_csv(plotPath+'/mcTest_ranks.csv')


    ##################
    #### Plotting ####
    ##################

    # Plot score/rank distribution per team 
    plotPerTeam(mc_scores[year], 'Real', 'Season Score', plotPath+'/mcTest_team_scores.pdf')
    plotPerTeam(mc_ranks[year], 'RealRank', 'Season Rank', plotPath+'/mcTest_team_ranks.pdf')

    #simple histogram of rank/score change
    histoFromList( rank_changes[year], 'Change in rank per team per iteration', 'Change in Rank (real - test)', plotPath+'/mcTest_rank_changes.pdf', 12, [-6,6])
    histoFromList( score_changes[year], 'Change in score per team per iteration', 'Change in Score (test - real)', plotPath+'/mcTest_score_changes.pdf', 20, [0,20])


    # Plot aggregate FOMs defined in compare_results in penaltyUtils.py
    foms_to_plot = list(mc_foms[year]['Real'].keys())
    plt.figure(figsize=(8,6)) # reset default
    for f in foms_to_plot:
      plt.hist( [ mc_foms[year][z][f] for z in mc_foms[year] ], label=f )
      plt.axvline( x = mc_foms[year]['Real'][f], color='black' , label='Actual Result')
      plt.legend(loc='upper right')
      plt.savefig(plotPath+'/mcTest_%s.pdf'%f)
      plt.close()


if args.mcPenalties:
  #simple histogram of rank/score change
  histoFromList( rank_changes['all'], 'Change in rank per team per iteration (all years combined)', 'Change in Rank (real - test)', plotPathSummary+'/mcTest_rank_changes.pdf', 12, [-6,6])
  histoFromList( score_changes['all'], 'Change in score per team per iteration (all years combined)', 'Change in Score (test - real)', plotPathSummary+'/mcTest_score_changes.pdf', 20, [0,20])


  ## Compare sigma spread across years
  colors = plt.cm.jet(np.linspace(0,1,len(years_to_plot)))
  bins = np.linspace(-3, 3, 20)
  
  for f in list(mc_foms[year]['Real'].keys()):
    
    if 'change' not in f: continue
    
    for i, year in enumerate(years_to_plot):
      plt.hist( [mc_foms[year][z][f] for z in mc_foms[year]], bins, linewidth=1.2, facecolor='none', histtype = 'step', label=year, edgecolor=colors[i])    
    
    plt.axvline(x=0, color='black')
    plt.legend(loc='upper right')
    plt.title(f.split('_')[-1])
    plt.xlabel('Change in Standard Deviation (test - Real)')
    plt.ylabel('Events')
    plt.savefig(plotPathSummary+'/compare_%s.pdf'%f)
    plt.close()
