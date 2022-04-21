from src.main.quantum.model.TimeVoxel import TimeVoxel


class FlightDetails:
    def __init__(self, start_voxel: TimeVoxel, end_voxel: TimeVoxel):
        self.start_voxel: TimeVoxel = start_voxel
        self.destination_voxel: TimeVoxel = end_voxel

    def __hash__(self):
        return hash((self.start_voxel, self.destination_voxel))

    def __eq__(self, other):
        if not isinstance(other, FlightDetails):
            return False

        return self.start_voxel == other.start_voxel and self.destination_voxel == other.destination_voxel

    def __str__(self):
        return f'Start voxel: ({self.start_voxel}); Destination voxel: ({self.destination_voxel})'
