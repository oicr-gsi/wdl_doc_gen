#!/usr/bin/env python3

import argparse
import re
import WDL

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--input-wdl-path", required=True)
parser.add_argument("--docker-image", required=False)
args = parser.parse_args()

doc = WDL.load(args.input_wdl_path)         # loads the entire document

# converts all tabs to spaces for compatibility
def tabs_to_spaces(num_spaces):     # what about multiple tabs, or tab is in a string?
    for index in range(len(doc.source_lines)):
        line = doc.source_lines[index].lstrip('\t')     # strips leading tabs
        num_tabs = len(doc.source_lines[index]) - len(line)     # how many tabs were stripped away
        doc.source_lines[index] = " " * num_spaces * num_tabs + line

# helper function: add "docker = docker" to a call with a multi-line input section
def docker_runtime_multi(part):
    # either multi-line has docker or hasn't, but will not be empty (single line)
    line_pos = part.pos.line - 1
    if "docker" not in part.inputs.keys():
        print("add comma docker = to the beginning")
        line_pos += 2 if "input:" in doc.source_lines[line_pos + 1] else 1   # first line with input vars
        line = doc.source_lines[line_pos]
        num_spaces = len(line) - len(line.lstrip(' '))
        prepend = " " * num_spaces + "docker = docker,\n"
        doc.source_lines[line_pos] = prepend + line

    else:
        while "docker" not in doc.source_lines[line_pos]:   # stops when line contains docker
            line_pos += 1
        line = doc.source_lines[line_pos]
        index1 = line.find("docker") + len("docker")
        while line[index1] in " =":  # move forward until at start of assignment
            index1 += 1
        index2 = len(line) - 1  # initialize at end of line
        for c in "} ,":         # value ends in ,/ /} whichever is smallest but must > -1
            index_temp = line[index1:].find(c) + index1
            index2 = index_temp if index_temp >  index1 - 1 and index_temp < index2 else index2
        line = line[:index1] + "docker" + line[index2:]
        doc.source_lines[line_pos] = line

# helper function: add "docker = docker" to a call with a single line input section
def docker_runtime_single(part):
    line = doc.source_lines[part.pos.line - 1]
    if not part.inputs:     # if input section empty, add "input: docker"
        index = len(line) - 1                   # if call doesn't have {}, set index to end of line
        line += " { input: docker = docker }"

    elif "docker" not in part.inputs.keys():    # if input not empty but no docker var: add it
        index = line.rfind('}')
        index -= (line[index - 1] == ' ')       # move one back if " }"
        line = line[:index] + ", docker = docker" + line[index:]

    else:                                       # if docker var exists, modify it
        index1 = line.find("docker") + len("docker")
        while line[index1] in " =":  # move forward until at start of assignment
            index1 += 1
        index2 = len(line) - 1  # initialize at end of line
        for c in "} ,":         # value ends in ,/ /} whichever is smallest but must > -1
            index_temp = line[index1:].find(c) + index1
            index2 = index_temp if index_temp >  index1 - 1 and index_temp < index2 else index2
        line = line[:index1] + "docker" + line[index2:]

    doc.source_lines[part.pos.line - 1] = line

# add docker to every task and workflow explicitly
def docker_runtime():
    # exit if user doesn't want to add a docker image
    if not args.docker_image:
        return

    # add image to workflow inputs
    if "docker" not in doc.workflow.inputs:
        print("append args.docker_image with docker: '~{docker}'")
    else:
        print("replace old docker with docker: '~{docker}'")

    # add image to all task calls
    for part in doc.workflow.body:      # tested - able to delegate multi- and single insert
        if isinstance(part, WDL.Tree.Call):
            line = doc.source_lines[part.pos.line - 1]
            if '{' in line and '}' not in line:
                docker_runtime_multi(part)
            else:
                docker_runtime_single(part)

    # add image to all tasks
    for task in doc.tasks:
        if "docker" not in task.inputs:
            print("add docker var to inputs")
        if "docker" not in task.runtime:
            print("add 'docker: ~{docker}'")

# pull all task variables to the workflow that calls them
def pull_to_root():
    print("placeholder")

# source .bashrc and load required modules for each task
def source_modules():
    for task in doc.tasks or []:
        for input in task.inputs or []:
            index = doc.source_lines[input.pos.line - 1].find("String modules")
            if index > -1:  # if the task does use modules
                pos = task.command.pos.line
                num_spaces = len(doc.source_lines[pos]) - len(doc.source_lines[pos].lstrip(' '))
                prepend = ' ' * num_spaces + 'source /home/ubuntu/.bashrc \n' + ' ' * num_spaces + '~{"module load " + modules + " || exit 20; "} \n\n' + ' ' * num_spaces
                doc.source_lines[pos] = prepend + doc.source_lines[pos][num_spaces:]

# find all params that need to be replaced
def test():
    print(doc.workflow.inputs)
    # if "docker" not in doc.workflow.inputs:
    #     print("append args.docker_image with docker: '~{docker}'")
    # else:
    #     print("replace old docker with docker: '~{docker}'")

# final outputs to stdout or a file with modified name
def write_out():
    name_index = args.input_wdl_path.rfind('/')
    output_path = args.input_wdl_path[:name_index + 1] + "dockstore_" + args.input_wdl_path[name_index + 1:]
    with open(output_path, "w") as output_file:
        output_file.write("\n".join(doc.source_lines))

tabs_to_spaces(8)   # tested - able to convert tabs to spaces
# docker_runtime()
    # docker_runtime_multi(part)    # tested - able to add or convert docker for multi-line call
    # docker_runtime_single(part)   # tested - able to add or convert docker for single-line call
# pull_to_root()
source_modules()  # tested - add source; module if "modules" var exists, else don't
test()
write_out()     # tested - able to write out