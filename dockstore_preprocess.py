#!/usr/bin/env python3

import argparse
import WDL

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--input-wdl-path", required=True)
args = parser.parse_args()

doc = WDL.load(args.input_wdl_path)         # loads the entire document

# converts all tabs to spaces for compatibility
def tabs_to_spaces():
    for line in doc.source_lines:
        line.replace('\t', "        ")

# add docker to every task and workflow explicitly
def docker_runtime():
    for task in doc.tasks:
        if("docker" not in task.runtime):   # need to add docker to runtime, inputs, and call
            # @@@@@@@@@@@@@@@
            print("placeholder")

# source .bashrc and load required modules for each task
def source_modules():
    for task in doc.tasks:
        for input in task.inputs:
            index = doc.source_lines[input.pos.line - 1].find("String modules")
            if index > -1:  # if the task does use modules
                position = task.command.pos.line
                num_spaces = doc.source_lines[position].rfind("  ") + 2
                append = ' ' * num_spaces + 'source /home/ubuntu/.bashrc \n' + ' ' * num_spaces + '~{"module load " + modules + " || exit 1; "} \n\n' + ' ' * num_spaces
                doc.source_lines[position] = append + doc.source_lines[position][num_spaces:]  # replace old command with the new

# find all params that need to be replaced, for example:
def test():
    for task in doc.tasks:
        print(type(task))
        print(type(task.command))
        print(type(task.command.parts))
        print(type(task.command.parts[0]))
        print(type(doc.tasks[0].inputs[0]))
        print(type(doc.tasks[0].inputs[0].pos))

# final outputs to stdout or a file with modified name
def write_out():
    # print("\n".join(doc.source_lines))      # prints the entire workflow to stdout

    name_index = args.input_wdl_path.rfind('/')
    output_path = args.input_wdl_path[:name_index + 1] + "dockstore_" + args.input_wdl_path[name_index + 1:]
    with open(output_path, "w") as output_file:
        output_file.write("\n".join(doc.source_lines))

tabs_to_spaces()
# test()
source_modules()
write_out()     # successfully creates / overwrites to the right destination