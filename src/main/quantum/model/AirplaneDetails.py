from src.main.quantum.model.AirplaneSpeed import AirplaneSpeed
from src.main.quantum.model.FuelConsumption import FuelConsumption


class AirplaneDetails:
    def __init__(self, airplane_speed: AirplaneSpeed, fuel_consumption: FuelConsumption):
        self.airplane_speed = airplane_speed
        self.fuel_consumption = fuel_consumption

    def __hash__(self):
        return hash((self.airplane_speed, self.fuel_consumption))

    def __eq__(self, other):
        if not isinstance(other, AirplaneDetails):
            return False

        return self.airplane_speed == other.airplane_speed and self.fuel_consumption == other.fuel_consumption
