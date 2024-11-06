from CARRI.translator import Translator
from manager import Manager


FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1",),
                        "Cars": ("Cars 1",),}
def main():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + "Cars.CARRI",
                                                 FOLDER_PROBLEMS + "\\" + DomainsProblemsDict["Cars"][0] + ".CARRI")
    manager = Manager(simulator, iterations, 1, 10, 10)
    manager.run()


if __name__ == '__main__':
    main()