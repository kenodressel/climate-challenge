from src.main.visualization.Coordinate import Coordinate


class Flight:
    def __init__(self, flight_number: int, start_coordinate: Coordinate, end_coordinate: Coordinate, start_time,
                 end_time=None):
        self.flight_number = flight_number
        self.start_coordinate = start_coordinate
        self.end_coordinate = end_coordinate
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f'flight number: {self.flight_number}, start coordinate: {self.start_coordinate}, end coordinate: {self.end_coordinate}, start time: {self.start_time}, end time: {self.end_time}'
