

class Coordinate:
    def __init__(self, longitudinal: int, latitudinal: int, flight_level: int = None):
        self.longitudinal = longitudinal
        self.latitudinal = latitudinal
        self.flight_level = flight_level

    def __repr__(self):
        return f'longitudinal: {self.longitudinal}, latitudinal: {self.latitudinal}, flight level: {self.flight_level}'
