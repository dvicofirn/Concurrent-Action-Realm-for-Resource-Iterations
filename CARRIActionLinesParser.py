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
            return segments, start + index
        if line.startswith("Case"):
            condition = extract_within_brackets(line.split("Case")[1]).strip()
            segment, index = parse_inside_segment(lines, start + index + 1)
            block = {"name": "case", "condition": condition, "segment": segment}
            if lines[index].startswith("Else"):
                segment, index = parse_inside_segment(lines, start + index + 1)
                block["else Segment"] = segment
            segments.append(block)

        elif line.startswith("All"):
            partition = line.split("All")[1].strip().split("-")
            part1 = partition[0].strip("(")
            parameter = part1.strip()
            part2 = partition[1].split(")")[0]
            variable = part2.strip()
            segment, index = parse_inside_segment(lines, start + index + 1)
            block = {"name": "all", "variable": variable, "parameter": parameter, "segment": segment}
            part3 = partition[1].strip(part2 + ")")
            if "(" in part3:
                condition = extract_within_brackets(part3).strip()
                block["condition"] = condition
            segments.append(block)
        else:
            segments.append(line)
        index += 1
    return segments, start + index

def parse_segment(lines):
    return parse_inside_segment(lines, 0)[0]


def startsWithSection(line: str):
    vals= {"Precs:": "preconditions",
           "Confs:": "conflicting preconditions",
           "Effects:": "effects",
           "Cost:": "costs",
           "Precs.Add:": "preconditions add",
           "Confs.Add:": "conflicting preconditions add",
           "Effects.Add:": "effects add"
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

        segmentName = startsWithSection(line)
        if segmentName is not None:
            if currentSection and section_lines:
                actions[actionName][currentSection] = parse_segment(section_lines)
            currentSection = segmentName
            section_lines = []


        elif line.startswith("EnvSteps:"):
            if currentSection and section_lines:
                actions[actionName][currentSection] = parse_segment(section_lines)
            currentSection = "environment steps"
            section_lines = []
        else:
            section_lines.append(line)

    # Handle the last section, if applicable
    if currentSection and section_lines:
        actions[actionName][currentSection] = parse_segment(section_lines)

def parse_action_header(actionHeader):
    if ":" not in actionHeader:
        raise AttributeError("No :")

    # Extract action name and parameters
    actionName, params = actionHeader.split(":")
    actionName = actionName.strip()

    # Extracting entity variable, entity type, parameters, and inheritance if applicable
    parametersAndInherits = [param.strip() for param in params.split(",")]
    entityParameter, entityType, parameters, inherits = None, None, [], None

    # Extract the entity variable and type
    if "-" in parametersAndInherits[0]:
        entityPart = parametersAndInherits[0].split("-")
        entityParameter = entityPart[0].strip()
        parameters.append(entityParameter)
        entityType = entityPart[1].strip()
    else:
        raise AttributeError("No -")

    if "(" in entityType:
        entityInheritsSplit = entityType.split("(")
        entityType = entityInheritsSplit[0].strip()
        inherits = entityInheritsSplit[1].replace(")", "").strip()
    else:
        # Extract additional parameters and inheritance, if applicable
        for part in parametersAndInherits[1:-1]:
            parameters.append(part.strip())
        part = parametersAndInherits[-1]
        if "(" in part:
            part = part.split("(")
            parameters.append(part[0].strip())
            inherits = part[1].replace(")", "").strip()

    return actionName, entityParameter, entityType, parameters, inherits