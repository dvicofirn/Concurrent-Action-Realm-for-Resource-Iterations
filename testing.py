from CARRITranslator import CARRITranslator
from CARRILogicParser import tokenize, parse_expression
from CARRILogic import ParameterNode
FILEPATH = "C:\\Users\\USER\\Documents\\Python Scripts\\PycharmProjects\\Real-Time Multi-Agent Dynamic Delivery System\\Trucks and Drones Domain.CARRI"
def main():
    translator = CARRITranslator()
    segments = translator.translate(FILEPATH, FILEPATH)[0]
    entities = segments['Entities']
    for entity in entities:
        print(f"{entity} {entities[entity]}")

    actionSegment = segments["Actions"]
    for action in actionSegment:
        print(action)
        print(actionSegment[action])

def tokenz(*vals):
    for val in vals:
        print(tokenize(val))

def tok(val):
    print(f'{val}: {tokenize(val)}')

def actiontokenz():
    noToTokenz = {'entity par', 'entity type', 'inherits', 'parameters'}
    translator = CARRITranslator()
    sections = translator.translate(FILEPATH, FILEPATH)[0]
    #print(sections[0])

    for name in sections["Actions"]:
        print(name)
        for key in sections["Actions"][name]:
            if key not in noToTokenz:
                print(f'{key}: {sections["Actions"][name][key]}')
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

def expres(val, params, expParams, parsedEntities):
    print(f'{val}:{parse_expression(val, params, expParams, parsedEntities)}')
    try:
        print(parse_expression(val, params, expParams, parsedEntities).evaluate(None, None))
    except Exception as e:
        print("not yet")

def test_parse_expression(expression_str, parameters, paramExpressions, parsedEntities):
    print(f"Parsing expression: {expression_str}")

    try:
        expressed = parse_expression(expression_str, parameters, paramExpressions, parsedEntities)
        print(f"Parsed Expression Node:{expressed}\n")
    except Exception as e:
        print(f"Error parsing expression: {e}\n")

def multiExpresTest():
    parameters = ['id', 'pack', 'trk', 'to', 'param1', 'param2', 'param3', 'param4', 'param5']
    paramExpressions = [ParameterNode(i) for i in range(len(parameters))]
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
    for expr in expressions:
        test_parse_expression(expr, parameters, paramExpressions, [])

if __name__ == "__main__":
    #multiExpresTest()
    #actiontokenz()
    main()
