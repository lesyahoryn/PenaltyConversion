# Penalty Conversions

## Main concept

My favorite part of any championship is the penalty shootout and I think that the threat of the penalty shootout helps makes these games feel more competitive. I half joked that there should be a point for a penalty shootout during the normal league, for some extra spice. 

My proposed rules are: no extra time, but if there is a tie at the end of 90 minutes, a penalty shootout commences. It will follow the normal rules (5 penalties per team, then one-one until someone wins. The team that wins the penalty shootout gets an extra point in addition to the normal ones allocated for ties. So if team A and team B tie, then team B wins the shootout, team A gets 1 point and team B gets 2 points. 

I wanted to see what impact my idea would have on a league season. Here I picked Serie A, which has data from 2005-2022 in the `data` folder. This data came from: [https://www.football-data.co.uk](https://www.football-data.co.uk).  

## Code 

### Setup instructions

Requires python3 with pandas, numpy, and matplotlib installed.
The code will make a folder called plots where output plots will appear. 

### Usage

The top level script is `testPenalties.py` which depends on `penaltyUtils.py` (mostly helper functions that compute points of comparison) and `penaltyShootout.py` (which simulates the shootout). 

There are currently two tests implemented:
1. A simple test of the idea (usage: `python testPenalties.py --simpleTest --year [year]`). This looks at how the season would change if the home (or away) team always won the penalty shootout.
2. A Monte Carlo simulation of the penalty shootout (usage: `python testPenalties.py --mcPenalties --year [year]`). Here it assumes that each team has a 50% chance of scoring the penalty, and runs through 1000 instances of the season to study the most likely result of the introduction of the rule. 

