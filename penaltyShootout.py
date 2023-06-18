import numpy as np

class penaltyShootout:

  def __init__(self):
    self.nPenalties = 4
    self.result = 'D'

    self.play_shootout()

  def play_shootout(self):
    
    homeScore = 0
    awayScore = 0

    ## first shoot the standard number of penalities per team
    for i in range(0,self.nPenalties):
      homeScore += self.simple_penalty()
      awayScore += self.simple_penalty()
    
    if homeScore > awayScore: self.result =  'DH'
    elif homeScore < awayScore: self.result =  'DA'    
    else:
      # if no one won, we go to shootout
      while(homeScore == awayScore):
        print("drama!!")
        homeScore += self.simple_penalty()
        awayScore += self.simple_penalty()

      if homeScore > awayScore: self.result = 'DH'
      elif homeScore < awayScore: self.result = 'DA'

  def simple_penalty(self):
    return np.random.randint(0,2)
  
  def get_result_string(self):
    return self.result  

def penaltyMap(result):
  if result != 'D': return result

  p = penaltyShootout()
  return p.get_result_string()



  
