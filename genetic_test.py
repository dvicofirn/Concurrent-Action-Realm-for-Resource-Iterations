# Run the GeneticPlanner

from CARRI.simulator import Simulator
from CARRI.problem import Problem
from CARRI.parser import Translator
from genetic_planner import GeneticPlanner

def main():
    FOLDER_DOMAINS = "Examples\\Domains"
    FOLDER_PROBLEMS = "Examples\\Problems"
    DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1",),
                            "Cars": ("Cars 1",),}

    translator = Translator()
    simulator, iterations = translator.parse(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
                                             FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Cars"][0] + ".CARRI")

    population_size = 50
    generations = 100
    mutation_rate = 0.1

    # Create an instance of GeneticPlanner
    planner = GeneticPlanner(simulator=simulator, population_size=population_size, generations=generations, mutation_rate=mutation_rate)

    # Run the Genetic Planner
    best_solution = planner.run()

    # Display the best solution found
    print("Best solution:")
    for vehicle_route in best_solution:
        print(f"Vehicle Route: {vehicle_route}")


if __name__ == "__main__":
    main()