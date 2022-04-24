from dimod import SampleSet
from typing import AnyStr, List, Tuple


class ProblemSolution:
    def __init__(self, cqm_sample_set: SampleSet):
        self.cqm_sample_set = cqm_sample_set
        self.lowest_energy_flight_path, self.lowest_cost = self.find_lowest_energy_solution()

    def get_run_time(self) -> AnyStr:
        return self.cqm_sample_set.info['run_time']

    def get_qpu_access_time(self) -> AnyStr:
        return self.cqm_sample_set.info['qpu_access_time']

    def get_problem_id(self) -> AnyStr:
        return self.cqm_sample_set.info['problem_id']

    def get_problem_label(self) -> AnyStr:
        return self.cqm_sample_set.info['problem_label']

    def find_lowest_energy_solution(self) -> Tuple[List[AnyStr], int]:
        df = self.cqm_sample_set.to_pandas_dataframe(True)

        feasible_solutions_df = df[df["is_feasible"]]  # Only feasible solution satisfy all constraints
        if len(feasible_solutions_df["energy"]) == 0:
            print("No solution found!")
            return [], 0

        lowest_energy_solution = feasible_solutions_df.iloc[[feasible_solutions_df["energy"].argmin()]] # Find feasible solution with the lowest energy (climate cost)
        lowest_energy_solution_flight_path = [key for key, value in lowest_energy_solution["sample"].values[0].items() if value == 1]  # Find flight path for feasible solution with lowest energy (climate cost). This returns only those binary variables equal to one (active flight edges between voxels)

        return lowest_energy_solution_flight_path, lowest_energy_solution["energy"].values[0]  # Return flight path and climate cost for feasible solution with lowest energy

    def print_lowest_energy_solution_with_info(self):
        print(f'Done! Sampler info is:\n'
              f'run_time -> {self.get_run_time()},\n'
              f'qpu_access_time -> {self.get_qpu_access_time()},\n'
              f'problem_id -> {self.get_problem_id()},\n'
              f'problem_label -> {self.get_problem_label()}!'
              )

        self.print_lowest_energy_solution()

    def print_lowest_energy_solution(self):
        print(f'Flight path is: {self.lowest_energy_flight_path}\n'
              f'Cost is {self.lowest_cost}')
