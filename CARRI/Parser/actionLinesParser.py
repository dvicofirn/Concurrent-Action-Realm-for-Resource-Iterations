import re

def extract_within_brackets(str):
    """
    Extract content within parentheses if the string matches the pattern '(content):',
    else return the original string.
    """
    # The regex matches a string that starts with '(', captures content until '):', and ends with '):', allowing optional spaces
    match = re.search(r'^\s*\(\s*(.*?)\s*\):\s*$', str)
    if match:
        return match.group(1)  # Extract the content inside the parentheses
    return str  # Return the original string if no match

def parse_inside_segment(lines, start):
    """
    Recursively parse lines starting from 'start' index into segments representing code blocks.
    Returns a list of segments and the updated index.
    """
    segments = []
    index = start
    while index < len(lines):
        line = lines[index]
        line = line.strip()
        if line.startswith("End") or line.startswith("Else"):
            return segments, index
        if line.startswith("Case"):
            # Extract condition within brackets after 'Case'
            condition = extract_within_brackets(line.split("Case")[1]).strip()
            # Recursively parse the segment inside the 'Case' block
            segment, index = parse_inside_segment(lines, index + 1)
            block = {"name": "case", "condition": condition, "segment": segment}
            # Check for 'Else' block following 'Case'
            if lines[index].startswith("Else"):
                segment, index = parse_inside_segment(lines, index + 1)
                block["else segment"] = segment
            segments.append(block)

        elif line.startswith("All"):
            # Parse 'All' block, extract parameter and entity
            partition = line.split("All")[1].strip().split("-")
            part1 = partition[0].strip("(")
            parameter = part1.strip()
            part2 = partition[1].split(")")[0]
            entity = part2.strip()
            # Recursively parse the segment inside the 'All' block
            segment, index = parse_inside_segment(lines, index + 1)
            block = {"name": "all", "entity": entity, "parameter": parameter, "segment": segment}
            # Check for optional condition within the 'All' block
            part3 = partition[1].strip(part2 + ")")
            if "(" in part3:
                condition = extract_within_brackets(part3).strip()
                block["condition"] = condition
            segments.append(block)
        elif line.startswith("Repeat"):
            # Extract condition within brackets after 'Repeat'
            condition = extract_within_brackets(line.split("Repeat")[1]).strip()
            # Recursively parse the segment inside the 'Repeat' block
            segment, index = parse_inside_segment(lines, index + 1)
            block = {"name": "repeat", "condition": condition, "segment": segment}
            segments.append(block)
        else:
            # Append regular line to segments
            segments.append(line)
        index += 1
    return segments, index

def parse_segment(lines):
    """Parse the given lines into segments starting from index 0."""
    return parse_inside_segment(lines, 0)[0]

def starts_with_section(line: str):
    """Check if the line starts with a known section header and return the corresponding section name."""
    vals = {
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

def parse_action_segments(actionLines, actions, actionName):
    """
    Helper function to parse segments of an action such as Preconditions, Effects, Costs, etc.
    Uses parse_segment to handle complex blocks like Case and All.
    """
    currentSection = None
    sectionLines = []

    for line in actionLines:
        line = line.strip()
        if not line:
            continue

        segmentName = starts_with_section(line)
        if segmentName is not None:
            if currentSection and sectionLines:
                # Parse the previous section and store it
                actions[actionName][currentSection] = parse_segment(sectionLines)
            currentSection = segmentName
            sectionLines = []
        else:
            sectionLines.append(line)

    # Handle the last section, if applicable
    if currentSection and sectionLines:
        actions[actionName][currentSection] = parse_segment(sectionLines)

def parse_action_header(actionHeader):
    """
    Parse the action header line to extract the action name, parameters, entities, and inheritance.
    Returns a tuple containing actionName, parameters, entities, and inherits.
    """
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
                # Split parameter into name and associated entity
                paramName, entityName = map(str.strip, param.split('-'))
                parameters.append(paramName)
                entities.append(entityName)
            else:
                raise AttributeError("Each parameter should include an entity with '-' separator")

    # Return results with empty lists and None for missing values
    return actionName, parameters or None, entities or None, inherits
