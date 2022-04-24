from dimod import SampleSet
from dwave.system import LeapHybridCQMSampler

from src.main.quantum.ProblemDefinition import ProblemDefinition
from src.main.quantum.ProblemSolution import ProblemSolution


class ProblemSolver:
    def __init__(self):
        self.cqm_sampler = LeapHybridCQMSampler()

    def solve(self, problem_definition: ProblemDefinition) -> ProblemSolution:
        cqm = problem_definition.create_constraint_quadratic_model()  # Define CQM

        print("Defined constrained quadratic model! Sampling on CQM-Solver.")
        cqm_sample_set: SampleSet = self.cqm_sampler.sample_cqm(cqm, label='QuantumChallenge')  # Sample CQM on D'Wave

        return ProblemSolution(cqm_sample_set)  # Return solution


if __name__ == "__main__":
    print("Start solving problem!")
    problem_definition = ProblemDefinition("medium")

    print("Problem definition done! Continuing to solve problem.")
    problem_solver = ProblemSolver()

    problem_solution: ProblemSolution = problem_solver.solve(problem_definition)  # Solve problem

    problem_solution.print_lowest_energy_solution_with_info()
    problem_definition.print_flight_details()
