from ortools.sat.python import cp_model
import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import time as t

climate = pd.read_csv('material/climate.csv')
fuel = pd.read_csv('material/fuel.csv')

climate = climate[['LATITUDE','LONGITUDE','FL','TIME','MERGED']]

fuel = fuel[['FL','fuel1','fuel2','fuel3']]



# #### Setting parameters, some examples given
# nrAirplanes = 1
# size = [5,5,1]
# time = 20
# start = [[0,0,0]]
# destination = [[3,4,0]]

# nrAirplanes = 1
# size = [5,5,3]
# time = 20
# start = [[0,0,0]]
# destination = [[3,4,2]]

# nrAirplanes = 1
# size = [5,5,5]
# time = 20
# start = [[0,0,0]]
# destination = [[3,4,4]]
               
# nrAirplanes = 1
# size = [10,10,5]
# time = 20
# start = [[0,0,0]]
# destination = [[7,9,4]]
                      
# nrAirplanes = 2
# size = [5,5,3]
# time = 20
# start = [[0,0,0],[2,2,0]]
# destination = [[3,4,1],[1,3,2]]
               
# nrAirplanes = 3
# size = [5,5,3]
# time = 20
# start = [[0,0,0],[2,2,0],[4,4,1]]
# destination = [[3,4,1],[1,3,2],[0,2,1]]
               
# nrAirplanes = 4
# size = [5,5,3]
# time = 20
# start = [[0,0,0],[2,2,0],[4,4,1],[1,2,0]]
# destination = [[3,4,1],[1,3,2],[0,2,1],[4,2,1]] 



# nrAirplanes = 2
# size = [6,6,3]
# time = 20
# start = [[0,0,0],[5,3,2]]
# destination = [[4,2,1],[2,1,0]]

# nrAirplanes = 4
# size = [10,10,5]
# time = 30
# start = [[0,0,1],[5,0,1],[3,0,1],[6,0,1]]
# destination = [[8,3,2],[2,4,4],[1,7,3],[1,3,3]]


