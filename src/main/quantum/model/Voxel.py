from typing import Optional


class Voxel:
    __METER_PER_DEGREE_LATITUDE: int = 111000
    __METER_PER_DEGREE_LONGITUDE: int = 85000
    __METER_PER_FEET: float = 0.3048
    __FEET_PER_FLIGHT_LEVEL: int = 100
    __METER_PER_FLIGHT_LEVEL: float = __METER_PER_FEET * __FEET_PER_FLIGHT_LEVEL

    def __init__(self, index: Optional[int], longitude: int, latitude: int, flight_level: int):
        self.index: int = index
        self.longitude_degree: int = longitude
        self.longitude_meter: float = self.longitude_degree * self.__METER_PER_DEGREE_LONGITUDE
        self.latitude_degree: int = latitude
        self.latitude_meter: float = self.latitude_degree * self.__METER_PER_DEGREE_LATITUDE
        self.flight_level: int = flight_level
        self.flight_level_meter: float = flight_level * self.__METER_PER_FLIGHT_LEVEL

    def __hash__(self):
        return hash(
            (
                self.index,
                self.longitude_degree,
                self.longitude_meter,
                self.latitude_degree,
                self.latitude_meter,
                self.flight_level,
                self.flight_level_meter
            )
        )

    def __eq__(self, other):
        if not isinstance(other, Voxel):
            return False

        if self.index == other.index and self.index is not None and other.index is not None:
            return True

        return self.longitude_meter == other.longitude_meter and self.latitude_meter == other.latitude_meter and self.flight_level_meter == other.flight_level_meter

    def __str__(self):
        return f'Index: {self.index}; Latitude: {self.latitude_degree}; Longitude: {self.longitude_degree}; Flight level: {self.flight_level}'
