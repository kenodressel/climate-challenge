import random
from datetime import datetime

import numpy as np
import pandas as pd
from dimod import ConstrainedQuadraticModel, Binary, quicksum
from dimod.sym import Sense
from pandas import DataFrame
from typing import AnyStr, List, Literal
from typing import Dict

from src.main.quantum.model.AirplaneDetails import AirplaneDetails
from src.main.quantum.model.AirplaneSpeed import AirplaneSpeed
from src.main.quantum.model.FlightDetails import FlightDetails
from src.main.quantum.model.FuelConsumption import FuelConsumption
from src.main.quantum.model.TimeVoxel import TimeVoxel
from src.main.quantum.model.Voxel import Voxel


class ProblemDefinition:
    __PATH_TO_CLIMATE_COST_CSV = '../../resources/data/climate_cost'
    __PATH_TO_FUEL_CONSUMPTION_CSV = '../../resources/data/bada_data'
    __PATH_TO_FLIGHTS_CSV = '../../resources/data/flights'

    INDEX_KEY = "INDEX"
    LONGITUDE_DEGREE_KEY = 'LONGITUDE'
    LATITUDE_DEGREE_KEY = 'LATITUDE'
    FLIGHT_LEVEL_KEY = 'FL'
    TIME_KEY = 'TIME'
    MERGED_KEY = 'MERGED'

    TAS_KTS_KEY = 'TAS [kts]'
    ROD_FT_PER_MIN_KEY = 'ROD [ft/min]'
    ROC_FT_PER_MIN_KEY = 'ROC [ft/min]'
    FUEL_CONSUMPTION_CRUISE_KEY = "fuel (cruise) [kg/min]"
    FUEL_CONSUMPTION_DESCENT_KEY = "fuel (descent) [kg/min]"
    FUEL_CONSUMPTION_CLIMB_KEY = "fuel (climb) [kg/min]"

    MAX_VOXEL_HORIZONTAL_DISTANCE_IN_METER = 8e5
    MAX_VOXEL_VERTICAL_DISTANCE_IN_METER = 8e2

    def __init__(self, problem_size: Literal['small', 'medium', 'big'] = 'small', random_cost: bool = False):
        self.__problem_size: Literal['small', 'medium', 'big'] = problem_size  # Define problem size (small: 6 x 6 x 1 for one flight; medium: 6 x 6 x 3 for two flights; big: full problem set)
        print(f'Running {self.__problem_size} problem set!')

        self.__random_cost: bool = random_cost  # Use random climate costs instead of the climate cost defined in csv
        print(f'Running with {"random costs" if self.__random_cost else "costs from data"}!')

        self.airplane_details = self.find_airplane_details()  # Define flight speed and fuel consumption for airplane
        self.cost_by_voxels: Dict[TimeVoxel: float] = self.find_cost_by_voxels()  # Define climate cost for each voxel
        self.voxels: List[Voxel] = [time_voxel.voxel for time_voxel in self.cost_by_voxels.keys()]  # Define grid from climate cost voxels
        self.flight_details_by_flight_number: Dict[int, FlightDetails] = self.find_flight_details()  # Define flight start and destination

    def find_airplane_details(self) -> Dict[AnyStr, AirplaneDetails]:
        df: DataFrame = pd.read_csv(self.__PATH_TO_FUEL_CONSUMPTION_CSV + ".csv", delimiter=';')  # Read in fuel consumption and flight speed depending on flight level

        return {
            int(row[self.FLIGHT_LEVEL_KEY]): AirplaneDetails(
                AirplaneSpeed(
                    int(row[self.FLIGHT_LEVEL_KEY]),  # Define flight speed for flight level
                    float(row[self.TAS_KTS_KEY]),
                    float(row[self.ROD_FT_PER_MIN_KEY]),
                    float(row[self.ROC_FT_PER_MIN_KEY]),
                ),
                FuelConsumption(  # Define fuel consumption for flight level
                    int(row[self.FLIGHT_LEVEL_KEY]),
                    float(row[self.FUEL_CONSUMPTION_CRUISE_KEY]),
                    float(row[self.FUEL_CONSUMPTION_DESCENT_KEY]),
                    float(row[self.FUEL_CONSUMPTION_CLIMB_KEY]),
                )
            ) for [_, row] in df.iterrows()  # Map flight level to airplane details
        }

    def find_cost_by_voxels(self) -> Dict:
        df: DataFrame = pd.read_csv(self.__PATH_TO_CLIMATE_COST_CSV + "_" + self.__problem_size + ".csv", delimiter=',')  # Read in climate cost depending on voxel

        return {
            TimeVoxel(
                Voxel(
                    int(row[self.INDEX_KEY]),
                    int(row[self.LONGITUDE_DEGREE_KEY]),
                    int(row[self.LATITUDE_DEGREE_KEY]),
                    int(row[self.FLIGHT_LEVEL_KEY])
                ),
                datetime.fromisoformat(row[self.TIME_KEY])
            ): float(row[self.MERGED_KEY]) if not self.__random_cost else random.random()  # generate random climate cost for testing, if self.__random_cost is True
            for [_, row] in df.iterrows()  # Map voxel (depending on time) to climate cost. The voxels define the grid
        }

    def find_flight_details(self) -> Dict[int, FlightDetails]:
        df: DataFrame = pd.read_csv(self.__PATH_TO_FLIGHTS_CSV + "_" + self.__problem_size + ".csv", delimiter=',')  # Read in flights

        return {
            int(row.flight_number):
                FlightDetails(
                    TimeVoxel(
                        self.find_closest_voxel(  # Map start voxel to a voxel on the grid defined by the climate costs
                            Voxel(
                                None,  # No index has to be defined for the start voxel, as it will be mapped to an indexed voxel on the climate costs grid
                                int(row.start_longitudinal),
                                int(row.start_latitudinal),
                                int(row.start_flightlevel),
                            )
                        ),
                        datetime.fromisoformat(row.start_time)
                    ),
                    TimeVoxel(
                        self.find_closest_voxel(  # Map destination voxel to a voxel on the grid defined by the climate costs
                            Voxel(
                                None,  # No index has to be defined for the destination voxel, as it will be mapped to an indexed voxel on the climate costs grid
                                int(row.end_longitudinal),
                                int(row.end_latitudinal),
                                int(row.start_flightlevel)
                            )
                        ),
                        None  # No time defined for the flight to arrive at the destination
                    )
                )
            for [_, row] in df.iterrows()  # Map flight number to flight details (start, destination)
        }

    def find_closest_voxel(self, voxel: Voxel) -> Voxel:
        index_of_closest_voxel_in_list = np.argmin(
            [self.find_distance(voxel, voxel_on_grid) for voxel_on_grid in self.voxels]  # Calculate distance to other voxels
        )

        return self.voxels[index_of_closest_voxel_in_list]  # Return closest voxel on grid to input voxel

    def create_constraint_quadratic_model(self):
        cqm = ConstrainedQuadraticModel()  # Define CQM

        cost_for_neighbouring_voxels = self.find_cost_for_neighbouring_voxels()  # Calculate cost for travel to neighbours for each voxel

        for flight_number, flight_detail in self.flight_details_by_flight_number.items():  # Iterate over flights
            start_voxel_constraint = []
            destination_voxel_constraint = []
            selected_neighbours_constraint = {}
            cost_objectives = []

            for voxel, cost_by_neighbour_voxels in cost_for_neighbouring_voxels.items():
                selected_neighbours_constraint[voxel] = {}
                for neighbour_voxel, cost in cost_by_neighbour_voxels.items():
                    binary_variable = Binary(f'flight_between_voxels_{flight_number}_{voxel}_{neighbour_voxel}')  # Define a binary variable to represent travel between voxel and neighbour_voxel

                    if voxel == flight_detail.start_voxel.voxel.index:
                        start_voxel_constraint.append(binary_variable)  # Add binary variable to start_voxel_constraint, if voxel is also start_voxel of flight

                    if neighbour_voxel == flight_detail.destination_voxel.voxel.index:
                        destination_voxel_constraint.append(binary_variable)  # Add binary variable to destination_voxel_constraint, if neighbour_voxel is also destination_voxel of flight

                    selected_neighbours_constraint[voxel][neighbour_voxel] = binary_variable  # Add binary variable to selected neighbour constraint

                    cost_objectives.append(cost * binary_variable)  # Add cost for travel between voxel and neighbour voxel to cost objectives

            cqm.add_constraint_from_model(quicksum(start_voxel_constraint), Sense.Eq, 1, label=f'flight {flight_number} start voxel constraint')  # Add constraint for start voxel of flight
            cqm.add_constraint_from_model(quicksum(destination_voxel_constraint), Sense.Eq, 1, label=f'flight {flight_number} destination voxel constraint')  # Add constraint for destination voxel of flight

            for voxel, binary_variable_by_neighbour_voxel in selected_neighbours_constraint.items():
                for neighbour_voxel, neighbour_binary_variable in binary_variable_by_neighbour_voxel.items():
                    if neighbour_voxel == flight_detail.destination_voxel.voxel.index:
                        continue

                    next_neighbour_binary_variables = [next_neighbour_bqm for next_neighbour, next_neighbour_bqm in selected_neighbours_constraint[neighbour_voxel].items() if next_neighbour != voxel]  # Find binary variables for neighbours of a neighbour

                    cqm.add_constraint_from_model((1 - neighbour_binary_variable) + neighbour_binary_variable * quicksum(next_neighbour_binary_variables), Sense.Eq, 1, label=f'next_neighbour_{flight_number}_{voxel}_{neighbour_voxel}')  # Only one of the binary variables representing travelling from a neighbour to its corresponding neighbours is allowed to be active (if one travelling to the initial neighbour is active)

            cqm.set_objective(quicksum(cost_objectives))  # Add cost objectives

        return cqm

    def find_cost_for_neighbouring_voxels(self) -> Dict:
        cost_between_neighbouring_voxels = {}
        for time_voxel_start, cost_start in self.cost_by_voxels.items():
            cost_between_neighbouring_voxels[time_voxel_start.voxel.index] = {}
            for time_voxel_end, cost_end in self.cost_by_voxels.items():
                if time_voxel_start.voxel == time_voxel_end.voxel:
                    continue  # Same voxel -> no connection

                if time_voxel_start.time != time_voxel_end.time:
                    continue  # Ignore connections between voxel for different times

                # if time_voxel_end.voxel.index in cost_between_neighbouring_voxels.keys():
                #     if time_voxel_start.voxel.index in cost_between_neighbouring_voxels[time_voxel_end.voxel.index].keys():
                #         continue

                if self.find_horizontal_distance(time_voxel_start.voxel, time_voxel_end.voxel) > self.MAX_VOXEL_HORIZONTAL_DISTANCE_IN_METER:  # If the other voxel is too far away (horizontally), there will be no direct connection
                    continue

                if self.find_vertical_distance(time_voxel_start.voxel, time_voxel_end.voxel) > self.MAX_VOXEL_VERTICAL_DISTANCE_IN_METER:  # If the other voxel is too far away (vertically), there will be no direct connection
                    continue

                cost_between_neighbouring_voxels[time_voxel_start.voxel.index][time_voxel_end.voxel.index] = self.calculate_cost(  # Calculate climate cost between start_voxel and end_voxel
                    time_voxel_start.voxel,
                    time_voxel_end.voxel,
                    cost_start,
                    cost_end
                )

        return cost_between_neighbouring_voxels

    def calculate_cost(self, voxel_start: Voxel, voxel_end: Voxel, cost_start_voxel: float, cost_end_voxel: float) -> float:
        distance: float = self.find_distance(voxel_start, voxel_end)  # Find distance between voxels

        flight_direction: str = self.find_flight_direction(voxel_start.flight_level_meter, voxel_end.flight_level_meter)  # Find flight direction (DESCENT, CLIMB, CRUISE) between voxels

        cost_K_start = self.cost_per_voxel((distance / 2), flight_direction, voxel_start, cost_start_voxel)  # Calculate climate cost in start_voxel
        cost_K_end = self.cost_per_voxel((distance / 2), flight_direction, voxel_end, cost_end_voxel)  # Calculate climate cost in destination voxel

        return cost_K_start + cost_K_end  # Add climate cost in start_voxel and end_voxel

    def find_distance(self, voxel_a: Voxel, voxel_b: Voxel) -> float:
        return np.sqrt(
            np.power(voxel_a.longitude_meter - voxel_b.longitude_meter, 2)
            + np.power(voxel_a.latitude_meter - voxel_b.latitude_meter, 2)
            + np.power(voxel_a.flight_level_meter - voxel_b.flight_level_meter, 2)
        )

    def find_vertical_distance(self, voxel_a: Voxel, voxel_b: Voxel) -> float:
        return np.absolute(voxel_a.flight_level_meter - voxel_b.flight_level_meter)

    def find_horizontal_distance(self, voxel_a: Voxel, voxel_b: Voxel) -> float:
        return np.sqrt(
            np.power(voxel_a.longitude_meter - voxel_b.longitude_meter, 2)
            + np.power(voxel_a.latitude_meter - voxel_b.latitude_meter, 2)
        )

    def cost_per_voxel(self, distance: float, direction: str, voxel: Voxel, cost_in_voxel: float):
        fuel_consumption_kg: float = self.calculate_fuel_consumption_in_voxel(distance, direction, voxel)  # Calculate fuel consumption in voxel (depends on flight direction: DESCENT, CLIMB, CRUISE)

        return cost_in_voxel * fuel_consumption_kg

    def calculate_fuel_consumption_in_voxel(self, distance: float, direction: str, voxel: Voxel) -> float:
        fuel_consumption: float = self.find_fuel_consumption_for_flight_direction(direction, voxel)  # Define fuel consumption per second by flight direction (DESCENT, CLIMB, CRUISE)
        time_s = self.calculate_time_in_voxel(distance, voxel)  # Find time in voxel, depending on airplane speed

        return fuel_consumption * time_s

    def find_fuel_consumption_for_flight_direction(self, direction: str, voxel: Voxel) -> float:
        if direction == "DESCENT":
            return self.airplane_details[voxel.flight_level].fuel_consumption.descent_fuel_consumption_kg_s  # Define fuel consumption for flight direction DESCENT

        if direction == "CLIMB":
            return self.airplane_details[voxel.flight_level].fuel_consumption.climb_fuel_consumption_kg_s  # Define fuel consumption for flight direction CLIMB

        return self.airplane_details[voxel.flight_level].fuel_consumption.cruise_fuel_consumption_kg_s  # Define fuel consumption for flight direction CRUISE

    def calculate_time_in_voxel(self, distance: float, voxel: Voxel) -> float:
        airplane_speed: AirplaneSpeed = self.airplane_details[voxel.flight_level].airplane_speed  # Find airplane speed for flight level

        return distance / airplane_speed.airplane_speed_m_s  # Calculate time to travel distance with airplane speed

    def find_flight_direction(self, flight_level_start: float, flight_level_end: float) -> str:
        if flight_level_start > flight_level_end:
            return "DESCENT"

        if flight_level_start < flight_level_end:
            return "CLIMB"

        return "CRUISE"

    def print_flight_details(self):
        for flight_number, flight_details in self.flight_details_by_flight_number.items():
            print(f'Flight details for flight number {flight_number}: {flight_details}')


if __name__ == "__main__":
    problem_definition = ProblemDefinition(problem_size="small", random_cost=False)

    problem_definition.print_flight_details()

    problem_definition.create_constraint_quadratic_model()
