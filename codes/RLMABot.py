# This program is configured to perform multiple actions.

#!/usr/bin/env python
#

# This is a reinforcement learning bot for the ML Project.
# Author: Ashwinkumar Ganesan.
# Date: 5/5/2011

from PlanetWars import PlanetWars
from PlanetWars import Fleet
from os import access, F_OK, stat
from random import random, randint
import sys

# The program implements Q-Learning.
# This is the function that calculates the reward at the current position.
def GetReward(pw, RewardConstant):
  Reward = 0
  for Fleet in pw._fleets:
    if(Fleet._owner == 1 and Fleet._turns_remaining == 1):
      # Calculate the difference between the number of ships in the source and destination planet.
      Num_Of_Ships_In_Planet = 0
      for Planet in pw._planets:
        if(Fleet._destination_planet == Planet._planet_id):
          Num_Of_Ships_In_Planet = Planet._num_ships + Planet._growth_rate
          break
        
      Diff_In_Num_Of_Ships = Fleet._num_ships - Num_Of_Ships_In_Planet 
      Reward += RewardConstant * Diff_In_Num_Of_Ships
     
    # This is for the opponent.
    elif(Fleet._owner == 2 and Fleet._turns_remaining == 1):
      # Calculate the difference between the number of ships in the source and destination planet.
      Num_Of_Ships_In_Planet = 0
      for Planet in pw._planets:
        if(Fleet._destination_planet == Planet._planet_id):
          Num_Of_Ships_In_Planet = Planet._num_ships + Planet._growth_rate
          break
        
      Diff_In_Num_Of_Ships = Fleet._num_ships - Num_Of_Ships_In_Planet 
      Reward -= RewardConstant * Diff_In_Num_Of_Ships
  
  return Reward

# This is the function to update the current state.
def UpdateState(pw):
  # Update all the planets with their new number of ships.
  # This has to be done for only those planets which are captured by the bot or the enemy.
  for Planet in pw._planets:
    if(Planet._owner == 1 or Planet._owner == 2):
      Planet._num_ships += Planet._growth_rate
  
  # Update all the fleets. Reduce the turns remaining by one.
  # Also if the fleet is attacking a planet, we have to take care of the 
  # ownership of the planet.
  DeleteFleetList = []
  for Fleet in pw._fleets:
    Fleet._turns_remaining -= 1
    if(Fleet._turns_remaining == 0):
      # Update the destination planet.
      for Planet in pw._planets:
        if(Fleet._destination_planet == Planet._planet_id):
          Planet._num_ships -= Fleet._num_ships
          DestPlanet = Planet
          break

      if(DestPlanet._num_ships < 0):
        DestPlanet._owner = Fleet._owner
      
      DeleteFleetList.append(Fleet)
   
  # Once the fleet is used. It needs to be removed from the list.
  for Fleet in DeleteFleetList:
    pw._fleets.remove(Fleet)

# This is the function that does Q-Learning.
# The Threshold is the define the minimum number of ships the source planet must have.

