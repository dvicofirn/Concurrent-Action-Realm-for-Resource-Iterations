from CARRITranslator import CARRITranslator
from manager import Manager

FOLDER_PATH = "Trucks and Drones Problems Folder"
def main():
    translator = CARRITranslator()
    simulator, iterations = translator.translate(FOLDER_PATH + "\\" + "Domain.CARRI",
                                                 FOLDER_PATH + "\\" + "Problem.CARRI")
    #manager = Manager(simulator, 3, 3)

    actions = simulator.generate_all_valid_actions_seperatly()
    #print(actions)

    for _ in actions.keys():
        for act in actions[_].values():
            for a in act:
                x = simulator.actionStringRepresentor.represent(a)
                print(x)

    actions = simulator.generate_all_valid_actions()
    x = 1

if __name__ == '__main__':
    main()
