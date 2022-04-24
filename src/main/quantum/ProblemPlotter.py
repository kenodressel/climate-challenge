import random
from typing import List, Dict

from matplotlib import pyplot as plt

from src.main.quantum.model.Voxel import Voxel


class ProblemPlotter:
    def __init__(self, grid: List[Voxel]):

        self.__fig = plt.figure(dpi=600)
        self.__ax = self.__fig.add_subplot(projection='3d')

        longitudinal_min, longitudinal_max = self.__find_longitudinal_range(grid)
        self.__ax.set_xlabel('longitudinal')
        self.__ax.set_xlim(longitudinal_min, longitudinal_max)

        latitudinal_min, latitudinal_max = self.__find_latitudinal_range(grid)
        self.__ax.set_ylabel('latitudinal')
        self.__ax.set_ylim(latitudinal_min, latitudinal_max)

        flight_level_min, flight_level_max = self.__find_flight_level_range(grid)
        self.__ax.set_zlabel('flight level')
        self.__ax.set_zlim(flight_level_min, flight_level_max)

    def __find_longitudinal_range(self, grid: List[Voxel]):
        longitudinal_range = self.__find_longitudinal_values(grid)
        return min(longitudinal_range), max(longitudinal_range)

    def __find_latitudinal_range(self, grid: List[Voxel]):
        latitudinal_range = self.__find_latitudinal_values(grid)
        return min(latitudinal_range), max(latitudinal_range)

    def __find_flight_level_range(self, grid: List[Voxel]):
        flight_level_range = self.__find_flight_level_values(grid)
        return min(flight_level_range), max(flight_level_range)

    def __find_longitudinal_values(self, voxels: List[Voxel]):
        return [voxel.longitude_degree for voxel in voxels]

    def __find_latitudinal_values(self, voxels: List[Voxel]):
        return [voxel.latitude_degree for voxel in voxels]

    def __find_flight_level_values(self, voxels: List[Voxel]):
        return [voxel.flight_level for voxel in voxels]

    def plot(self, flight_paths: Dict[int, List[Voxel]]):

        for flight_number, flight_path in flight_paths.items():
            longitudinal_points = self.__find_longitudinal_values(flight_path)
            latitudinal_points = self.__find_latitudinal_values(flight_path)
            flight_level_points = self.__find_flight_level_values(flight_path)

            self.__ax.plot(
                longitudinal_points,
                latitudinal_points,
                flight_level_points,
                alpha=0.5,
                label=f'Flight number: {flight_number + 1}'
            )

        self.__fig.legend()
        plt.show()

if __name__ == '__main__':
    grid = [
        Voxel(
            random.randint(0, 1000),
            longitude,
            latitude,
            flight_level
        ) for longitude in range (0, 10) for latitude in range(0, 10) for flight_level in range(0, 10)
    ]

    flight_paths = {
        0: [
            Voxel(
                random.randint(0, 1000),
                0,
                0,
                2
            ),
            Voxel(
                random.randint(0, 1000),
                0,
                1,
                2
            ),
            Voxel(
                random.randint(0, 1000),
                0,
                2,
                2
            ),
            Voxel(
                random.randint(0, 1000),
                1,
                2,
                3
            ),
        ],
        1: [

            Voxel(
                random.randint(0, 1000),
                5,
                0,
                2
            ),
            Voxel(
                random.randint(0, 1000),
                4,
                1,
                2
            ),
            Voxel(
                random.randint(0, 1000),
                3,
                2,
                2
            ),
            Voxel(
                random.randint(0, 1000),
                2,
                2,
                3
            ),
        ]
    }

    problem_plotter = ProblemPlotter(grid)

    problem_plotter.plot(flight_paths)
