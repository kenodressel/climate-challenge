from datetime import datetime
from typing import Optional

from src.main.quantum.model.Voxel import Voxel


class TimeVoxel:
    def __init__(self, voxel: Voxel, time: Optional[datetime]):
        self.voxel = voxel
        self.time = time

    def __hash__(self):
        return hash((self.voxel, self.time))

    def __eq__(self, other):
        if not isinstance(other, TimeVoxel):
            return False

        return self.voxel == other.voxel and self.time == other.time

    def __str__(self):
        return f'Voxel: ({self.voxel}); Time: ({self.time})'
