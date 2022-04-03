import pandas as pd
climate = pd.read_csv('material/climate.csv')
fuel = pd.read_csv('material/fuel.csv')

climate = climate[['LATITUDE','LONGITUDE','FL','TIME','MERGED']]

fuel = fuel[['FL','fuel1','fuel2','fuel3']]

def costFunction(qbits):
    res = 0
    for t in range(times):
        for a in range(nrAirplanes):
            for x in range(size[0]):
                for y in range(size[1]):
                    for z in range(size[2]):
                        if [x,y,z] != destination[a]:
                            climate_cost = int(1e6*climate[(climate.LONGITUDE==climate.LONGITUDE.unique()[x])&(climate.LATITUDE==climate.LATITUDE.unique()[y])&(climate.FL==climate.FL.unique()[z])].MERGED.values[0])
                            fuel_cost = int(10*fuel[fuel.FL==fuel.FL.unique()[z]].fuel1.values[0])
                            res += qbits[t][a][x][y][z]*fuel_cost*climate_cost
    return res