class CPSolver(object):
    def __init__(self,nrAirplanes,size,time,start,destination):
        self.nrAirplanes = nrAirplanes
        self.size_x,self.size_y,self.size_z = size
        self.time = time
        self.destination = destination
        self.model = cp_model.CpModel()
        self.createMap()
        self.start = start
    
    def createMap(self):
        "Defines the size of the airspace, maximum number of timesteps, and the number of airplanes. "
        T = []
        for t in range(self.time):
            A = [] 
            for a in range(self.nrAirplanes):
                X = []
                for x in range(self.size_x):
                    Y = []
                    for y in range(self.size_y):
                        Z = []
                        for z in range(self.size_z):
                            C = []
                            for c in [0,1,2]:
                                C.append(self.model.NewIntVar(0, 1, 't%ia%ix%iy%iz%i%s' %(t,a,x,y,z,c)))
                            Z.append(C)
                        Y.append(Z)
                    X.append(Y)
                A.append(X)
            T.append(A)
        self.qbits = T
    
    def possibleTrajectory(self):
        """List of all possible trajectories any airplane can take. 
        Planes will:
            - only move to neighbouring voxels
            - not leave the defined grid
            - change their altitude by at most one flight level 
            - stay at the destination once it has arrived there
        """
        for t in range(self.time-1):
            for a in range(self.nrAirplanes):
                for x in range(self.size_x):
                    for y in range(self.size_y):
                        for z in range(self.size_z):
                            if [x,y,z] != self.destination[a]:
                                self.model.Add(self.qbits[t+1][a][min(self.size_x-1,x+1)][y][max(0,z-1)][0]
                                    + self.qbits[t+1][a][max(0,x-1)][y][max(0,z-1)][0] 
                                    + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][max(0,z-1)][0]
                                    + self.qbits[t+1][a][x][max(0,y-1)][max(0,z-1)][0]
                                               
                                    + self.qbits[t+1][a][min(self.size_x-1,x+1)][y][z][1]
                                    + self.qbits[t+1][a][max(0,x-1)][y][z][1] 
                                    + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][z][1]
                                    + self.qbits[t+1][a][x][max(0,y-1)][z][1]
                                               
                                               
                                    + self.qbits[t+1][a][min(self.size_x-1,x+1)][y][min(self.size_z-1,z+1)][2]
                                    + self.qbits[t+1][a][max(0,x-1)][y][min(self.size_z-1,z+1)][2] 
                                    + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][min(self.size_z-1,z+1)][2]
                                    + self.qbits[t+1][a][x][max(0,y-1)][min(self.size_z-1,z+1)][2]
                                    -self.qbits[t][a][x][y][z][0] -self.qbits[t][a][x][y][z][1] -self.qbits[t][a][x][y][z][2] >= 0)
                            else:
                                self.model.Add(self.qbits[t][a][x][y][z][0] + self.qbits[t][a][x][y][z][1] + self.qbits[t][a][x][y][z][2] <= self.qbits[t+1][a][x][y][z][1])
                        
    def avoidCrash(self):
        "Prohibits two airplanes to be in the same voxel at the same time, no matter the maneuver."
        for t in range(self.time):
            for a1 in range(self.nrAirplanes):
                for a2 in range(a1+1,self.nrAirplanes):
                    for x in range(self.size_x):
                        for y in range(self.size_y):
                            for z in range(self.size_z):
                                self.model.Add(self.qbits[t][a1][x][y][z][0] + self.qbits[t][a2][x][y][z][0] 
                                               + self.qbits[t][a1][x][y][z][1] + self.qbits[t][a2][x][y][z][1]
                                               + self.qbits[t][a1][x][y][z][2] + self.qbits[t][a2][x][y][z][2] <= 1)
   
    def flightlevel(self):
        "Defines process of changing flight level by one."
        for t in range(self.time-1):
            for a in range(self.nrAirplanes):
                for x in range(self.size_x):
                    for y in range(self.size_y):
                        for z in range(self.size_z):
                            for c in [0,1,2]:
                                self.model.Add(self.qbits[t][a][x][y][z][0]               
                                + self.qbits[t+1][a][min(self.size_x-1,x+1)][y][z][c]           
                                + self.qbits[t+1][a][max(0,x-1)][y][z][c] 
                                + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][z][c]
                                + self.qbits[t+1][a][x][max(0,y-1)][z][c] <= 1)
                                if z!=self.size_z-1:
                                    self.model.Add(self.qbits[t][a][x][y][z][0]               
                                    + self.qbits[t+1][a][min(self.size_x-1,x+1)][y][z+1][c]           
                                    + self.qbits[t+1][a][max(0,x-1)][y][z+1][c] 
                                    + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][z+1][c]
                                    + self.qbits[t+1][a][x][max(0,y-1)][z+1][c] <= 1)
                                self.model.Add(self.qbits[t][a][x][y][z][2]               
                                + self.qbits[t+1][a][min(self.size_x-1,x+1)][y][z][c]           
                                + self.qbits[t+1][a][max(0,x-1)][y][z][c] 
                                + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][z][c]
                                + self.qbits[t+1][a][x][max(0,y-1)][z][c] <= 1)
                                if z!=0:
                                    self.model.Add(self.qbits[t][a][x][y][z][2]               
                                    + self.qbits[t+1][a][min(self.size_x-1,x+1)][y][z-1][c]           
                                    + self.qbits[t+1][a][max(0,x-1)][y][z-1][c] 
                                    + self.qbits[t+1][a][x][min(self.size_y-1,y+1)][z-1][c]
                                    + self.qbits[t+1][a][x][max(0,y-1)][z-1][c] <= 1)
                                           
        

    def addConstraints(self):
        "Adds all the individual constraints to the model."
        for a in range(self.nrAirplanes):
            # Create Start
            self.model.Add(self.qbits[0][a][self.start[a][0]][self.start[a][1]][self.start[a][2]][1] == 1)
            # # Create destination
            self.model.Add(self.qbits[self.time-1][a][self.destination[a][0]][self.destination[a][1]][self.destination[a][2]][0]
                           +self.qbits[self.time-1][a][self.destination[a][0]][self.destination[a][1]][self.destination[a][2]][1]
                           +self.qbits[self.time-1][a][self.destination[a][0]][self.destination[a][1]][self.destination[a][2]][2] == 1) 
            # Conserve number of planes
            for t in range(self.time):
                self.model.Add(self.planeConservation(self.qbits[t][a])==1)
            # Define all trajectories
            self.possibleTrajectory()
            # Avoid crash between any two planes
            self.avoidCrash()
            # Defines change of flight level and associated cost.
            self.flightlevel()            
            
    def planeConservation(self,mapbits):
        "Conserves total number of planes in the system."
        res = 0
        for x in mapbits:
            for y in x:
                for z in y:
                    for c in z:
                        res+=c
        return res
    
    
    
    def plotTrajectory(self,solver):
        "Plots the resulting trajectory."
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for a in range(self.nrAirplanes):
            trajectory_x = []
            trajectory_y = []
            trajectory_z = []
            for t in range(self.time):
                for z in range(self.size_z):
                    for y in range(self.size_y):
                        for x in range(self.size_x):
                            for c in [0,1,2]:
                                if (solver.Value(self.qbits[t][a][x][y][z][c]) == 1):
                                    trajectory_x.append(x)
                                    trajectory_y.append(y)
                                    trajectory_z.append(z)
        
                                
            ax.plot(trajectory_x, trajectory_y,trajectory_z, linestyle='-')
            ax.scatter(*self.start[a])
        plt.show()






