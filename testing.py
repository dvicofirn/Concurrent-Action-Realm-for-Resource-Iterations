from CARRIDomain import CARRITranslator
FILEPATH = "C:\\Users\\USER\\Documents\\Python Scripts\\PycharmProjects\\Real-Time Multi-Agent Dynamic Delivery System\\Trucks and Drones Domain.CARRI"
def main():

    translator = CARRITranslator()
    translator.create_problem(FILEPATH, FILEPATH)

if __name__ == "__main__":
    main()