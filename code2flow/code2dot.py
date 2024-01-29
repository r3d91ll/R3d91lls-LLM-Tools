def generate_dot_representation():
    """
    Generate a DOT file content representing the flowchart.
    """
    return """
    digraph G {
        node [shape=box, style=filled, color=lightgrey];
        edge [color=black];

        start [label="Start", shape=oval];
        var_defs [label="Variable Definitions"];
        func_defs [label="Function Definitions"];
        determine_pakman [label="Determine Package Manager (PAKMAN)"];
        run_prepare_report [label="Run prepare_report Function"];
        package_cmds [label="Package Manager Specific Commands"];
        run_generate_report [label="Run generate_report Function"];
        end [label="End", shape=oval];

        start -> var_defs;
        var_defs -> func_defs;
        func_defs -> determine_pakman;
        determine_pakman -> run_prepare_report;
        run_prepare_report -> package_cmds;
        package_cmds -> run_generate_report;
        run_generate_report -> end;
    }
    """

# Generate the DOT file content
dot_file_content = generate_dot_representation()

# Save the DOT file
dot_file_path = 'flowchart.dot'
with open(dot_file_path, 'w') as file:
    file.write(dot_file_content)

dot_file_path
