
class FuelConsumption:
    def __init__(self, flight_level: int, cruise_fuel_consumption: float, descent_fuel_consumption: float, climb_fuel_consumption: float):
        self.flight_level: int = flight_level
        self.cruise_fuel_consumption_kg_min: float = cruise_fuel_consumption
        self.cruise_fuel_consumption_kg_s: float = self.cruise_fuel_consumption_kg_min / 60
        self.descent_fuel_consumption_kg_min: float = descent_fuel_consumption
        self.descent_fuel_consumption_kg_s: float = self.descent_fuel_consumption_kg_min / 60
        self.climb_fuel_consumption_kg_min: float = climb_fuel_consumption
        self.climb_fuel_consumption_kg_s: float = self.climb_fuel_consumption_kg_min / 60

    def __hash__(self):
        return hash(
            (
                self.flight_level,
                self.cruise_fuel_consumption_kg_min,
                self.cruise_fuel_consumption_kg_s,
                self.descent_fuel_consumption_kg_min,
                self.descent_fuel_consumption_kg_s,
                self.climb_fuel_consumption_kg_min,
                self.climb_fuel_consumption_kg_s
            )
        )

    def __eq__(self, other):
        if not isinstance(other, FuelConsumption):
            return False

        if self.flight_level != other.flight_level:
            return False

        return self.cruise_fuel_consumption_kg_s == other.cruise_fuel_consumption_kg_s and self.descent_fuel_consumption_kg_s == other.descent_fuel_consumption_kg_s and self.climb_fuel_consumption_kg_s == other.climb_fuel_consumption_kg_s
