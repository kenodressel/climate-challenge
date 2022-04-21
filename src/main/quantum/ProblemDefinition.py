import random
from datetime import datetime
from typing import AnyStr, List, Literal
from typing import Dict

import numpy as np
import pandas as pd
from dimod import ConstrainedQuadraticModel, Binary, quicksum
from dimod.sym import Sense
from pandas import DataFrame

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
        self.__problem_size: Literal['small', 'medium', 'big'] = problem_size
        print(f'Running {self.__problem_size} problem set!')

        self.__random_cost: bool = random_cost
        print(f'Running with {"random costs" if self.__random_cost else "costs from data"}!')

        self.airplane_details = self.find_airplane_details()
        self.cost_by_voxels: Dict[TimeVoxel: float] = self.find_cost_by_voxels()
        self.voxels: List[Voxel] = [time_voxel.voxel for time_voxel in self.cost_by_voxels.keys()]
        self.flight_details_by_flight_number: Dict[int, FlightDetails] = self.find_flight_details()

    def find_airplane_details(self) -> Dict[AnyStr, AirplaneDetails]:
        df: DataFrame = pd.read_csv(self.__PATH_TO_FUEL_CONSUMPTION_CSV + ".csv", delimiter=';')

        return {
            int(row[self.FLIGHT_LEVEL_KEY]): AirplaneDetails(
                AirplaneSpeed(
                    int(row[self.FLIGHT_LEVEL_KEY]),
                    float(row[self.TAS_KTS_KEY]),
                    float(row[self.ROD_FT_PER_MIN_KEY]),
                    float(row[self.ROC_FT_PER_MIN_KEY]),
                ),
                FuelConsumption(
                    int(row[self.FLIGHT_LEVEL_KEY]),
                    float(row[self.FUEL_CONSUMPTION_CRUISE_KEY]),
                    float(row[self.FUEL_CONSUMPTION_DESCENT_KEY]),
                    float(row[self.FUEL_CONSUMPTION_CLIMB_KEY]),
                )
            ) for [_, row] in df.iterrows()
        }

    def find_cost_by_voxels(self) -> Dict:
        df: DataFrame = pd.read_csv(self.__PATH_TO_CLIMATE_COST_CSV + "_" + self.__problem_size + ".csv", delimiter=',')

        return {
            TimeVoxel(
                Voxel(
                    int(row[self.INDEX_KEY]),
                    int(row[self.LONGITUDE_DEGREE_KEY]),
                    int(row[self.LATITUDE_DEGREE_KEY]),
                    int(row[self.FLIGHT_LEVEL_KEY])
                ),
                datetime.fromisoformat(row[self.TIME_KEY])
            ): float(row[self.MERGED_KEY]) if not self.__random_cost else random.random()
            for [_, row] in df.iterrows()
        }

    def find_flight_details(self) -> Dict[int, FlightDetails]:
        df: DataFrame = pd.read_csv(self.__PATH_TO_FLIGHTS_CSV + "_" + self.__problem_size + ".csv", delimiter=',')

        return {
            int(row.flight_number):
                FlightDetails(
                    TimeVoxel(
                        self.find_closest_voxel(
                            Voxel(
                                None,
                                int(row.start_longitudinal),
                                int(row.start_latitudinal),
                                int(row.start_flightlevel),
                            )
                        ),
                        datetime.fromisoformat(row.start_time)
                    ),
                    TimeVoxel(
                        self.find_closest_voxel(
                            Voxel(
                                None,
                                int(row.end_longitudinal),
                                int(row.end_latitudinal),
                                int(row.start_flightlevel)
                            )
                        ),
                        None

                    )
                )
            for [_, row] in df.iterrows()
        }

    def find_closest_voxel(self, voxel: Voxel) -> Voxel:
        index_of_closest_voxel_in_list = np.argmin(
            [self.find_distance(voxel, voxel_on_grid) for voxel_on_grid in self.voxels]
        )

        return self.voxels[index_of_closest_voxel_in_list]

    def create_constraint_quadratic_model(self, max_steps: int = 10):
        cqm = ConstrainedQuadraticModel()

        cost_for_neighbouring_voxels = self.find_cost_for_neighbouring_voxels()

        for flight_number, flight_detail in self.flight_details_by_flight_number.items():
            start_voxel_constraint = []
            destination_voxel_constraint = []
            selected_neighbours_constraint = {}
            cost_objectives = []

            for start_voxel, cost_by_neighbour_voxels in cost_for_neighbouring_voxels.items():
                selected_neighbours_constraint[start_voxel] = {}
                for neighbour_voxel, cost in cost_by_neighbour_voxels.items():
                    binary_quadratic_model = Binary(f'flight_between_voxels_{flight_number}_{start_voxel}_{neighbour_voxel}')

                    if start_voxel == flight_detail.start_voxel.voxel.index:
                        start_voxel_constraint.append(binary_quadratic_model)

                    if neighbour_voxel == flight_detail.destination_voxel.voxel.index:
                        destination_voxel_constraint.append(binary_quadratic_model)

                    selected_neighbours_constraint[start_voxel][neighbour_voxel] = binary_quadratic_model

                    cost_objectives.append(cost * binary_quadratic_model)

            cqm.add_constraint_from_model(quicksum(start_voxel_constraint), Sense.Eq, 1, label=f'flight {flight_number} start voxel constraint')
            cqm.add_constraint_from_model(quicksum(destination_voxel_constraint), Sense.Eq, 1, label=f'flight {flight_number} destination voxel constraint')

            for start_voxel, bqm_by_neighbour_voxel in selected_neighbours_constraint.items():
                for neighbour_voxel, neighbour_bqm in bqm_by_neighbour_voxel.items():
                    if neighbour_voxel == flight_detail.destination_voxel.voxel.index:
                        continue

                    next_neighbour_bqms = [next_neighbour_bqm for next_neighbour, next_neighbour_bqm in selected_neighbours_constraint[neighbour_voxel].items() if next_neighbour != start_voxel]

                    cqm.add_constraint_from_model((1 - neighbour_bqm) + neighbour_bqm * quicksum(next_neighbour_bqms), Sense.Eq, 1, label=f'next_neighbour_{flight_number}_{start_voxel}_{neighbour_voxel}')

            cqm.set_objective(quicksum(cost_objectives))

        return cqm

    def find_cost_for_neighbouring_voxels(self) -> Dict:
        cost_between_neighbouring_voxels = {}
        for time_voxel_start, cost_start in self.cost_by_voxels.items():
            cost_between_neighbouring_voxels[time_voxel_start.voxel.index] = {}
            for time_voxel_end, cost_end in self.cost_by_voxels.items():
                if time_voxel_start.voxel == time_voxel_end.voxel:
                    continue

                if time_voxel_start.time != time_voxel_end.time:
                    continue

                if time_voxel_end.voxel.index in cost_between_neighbouring_voxels.keys():
                    if time_voxel_start.voxel.index in cost_between_neighbouring_voxels[time_voxel_end.voxel.index].keys():
                        continue

                if self.find_horizontal_distance(time_voxel_start.voxel, time_voxel_end.voxel) > self.MAX_VOXEL_HORIZONTAL_DISTANCE_IN_METER:
                    continue

                if self.find_vertical_distance(time_voxel_start.voxel, time_voxel_end.voxel) > self.MAX_VOXEL_VERTICAL_DISTANCE_IN_METER:
                    continue

                cost_between_neighbouring_voxels[time_voxel_start.voxel.index][time_voxel_end.voxel.index] = self.calculate_cost(
                    time_voxel_start.voxel,
                    time_voxel_end.voxel,
                    cost_start,
                    cost_end
                )

        return cost_between_neighbouring_voxels

    def calculate_cost(self, voxel_start: Voxel, voxel_end: Voxel, cost_start_voxel: float,
                       cost_end_voxel: float) -> float:
        distance: float = self.find_distance(voxel_start, voxel_end)

        flight_direction: str = self.find_flight_direction(voxel_start.flight_level_meter, voxel_end.flight_level_meter)

        cost_K_start = self.cost_per_voxel((distance / 2), flight_direction, voxel_start, cost_start_voxel)
        cost_K_end = self.cost_per_voxel((distance / 2), flight_direction, voxel_end, cost_end_voxel)

        return cost_K_start + cost_K_end

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
        fuel_consumption_kg: float = self.calculate_fuel_consumption_in_voxel(distance, direction, voxel)

        return cost_in_voxel * fuel_consumption_kg

    def calculate_fuel_consumption_in_voxel(self, distance: float, direction: str, voxel: Voxel) -> float:
        fuel_consumption: float = self.find_fuel_consumption_for_flight_direction(direction, voxel)
        time_s = self.calculate_time_in_voxel(distance, voxel)

        return fuel_consumption * time_s

    def find_fuel_consumption_for_flight_direction(self, direction: str, voxel: Voxel) -> float:
        if direction == "DESCENT":
            return self.airplane_details[voxel.flight_level].fuel_consumption.descent_fuel_consumption_kg_s

        if direction == "CLIMB":
            return self.airplane_details[voxel.flight_level].fuel_consumption.climb_fuel_consumption_kg_s

        return self.airplane_details[voxel.flight_level].fuel_consumption.cruise_fuel_consumption_kg_s

    def calculate_time_in_voxel(self, distance: float, voxel: Voxel) -> float:
        airplane_speed: AirplaneSpeed = self.airplane_details[voxel.flight_level].airplane_speed

        return distance / airplane_speed.airplane_speed_m_s

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
