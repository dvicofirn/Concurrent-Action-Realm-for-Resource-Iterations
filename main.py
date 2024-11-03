from CARRITranslator import CARRITranslator
from manager import Manager
from planner import Planner

FOLDER_PATH = "Cars Problems Folder"
def main():
    translator = CARRITranslator()
    simulator, iterations = translator.translate(FOLDER_PATH + "\\" + "Domain.CARRI",
                                                 FOLDER_PATH + "\\" + "Problem.CARRI")
    #manager = Manager(simulator, 3, 3)

    '''
    actions = simulator.generate_all_valid_actions_seperatly()

    for _ in actions.keys():
        for act in actions[_].values():
            for a in act:
                x = simulator.actionStringRepresentor.represent(a)
                print(x)

    actions = simulator.generate_all_valid_actions()
    i = 0
    for act in actions :
        print('\n')
        print(f'full reduced action {i}')
        for a in act:
            x = simulator.actionStringRepresentor.represent(a)
            print(x)
        i += 1

    '''
    succesors = simulator.generate_successor_states()
    init_time = 5.0
    iter_t = 5.0


    planner = Planner(simulator, init_time, iter_t)
    planner.run_iteration()


if __name__ == '__main__':
    main()
