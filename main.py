from CARRITranslator import CARRITranslator
from manager import Manager
from manager import Manager
FOLDER_PATH = "Trucks and Drones Prolems Folder"
def main():
    translator = CARRITranslator()
    simulator, iterations = translator.translate(FOLDER_PATH + "\\" + "Domain.CARRI",
                                                 FOLDER_PATH + "\\" + "Problem.CARRI")
    #manager = Manager(simulator, 3, 3)

if __name__ == '__main__':
    main()
