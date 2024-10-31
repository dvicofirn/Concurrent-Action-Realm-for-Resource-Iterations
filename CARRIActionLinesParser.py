import re
def extract_within_brackets(str):
    # The regex matches optional spaces, followed by '(', captures the content until '):' and ignores the last part
    match = re.search(r'^\s*\(\s*(.*?)\s*\):\s*$', str)
    if match:
        return match.group(1)  # Extract the content inside the parentheses
    return str  # Return the original string if no match
def parse_inside_segment(lines, start):
    segments = []
    index = start
    while index < len(lines):
        line = lines[index]
        line = line.strip()
        if line.startswith("End") or line.startswith("Else"):
            return segments, index
        if line.startswith("Case"):
            condition = extract_within_brackets(line.split("Case")[1]).strip()
            segment, index = parse_inside_segment(lines, index + 1)
            block = {"name": "case", "condition": condition, "segment": segment}
            if lines[index].startswith("Else"):
                segment, index = parse_inside_segment(lines, index + 1)
                block["else Segment"] = segment
            segments.append(block)

        elif line.startswith("All"):
            partition = line.split("All")[1].strip().split("-")
            part1 = partition[0].strip("(")
            parameter = part1.strip()
            part2 = partition[1].split(")")[0]
            entity = part2.strip()
            segment, index = parse_inside_segment(lines, index + 1)
            block = {"name": "all", "entity": entity, "parameter": parameter, "segment": segment}
            part3 = partition[1].strip(part2 + ")")
            if "(" in part3:
                condition = extract_within_brackets(part3).strip()
                block["condition"] = condition
            segments.append(block)
        else:
            segments.append(line)
        index += 1
    return segments, index

def parse_segment(lines):
    return parse_inside_segment(lines, 0)[0]


def starts_with_section(line: str):
    vals= {
        "Precs:": "preconditions",
        "Confs:": "conflicting preconditions",
        "Effects:": "effects",
        "Cost:": "cost",
        "Precs Add:": "preconditions add",
        "Confs Add:": "conflicting preconditions add",
        "Effects Add:": "effects add"
           }
    for key in vals:
        if line.startswith(key):
            return vals[key]
    else:
        return None

def parse_action_segments(action_lines, actions, actionName):
    """
    Helper function to parse segments of an action such as Preconditions, Effects, Costs, etc.
    Uses SegmentParser to handle complex blocks like Case and FindAll.
    """
    currentSection = None
    section_lines = []

    for line in action_lines:
        line = line.strip()
        if not line:
            continue

        segmentName = starts_with_section(line)
        if segmentName is not None:
            if currentSection and section_lines:
                actions[actionName][currentSection] = parse_segment(section_lines)
            currentSection = segmentName
            section_lines = []
        else:
            section_lines.append(line)

    # Handle the last section, if applicable
    if currentSection and section_lines:
        actions[actionName][currentSection] = parse_segment(section_lines)

def parse_action_header(actionHeader):
    # Define regex to parse the action header
    pattern = r'^(?P<actionName>\w+):\s*(?P<params>.*?)(?:\((?P<inherits>\w+)\))?$'
    match = re.match(pattern, actionHeader.strip())

    if not match:
        raise ValueError("Invalid format")

    # Extract action name and inherited function if it exists
    actionName = match.group('actionName')
    inherits = match.group('inherits')

    # Process parameters and entities
    params = match.group('params')
    parameters, entities = [], []

    if params:
        for param in params.split(','):
            param = param.strip()
            if '-' in param:
                param_name, entity_name = map(str.strip, param.split('-'))
                parameters.append(param_name)
                entities.append(entity_name)
            else:
                raise AttributeError("Each parameter should include an entity with '-' separator")

    # Return results with empty lists and None for missing values
    return actionName, parameters or None, entities or None, inherits