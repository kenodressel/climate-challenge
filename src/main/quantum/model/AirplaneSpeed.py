
class AirplaneSpeed:
    __KNOTS_PER_METER_PER_SECOND: float = 1.94384
    __METER_PER_FEET: float = 0.3048

    def __init__(self, flight_level: int, airplane_speed: float, rate_of_descent: float, rate_of_climb: float):
        self.flight_level: int = flight_level
        self.airplane_speed_kts: float = airplane_speed
        self.airplane_speed_m_s: float = self.airplane_speed_kts / self.__KNOTS_PER_METER_PER_SECOND
        self.rate_of_descent_ft_per_s: float = rate_of_descent / 60
        self.rate_of_climb_m_per_s: float = rate_of_climb * self.__METER_PER_FEET / 60

    def __hash__(self):
        return hash(
            (
                self.flight_level,
                self.airplane_speed_kts,
                self.airplane_speed_m_s,
                self.rate_of_descent_ft_per_s,
                self.rate_of_climb_m_per_s
            )
        )

    def __eq__(self, other):
        if not isinstance(other, AirplaneSpeed):
            return False

        if self.flight_level != other.flight_level:
            return False

        return self.airplane_speed_m_s == other.airplane_speed_m_s and self.rate_of_climb_m_per_s == other.rate_of_climb_m_per_s