def QLearn(pw, RewardConstant, TurnNumber, LearningRate, Threshold, Gamma, DatabaseLocation,MinAttackUnit):
  # First step is to build the index.
  # Check if the learning file for the turn exists.
  FilePath = DatabaseLocation + "/" + str(TurnNumber) + ".csv"
  MAFilePath = DatabaseLocation + "/MA" + str(TurnNumber) + ".csv"
   
  fsock = open('error.log', 'a')
  sys.stderr = fsock

  AccessFlag = 1

  # Create two Q-Index.
  # 1. For maintaining Q-Values of individual actions.
  # 2. For maintaining the Q-Values for mutiple action related states.
  QIndex = {}
  QMAIndex = {} # This is the multi-action index.

  if(access(FilePath, F_OK) == False):
    AccessFlag = 0

  if(AccessFlag == 1):
    FileInfo = stat(FilePath)

  if((AccessFlag == 0) or (FileInfo[6] == 0L)):
    # Create the CSV File and add the initial values.
    FilePtr = open(FilePath,"w");
    MAFilePtr = open(MAFilePath, "w")

    # The initial learning values are taken to be zero.
    for SPlanet in pw._planets:
      QIndex[SPlanet._planet_id] = {}
      for DPlanet in pw._planets:
        if(SPlanet._planet_id != DPlanet._planet_id):
          WriteString = str(SPlanet._planet_id) + "," + str(DPlanet._planet_id) + ",0\n"
          FilePtr.write(WriteString)
          QIndex[SPlanet._planet_id][DPlanet._planet_id] = 0

    # Build the multiple attack Q-Index (QMAIndex). 
    TotalNumPlanets = len(pw._planets)
    for inc in range(1, TotalNumPlanets):
        WriteString = str(inc) + ",0\n"
        MAFilePtr.write(WriteString)
        QMAIndex[inc] = 0
    
    # Close the file.
    FilePtr.close()
  elif(AccessFlag == 1):
    # Construct the index.
    for Planet in pw._planets:
      QIndex[Planet._planet_id] = {}
      
    FilePtr = open(FilePath, "r")
    lines = [line for line in FilePtr][:1000]
    
    for FileLine in lines:
      LineSplit = FileLine.split(",")
      QIndex[int(LineSplit[0])][int(LineSplit[1])]= float(LineSplit[2].rstrip())
      
    FilePtr.close()
    # Construct the Multiple Attack QMAIndex.
    MAFilePtr = open(MAFilePath, "r")
    lines = [line for line in MAFilePtr][:1000]
    
    for FileLine in lines:
      LineSplit = FileLine.split(",")
      QMAIndex[int(LineSplit[0])] = float(LineSplit[1].rstrip())

    MAFilePtr.close()
  # Select the action which has the best  
  # Next Step is to select the best action.
  MaxQValue = -99999999 # Minimum value possible.
  MaxMAQValue = -99999999

  SourcePlanetID = 0
  DestinationPlanetID = -1
  AttackVector = []

  # Define Multiple Attack Size.
  AttackSize = 0 
    
  # Consider enemy planets.
  # Fleet Size calculation is constant for now.
  MyPlanets = pw.MyPlanets()
  EnemyPlanets = pw.EnemyPlanets()
  NeutralPlanets = pw.NeutralPlanets()
 
  # Making the fleet choice random.
  if(random() < Gamma):
   try:
      MyPlanetCount = len(MyPlanets)
      EnemyPlanetCount = len(EnemyPlanets)
      NeutralPlanetCount = len(NeutralPlanets)

      # This makes the attacksize random.
      if(len(pw.NotMyPlanets()) > 0 or len(pw.MyPlanets()) > 0):
         AttackSize = randint(1, len(pw.NotMyPlanets()))
         Count = 0

         for inc in range(0, AttackSize):
            SourcePlanetIndex = randint(0,MyPlanetCount-1)
            SourcePlanetID = MyPlanets[SourcePlanetIndex]._planet_id 
   
         if((NeutralPlanetCount > 0) and (random() <= 0.4)):
            DestinationPlanetID = NeutralPlanets[randint(0,NeutralPlanetCount-1)]._planet_id
         elif(EnemyPlanetCount > 0):
            DestinationPlanetID = EnemyPlanets[randint(0,EnemyPlanetCount-1)]._planet_id
      
         if(DestinationPlanetID != -1):
            AttackVector.append([SourcePlanetID, DestinationPlanetID, QIndex[SourcePlanetID][DestinationPlanetID], 0, MyPlanets[SourcePlanetIndex]])
         elif(DestinationPlanetID == -1):
            Count += 1
      
         AttackSize = AttackSize - Count
         if(AttackSize < 0):
            AttackSize = 0
   except:
      pass
          
  else:
    #  First Choose the attack vector size with the highest value.
    for Size in QMAIndex:
      if(MaxMAQValue <= QMAIndex[Size]):
        MaxMAQValue = QMAIndex[Size]
        AttackSize = Size
         
    # Once the attack vector size is defined, select source and destination planets for the attack.
    # Put the QIndex Value in a new list.
    NotMyPlanets = pw.NotMyPlanets()
    
    for SPlanet in pw.MyPlanets():
      if(SPlanet._num_ships > (SPlanet._growth_rate*Threshold)):
        for DPlanet in NotMyPlanets:
          AttackVector.append([SPlanet._planet_id, DPlanet._planet_id, QIndex[SPlanet._planet_id][DPlanet._planet_id], 0, SPlanet])
     
    if(AttackSize > len(AttackVector)):
      AttackSize = len(AttackVector)

    # Sort the Attack Vector by in descending order of value.
    # The Attack Vector and the Attack Size are to be returned back.
    AttackVector = sorted(AttackVector, key=lambda AttackTuple: AttackTuple[2], reverse=True)
  
  # Calculate the fleet size.
  Vector = CalculateFleetSize(AttackVector, AttackSize, MinAttackUnit, Threshold)
  AttackVector = Vector[0]
  AttackSize = Vector[1]

  # Action Selected.
  # Create a Fleet for that action.
  for SingleAttack in AttackVector:
    if(pw.Distance(SingleAttack[0], SingleAttack[1]) == 1):
      NewFleet = Fleet(1, # Owner
                    SingleAttack[3], # Num ships
                    SingleAttack[0], # Source
                    SingleAttack[1], # Destination
                    1, # Total trip length
                    1) # Turns remaining
      pw._fleets.append(NewFleet)
  
  # Next step is to calculate the reward for next state.
  Reward = GetReward(pw, RewardConstant)
  
  # Now calculate the Max QValue for the next state.
  # First we update the state.
  # UpdateState(pw)
  
  # Then find the highest QValue.
  FilePathNextState = DatabaseLocation + "/" + str(TurnNumber+1) + ".csv"
  MAFilePathNextState = DatabaseLocation + "/MA" + str(TurnNumber+1) + ".csv"
  
  MaxQValueNextState = -99999999 # Minimum value possible.
  MaxMAQValueNextState = 0 # Minimum value possible.
  AccessFlag = 1
  
  if(access(FilePathNextState, F_OK) == False):
    AccessFlag = 0
  
  if(AccessFlag == 1):
    FileInfo = stat(FilePathNextState)
  
  if((AccessFlag == 0) or (FileInfo[6] == 0L)):
    # Create the CSV File and add the initial values.
    FilePtr = open(FilePathNextState,"w");
    MAFilePtr = open(MAFilePathNextState,"w");
    # The initial learning values are taken to be zero.
    for SPlanet in pw._planets:
      for DPlanet in pw._planets:
        if(SPlanet._planet_id != DPlanet._planet_id):
          WriteString = str(SPlanet._planet_id) + "," + str(DPlanet._planet_id) + ",0\n"
          FilePtr.write(WriteString)
    
    # Build the multiple attack Q-Index (OMAIndex). 
    TotalNumPlanets = len(pw._planets)
    for inc in range(1, TotalNumPlanets+1):
        WriteString = str(inc) + ",0\n"
        MAFilePtr.write(WriteString)
        inc += 1

    MaxQValueNextState = 0 # Minimum value possible.
    
    # Close the file.
    FilePtr.close()
  elif(AccessFlag == 1):
    
    if(AttackSize != 0):
      # Create the Destination Vector.
      DesVector = {}
      for inc in range(0, AttackSize):
        DesVector[AttackVector[inc][1]] = 0
    
      for inc in range(0, AttackSize):
        DesVector[AttackVector[inc][1]] += 1 
        
      FilePtr = open(FilePathNextState, "r")
      lines = [line for line in FilePtr][:1000]
    
      DesQValue = {}
    
      for FileLine in lines:
        LineSplit = FileLine.split(",")
        if((int(LineSplit[1]) in DesQValue) == False):
          DesQValue[int(LineSplit[1])] = []
        DesQValue[int(LineSplit[1])].append(float(LineSplit[2].rstrip()))
      
        # Find the Max Q Value in the next state.
        if(MaxQValueNextState <= float(LineSplit[2].rstrip())):
          MaxQValueNextState = float(LineSplit[2].rstrip())
    
      # Sort each list in the dictionary.
      for Key in DesQValue:
        DesQValue[Key] = sorted(DesQValue[Key], reverse=True)
    
      FilePtr.close()
 
      for inc in range(0, AttackSize):
        MaxMAQValueNextState += DesQValue[AttackVector[inc][1]][DesVector[AttackVector[inc][1]]-1]
        DesVector[AttackVector[inc][1]] -= 1
 
      MaxMAQValueNextState = MaxMAQValueNextState / AttackSize

  # Perform the QValue Update.
  
  for SingleAttack in AttackVector:
    TempQIndexValue = float(QIndex[SingleAttack[0]][SingleAttack[1]])
    QIndex[SingleAttack[0]][SingleAttack[1]] += LearningRate*(Reward + MaxQValueNextState - TempQIndexValue)

  if(AttackSize != 0):
    TempQMAIndexValue = float(QMAIndex[AttackSize])
    QMAIndex[AttackSize] += LearningRate*(MaxMAQValueNextState - TempQMAIndexValue)
  
  # Re-write the updated values to the database.
  FilePtr = open(FilePath, "w")
  for SPlanet in QIndex:
    for DPlanet in QIndex[SPlanet]:
      WriteString = str(SPlanet) + "," + str(DPlanet) + "," + str(QIndex[SPlanet][DPlanet]) +"\n"
      FilePtr.write(WriteString)

  MAFilePtr = open(MAFilePath, "w")
  for inc in QMAIndex:
    WriteString = str(inc) + "," + str(QMAIndex[inc]) +"\n"
    MAFilePtr.write(WriteString)

  FilePtr.close()
  MAFilePtr.close()

  return [AttackVector, AttackSize]
  