def costFunction(qbits):
    "Overall cost function: cliamte cost depending on fuel consumption and voxels traversed."
    res = 0
    for t in range(time):
        for a in range(nrAirplanes):
            for x in range(size[0]):
                for y in range(size[1]):
                    for z in range(size[2]):
                        for c in [0,1,2]:
                            if [x,y,z] != destination[a]:
                                climate_cost = int(1e6*climate[(climate.LONGITUDE==climate.LONGITUDE.unique()[x])&(climate.LATITUDE==climate.LATITUDE.unique()[y])&(climate.FL==climate.FL.unique()[z])].MERGED.values[0])
                                if c ==0:
                                    fuel_cost = int(10*fuel[fuel.FL==fuel.FL.unique()[z+1]].fuel3.values[0])
                                if c ==1:
                                    fuel_cost = int(10*fuel[fuel.FL==fuel.FL.unique()[z+1]].fuel1.values[0])
                                if c ==2:
                                    fuel_cost = int(10*fuel[fuel.FL==fuel.FL.unique()[z+1]].fuel2.values[0])
                                res += qbits[t][a][x][y][z][c]*fuel_cost*climate_cost
    return res


def reward(qbits):
    "Hands out reward for having reaching the destination at the final time step."
    res = 0
    for a in range(nrAirplanes):
        res+=qbits[time-1][a][destination[a][0]][destination[a][1]][destination[a][2]][1]
    return res




CP = CPSolver(nrAirplanes,size,time,start,destination)
t0 = t.time()
print('Adding constraints...')
CP.addConstraints()
t1 = t.time()
print('Creating cost function...')

CP.model.Minimize(costFunction(CP.qbits) - 1000 * reward(CP.qbits))
t2 = t.time()
print('Solving...')
# Creates a solver and solves the model.
solver = cp_model.CpSolver()
# solver.parameters.enumerate_all_solutions = True
solver.parameters.num_search_workers = 5
status = solver.Solve(CP.model)
t3 = t.time()
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    CP.plotTrajectory(solver)
else:
    print('No solution found.')

# # Statistics.
print('Constraints: %.2f' %(t1-t0))
print('Cost function: %.2f' %(t2-t1))
print('Solving:%.2f' %(t3-t2))


