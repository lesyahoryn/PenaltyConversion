import pandas as pd

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

  #inputData['%s_PointDiff'%test] = inputData[test] - inputData[control]

  resultInfo['spread'] = int(inputData[test].max() - inputData[test].min())
  resultInfo['spread_top10'] = int(inputData.sort_values(test, ascending=False)[0:10][test].max()) - int(inputData.sort_values(test, ascending=False)[0:10][test].min())
  resultInfo['spread_bottom10'] = int(inputData.sort_values(test, ascending=False)[10:20][test].max()) - int(inputData.sort_values(test, ascending=False)[10:20][test].min())
  resultInfo['spread_middle10'] = int(inputData.sort_values(test, ascending=False)[6:15][test].max()) - int(inputData.sort_values(test, ascending=False)[6:15][test].min())
  resultInfo['spread_noTopBottom'] = int(inputData.sort_values(test, ascending=False)[1:18][test].max()) - int(inputData.sort_values(test, ascending=False)[1:18][test].min())
  resultInfo['CL'] = inputData.sort_values(test, ascending=False)['Team'][0:4].tolist()
  resultInfo['EL'] = inputData.sort_values(test, ascending=False)['Team'][4:7].tolist()
  resultInfo['relegation'] = inputData.sort_values(test)['Team'][0:3].tolist()

  return inputData, resultInfo 


# Initialize a new results dataframe, and compute the real score from the season
def newTeamDFWithRealScore(inputData, point_mapping = {'Home': {'H': 3, 'A':0, 'D':1}, 'Away': {'H': 0, 'A':3, 'D':1}}):
  
  outputData = pd.DataFrame()
  outputData['Team'] = inputData['HomeTeam'].unique()

  inputData['HomePoints'] = inputData['FTR'].map(point_mapping['Home'])
  inputData['AwayPoints'] = inputData['FTR'].map(point_mapping['Away'])
  outputData = compute_score(inputData, outputData, 'Real')

  return outputData


