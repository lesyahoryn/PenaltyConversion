import pandas as pd
import matplotlib.pyplot as plt

## get rankings for the season given home/away points per game and save into output data frame
##    inputData: dataframe with home/away teams and home/away points
##    outputData: dataframe where we are storing the results of the season, must have the team names already set
##    col: column to store the results in 
def compute_score(inputData, outputData, col):
  
  outputData[col] = 0
  for pos in ['Home','Away']: 
    
    # sum home/away points for the season
    tmpdf = inputData.groupby(['%sTeam'%pos], as_index=False)['%sPoints'%pos].sum()
    
    # need to use team names as indices to sum the 'Points'umns correctly
    outputData = outputData.set_index('Team')
    tmpdf = tmpdf.set_index('%sTeam'%pos)

    outputData[col] = outputData[col] + tmpdf['%sPoints'%pos]
      
    outputData = outputData.reset_index()
    inputData = inputData.reset_index()
  
  return outputData
    

## Do some comparison between a control and test scoring system
##    inputData: dataframe with total season points per team
##    control: name of column we want to compare to 
##    test: name of column with scoring system we want to evaluate 
def compare_results(inputData, test, control): 

  resultInfo = {}

  resultInfo['sigma_all'] = getSigma(inputData, 0, 20, test)
  resultInfo['changein_sigma_all'] = getSigma(inputData, 0, 20, test) - getSigma(inputData, 0, 20, control)
  
  resultInfo['sigma_top10'] = getSigma(inputData, 0, 10, test)
  resultInfo['changein_sigma_top10'] = getSigma(inputData, 0, 10, test) - getSigma(inputData, 0, 10, control)
  
  resultInfo['sigma_bottom10'] = getSigma(inputData, 10, 20, test)
  resultInfo['changein_sigma_bottom10'] = getSigma(inputData, 10, 20, test) - getSigma(inputData, 10, 20, control)

  # resultInfo['CL'] = inputData.sort_values(test, ascending=False)['Team'][0:4].tolist()
  # resultInfo['EL'] = inputData.sort_values(test, ascending=False)['Team'][4:7].tolist()
  # resultInfo['relegation'] = inputData.sort_values(test)['Team'][0:3].tolist()

  return resultInfo 


#get standard deviation - uses numpy std
def getSigma(inputData, startPos, endPos, column):
  return float(inputData.sort_values(column, ascending=False)[startPos:endPos][column].std())

# Initialize a new results dataframe, and compute the real score from the season
def newTeamDFWithRealScore(inputData, point_mapping = {'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':1}}):
  
  outputData = pd.DataFrame()
  outputData['Team'] = inputData['HomeTeam'].unique()

  inputData['HomePoints'] = inputData['FTR'].map(point_mapping['Home'])
  inputData['AwayPoints'] = inputData['FTR'].map(point_mapping['Away'])
  outputData = compute_score(inputData, outputData, 'Real')

  return outputData

################
## Plotters
################

## Histogram from list
def histoFromList(inputData, title, xlabel, savename, nbins, range):
    plt.hist( inputData, bins=nbins, range=range )
    plt.title( title )
    plt.xlabel( xlabel )
    plt.savefig( savename )
    plt.close()

## Plot one distribution per team in dataframe
def plotPerTeam(inputData, control, xlabel, savename):
    
    axes = inputData.set_index('Team').T.hist(column = inputData['Team'].to_list(), figsize = (14,16))
    for ax in axes.flatten():
      ax.axvline( x = inputData.set_index('Team')[control][ax.get_title()], color='black' , label='Actual Result')
      ax.legend(loc='upper right')
      ymin, ymax = ax.get_ylim()
      ax.set_ylim( ymin, ymax*1.5 )
      ax.set_xlabel(xlabel)
      ax.set_ylabel("Entries")
    plt.savefig(savename)
    plt.close()
