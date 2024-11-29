import re

def parse_cells(liberty_content):
    """
    Parses Liberty file and captures each cell's content fully.
    """
    cells = {}
    cell_start_pattern = r'cell\s*\(\s*"([^"]+)"\s*\)\s*\{'  # Match the cell name
    stack = []
    current_cell_name = None
    current_cell_content = []
    inside_cell = False

    for line in liberty_content.splitlines():
        line = line.strip()
        if re.match(cell_start_pattern, line):
            # Start of a cell
            inside_cell = True
            current_cell_name = re.match(cell_start_pattern, line).group(1)
            stack.append("{")
            current_cell_content.append(line)
        elif inside_cell:
            # Handle nested braces and closing braces
            if "{" in line:
                stack.append("{")
            if "}" in line:
                stack.pop()
            current_cell_content.append(line)
            
            # End of the cell
            if not stack:
                inside_cell = False
                cells[current_cell_name] = "\n".join(current_cell_content)
                current_cell_content = []
                current_cell_name = None

    return cells

def extract_pins(cell_raw_data):
    """
    Extracts all pin definitions from a cell's raw data.
    """
    # Regex to match pin blocks
    pin_pattern = r'pin\s*\(\s*"([^"]+)"\s*\)\s*\{(.*?)\}'
    
    # Use re.DOTALL to capture multi-line pin content
    matches = re.finditer(pin_pattern, cell_raw_data, re.DOTALL)
    
    pins = {}
    for match in matches:
        pin_name = match.group(1)  # Pin name
        pin_data = match.group(2).strip()  # Pin content
        pins[pin_name] = pin_data

    return pins
def classify_pins(pins):
    """
    Classifies pins into inputs and outputs, and extracts functions for outputs.
    """
    inputs = []
    outputs = {}
    
    for pin_name, pin_data in pins.items():
        # Check the direction
        direction_match = re.search(r'direction\s*:\s*"(input|output)";', pin_data)
        if direction_match:
            direction = direction_match.group(1)
            if direction == "input":
                inputs.append(pin_name)
            elif direction == "output":
                # Extract the function for outputs
                function_match = re.search(r'function\s*:\s*"([^"]+)"', pin_data)
                function = function_match.group(1) if function_match else None
                outputs[pin_name] = function
    
    return inputs, outputs
# Parse the Liberty file content
parsed_cells = parse_cells(open('sky130_fd_sc_hd__ss_n40C_1v76.lib').read())

for cell_name, raw_data in parsed_cells.items():
    print(f"Cell: {cell_name}" + ' {')
    pins = extract_pins(raw_data)
    inputs, outputs = classify_pins(pins)
    
    # Format the results
    inputs_str = " ".join(inputs)
    for output, function in outputs.items():
        cleaned_input = re.sub(r'\bS\b', 'S0', inputs_str)
        cleaned_output = re.sub(r'\bS\b', 'S0', output)
        if function is not None:
            cleaned_function = re.sub(r'\bS\b', 'S0', function)
        else:
            cleaned_function = None
        print(f"  Inputs: {cleaned_input}")
        print(f"  Output: {cleaned_output}")
        print(f"  Function: {cleaned_function}")
    print('}\n')