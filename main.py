from CARRI.translator import Translator
from manager import Manager


FOLDER_DOMAINS = "Examples\\Domains"
FOLDER_PROBLEMS = "Examples\\Problems"
DomainsProblemsDict = {"Trucks and Drones": ("Trucks and Drones 1",),
                        "Cars": ("Cars 1",),}
instance = 'Cars' #"Trucks and Drones"

def main():
    translator = Translator()
    simulator, iterations = translator.translate(FOLDER_DOMAINS + "\\" + instance + ".CARRI",
                                                 FOLDER_PROBLEMS + "\\" + DomainsProblemsDict[instance][0] + ".CARRI")
    manager = Manager(simulator, iterations, 1,7, 10)
    manager.run() 


if __name__ == '__main__':
    main()