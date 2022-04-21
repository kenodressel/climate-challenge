import csv
from datetime import datetime
from typing import List

import imageio as imageio
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors, markers

from src.main.visualization.Coordinate import Coordinate
from src.main.visualization.Flight import Flight


class Visualization:
    __PATH_TO_FLIGHTS_CSV = "../../resources/data/flights_big.csv"
    __PATH_TO_VISUALIZATION_DATA = '../../resources/visualization'

    def __init__(self):
        self.flights: List[Flight] = self.read_in_flights()

    def plot_flights(self):
        available_colors = [i for i in colors.cnames.keys()]

        longitudinal_start = [flight.start_coordinate.longitudinal for flight in self.flights]
        longitudinal_end = [flight.end_coordinate.longitudinal for flight in self.flights]
        longitudinal_min = min(min(longitudinal_start), min(longitudinal_end))
        longitudinal_max = max(max(longitudinal_start), max(longitudinal_end))

        latitudinal_start = [flight.start_coordinate.latitudinal for flight in self.flights]
        latitudinal_end = [flight.end_coordinate.latitudinal for flight in self.flights]
        latitudinal_min = min(min(latitudinal_start), min(latitudinal_end))
        latitudinal_max = max(max(latitudinal_start), max(latitudinal_end))

        flight_level_start = [flight.start_coordinate.flight_level for flight in self.flights]
        flight_level_min = min(flight_level_start)
        flight_level_max = max(flight_level_start)

        start_times = [flight.start_time for flight in self.flights]
        start_times.sort()

        images = []

        fig = plt.figure(dpi=600)
        ax = fig.add_subplot(projection='3d')

        ax.set_xlabel('longitudinal')
        ax.set_ylabel('latitudinal')
        ax.set_zlabel('flight level')

        ax.set_xlim(longitudinal_min, longitudinal_max)
        ax.set_ylim(latitudinal_min, latitudinal_max)
        ax.set_zlim(flight_level_min, flight_level_max)

        flight: Flight
        for flight in self.flights:
            longitudinal_points = [flight.start_coordinate.longitudinal, flight.end_coordinate.longitudinal]
            latitudinal_points = [flight.start_coordinate.latitudinal, flight.end_coordinate.latitudinal]
            flight_levels = [flight.start_coordinate.flight_level, flight.start_coordinate.flight_level]

            ax.scatter(
                flight.start_coordinate.longitudinal,
                flight.start_coordinate.latitudinal,
                flight.start_coordinate.flight_level,
                alpha=0.9,
                c=available_colors[flight.flight_number],
                marker=markers.CARETUPBASE
            )

            ax.scatter(
                flight.end_coordinate.longitudinal,
                flight.end_coordinate.latitudinal,
                flight.start_coordinate.flight_level,
                alpha=0.1,
                c=available_colors[flight.flight_number],
                marker=markers.CARETDOWNBASE
            )

            ax.plot(
                longitudinal_points,
                latitudinal_points,
                flight_levels,
                alpha=0.5,
                c=available_colors[start_times.index(flight.start_time)]
            )

            plt.title("Start time: {0}".format(flight.start_time))

            fig.canvas.draw()
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))

            images.append(image)

        kwargs_write = {'fps': 1.0, 'quantizer': 'nq'}
        imageio.mimsave(self.__PATH_TO_VISUALIZATION_DATA + '/flights.gif', images, fps=1)


    def read_in_flights(self) -> List[Flight]:
        flights = []
        with open(self.__PATH_TO_FLIGHTS_CSV, "r") as flights_file:
            flight_reader = csv.reader(flights_file, delimiter=',')
            next(flight_reader, None)
            for row in flight_reader:
                start_time = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
                start_coordinate = Coordinate(longitudinal=int(row[3]), latitudinal=int(row[4]), flight_level=int(row[2]))
                end_coordinate = Coordinate(longitudinal=int(row[5]), latitudinal=int(row[6]))
                flight = Flight(flight_number=int(row[0]), start_coordinate=start_coordinate, end_coordinate=end_coordinate,
                                start_time=start_time)
                flights.append(flight)

        flights.sort(key=lambda flight_to_sort: flight_to_sort.start_time)
        return flights


if __name__ == "__main__":
    visualization = Visualization()

    visualization.plot_flights()
