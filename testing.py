from CARRITranslator import CARRITranslator
from CARRILogicParser import tokenize
from CARRIContextParser import ContextParser
from CARRILogic import ValueParameterNode
FILEPATH_DOMAIN = "Trucks and Drones Problems Folder\Domain.CARRI"
FILEPATH_PROBLEM = "Trucks and Drones Problems Folder\Problem.CARRI"

def main():
    translator = CARRITranslator()
    segments = translator.translate(FILEPATH_DOMAIN, FILEPATH_PROBLEM)[0]
    x = 1
    
    print("---Entities---")
    entities = segments['Entities']
    for entity in entities:
        print(f"{entity}: {entities[entity]}")

    print("---Variables---")
    variableSegment = segments["Variables"]
    for variable in variableSegment:
        print(f"{variable}:")
        print(variableSegment[variable])

    print("---Actions---")
    actionSegment = segments["Actions"]
    for action in actionSegment:
        print(action)
        print(actionSegment[action])

    print("---EnvSteps---")
    envStepsSegment = segments["EnvSteps"]
    for envSteps in envStepsSegment:
        print(envSteps)
        print(envStepsSegment[envSteps])
    print("---IterStep---")
    print(segments["IterStep"])
    
def tokenz(*vals):
    for val in vals:
        print(tokenize(val))

def tok(val):
    print(f'{val}: {tokenize(val)}')

def actiontokenz():
    noToTokenz = {'entity par', 'entity type', 'inherits', 'parameters'}
    translator = CARRITranslator()
    sections = translator.translate(FILEPATH_DOMAIN, FILEPATH_PROBLEM)[0]
    #print(sections[0])

    for name in sections["Actions"]:
        print(name)
        for key in sections["Actions"][name]:
            if key not in noToTokenz:
                print(f"{key}: {sections['Actions'][name][key]}")

                for val in sections["Actions"][name][key]:
                    if isinstance(val, str):
                        print(tokenize(val), end=', ')
                    else:
                        print("Block: ", val, end=', ')
                print()
    print("---Blocks---")
    tok('droneCharge id < 8')
    tok('droneCharge id : droneCharge id + 3')
    tok('package onEntity pack : 2')
    tok('package loc pack : trk')
    tok('(package onEntity pack = 1) And (package loc pack = id)')


def multiExpresTest():
    parameters = ['id', 'pack', 'trk', 'to', 'param1', 'param2', 'param3', 'param4', 'param5']
    paramExpressions = [ValueParameterNode(i) for i in range(len(parameters))]
    expressions = [
    'droneCharge id > 0',
    'droneCharge id > 0 and droneBoard id = false',
    'droneCharge id - 1',
    'locAdj (droneLoc id) ? to',
    '((droneLoc id = truckLoc trk) and (droneBoard id = false)) or ((droneLoc id = trk) and (droneBoard id = true))',
    'Not (locType to = 1)',
    'droneCap id < 1',
    'droneCap id < 1 and package onEntity pack = 0',
    '(package onEntity pack = 1) and (package loc pack = id)',
    'value1 param1 + value2 param2 / value3 - (value4 * value5)',
    'value1 param1 ? param2',
    'value2 (value1 param1) ? param2',
    'value2 (value1 param1) @ param2',
    'value3 (value1 param1) @ value param2'
    ]

if __name__ == "__main__":
    #multiExpresTest()
    #actiontokenz()
    main()