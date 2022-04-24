from typing import AnyStr, List, Tuple, Dict

from dimod import SampleSet

from src.main.quantum.model.Voxel import Voxel


class ProblemSolution:
    def __init__(self, cqm_sample_set: SampleSet | None):
        self.cqm_sample_set = cqm_sample_set
        self.__lowest_energy_flight_path, self.__lowest_cost = self.__find_lowest_energy_solution()

    def __get_run_time(self) -> AnyStr:
        return self.cqm_sample_set.info['run_time']

    def __get_qpu_access_time(self) -> AnyStr:
        return self.cqm_sample_set.info['qpu_access_time']

    def __get_problem_id(self) -> AnyStr:
        return self.cqm_sample_set.info['problem_id']

    def __get_problem_label(self) -> AnyStr:
        return self.cqm_sample_set.info['problem_label']

    def __find_lowest_energy_solution(self) -> Tuple[List[AnyStr], int]:
        df = self.cqm_sample_set.to_pandas_dataframe(True)

        feasible_solutions_df = df[df["is_feasible"]]  # Only feasible solution satisfy all constraints
        if len(feasible_solutions_df["energy"]) == 0:
            print("No solution found!")
            return [], 0

        lowest_energy_solution = feasible_solutions_df.iloc[
            [feasible_solutions_df["energy"].argmin()]]  # Find feasible solution with the lowest energy (climate cost)
        lowest_energy_solution_flight_path = [key for key, value in lowest_energy_solution["sample"].values[0].items()
                                              if
                                              value == 1]  # Find flight path for feasible solution with lowest energy (climate cost). This returns only those binary variables equal to one (active flight edges between voxels)

        return lowest_energy_solution_flight_path, lowest_energy_solution["energy"].values[
            0]  # Return flight path and climate cost for feasible solution with lowest energy

    def print_lowest_energy_solution_with_info(self) -> None:
        print(f'Done! Sampler info is:\n'
              f'run_time -> {self.__get_run_time() / 1000} ms,\n'
              f'qpu_access_time -> {self.__get_qpu_access_time() / 1000} ms,\n'
              f'problem_id -> {self.__get_problem_id()},\n'
              f'problem_label -> {self.__get_problem_label()}!'
              )

        self.print_lowest_energy_solution()

    def print_lowest_energy_solution(self) -> None:
        print(f'Flight path is: {self.__lowest_energy_flight_path}\n'
              f'Cost is {self.__lowest_cost}')

    def find_flight_paths(self, voxels: List[Voxel]):
        return self.__parse_solution(self.__lowest_energy_flight_path, voxels)

    def __parse_solution(self, binary_variables: List[AnyStr], voxels: List[Voxel]) -> Dict[int, List[Voxel]]:
        flight_paths = {}
        for binary_variable in binary_variables:
            splitted_string = binary_variable.split("_")

            flight_number = int(splitted_string[1])
            start_voxel = [voxel for voxel in voxels if voxel.index == int(splitted_string[4])][0]
            neighbour_voxel = [voxel for voxel in voxels if voxel.index == int(splitted_string[5])][0]

            if not flight_number in flight_paths.keys():
                flight_paths[flight_number] = []

            if not start_voxel in flight_paths[flight_number]:
                flight_paths[flight_number].append(start_voxel)

            if not neighbour_voxel in flight_paths[flight_number]:
                flight_paths[flight_number].append(neighbour_voxel)

        return flight_paths