# This function calculates the Attack Vector Fleet Size using round robin technique.
def CalculateFleetSize(AttackVector, AttackSize, MinAttackUnit, Threshold):
  NewAttackVector = {}
  FinalAttackVector = []
  
  if(AttackSize == 0):
    return [[], 0]
  
  # Create a new Attack Vector.
  if(AttackSize > len(AttackVector)):
    AttackSize = len(AttackVector)

  try:
   for inc in range(0, AttackSize):
      NewAttackVector[AttackVector[inc][0]] = []
  except:
   sys.stderr.write(str(NewAttackVector))
   sys.stderr.write(str(AttackVector))
   sys.stderr.write(str(AttackSize))


  # Allocate the Fleet.
  for inc in range(0, AttackSize):
    NewAttackVector[AttackVector[inc][0]].append([AttackVector[inc][1], AttackVector[inc][2], AttackVector[inc][3], AttackVector[inc][4], inc])
    

  # Apply Round Robin to allocates ships.
  for SPlanet in NewAttackVector:
    NumOfShips = NewAttackVector[SPlanet][0][3]._num_ships - (NewAttackVector[SPlanet][0][3]._growth_rate*Threshold) 
    Flag = 0
    while(NumOfShips > 0):
      for DPlanet in NewAttackVector[SPlanet]:
         if(NumOfShips > 0):
            DPlanet[2] += MinAttackUnit
            NumOfShips -= MinAttackUnit
         elif(NumOfShips <= 0):
            Flag = 1
            break
      
      if(Flag == 1):
         break

  # Change the Allocations in the AttackVector.
  for SPlanet in NewAttackVector:
    for DPlanet in NewAttackVector[SPlanet]:
      AttackVector[DPlanet[4]][3] = DPlanet[2]

  for SingleAttack in AttackVector:
    if(SingleAttack[3] != 0):
      FinalAttackVector.append(SingleAttack)
      
  return [FinalAttackVector, len(FinalAttackVector)]
  
# This function that executes at every turn and issues the order.
# Source is the source planet of the ships.
# dest is the destination planet of the ships.
# num_ships is the number of ships to be sent to the planet.

def DoTurn(pw, TurnNumber, Alpha, Gamma, DatabaseLocation):
  TurnNumber += 1
  Order = QLearn(pw, 10, TurnNumber, Alpha, 10, Gamma, DatabaseLocation, 10)
  for inc in range(0, Order[1]):
    pw.IssueOrder(Order[0][inc][0],Order[0][inc][1], Order[0][inc][3])
  
  return TurnNumber

def main():
  Alpha = float(sys.argv[1])
  Gamma = float(sys.argv[2])
  DatabaseLocation = sys.argv[3]

  map_data = ''
  TurnNumber = 0
  while(True):
    current_line = raw_input()
    if len(current_line) >= 2 and current_line.startswith("go"):
      pw = PlanetWars(map_data)
      TurnNumber = DoTurn(pw, TurnNumber, Alpha, Gamma, DatabaseLocation)
      pw.FinishTurn()
      map_data = ''
    else:
      map_data += current_line + '\n'


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
