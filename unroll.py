#!/usr/bin/python3

import bashparse

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from logging import debug, info, warning, error, critical
import logging
import sys

def parse_args():
        parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                                description=__doc__,
                                epilog="Exmaple Usage: ")

        parser.add_argument("--log-level", "--ll", default="info",
                            help="Define the logging verbosity level (debug, info, warning, error, fotal, critical).")

        parser.add_argument("input_file", type=FileType('r'),
                            nargs='?', default=sys.stdin,
                            help="")

        parser.add_argument("output_file", type=FileType('w'),
                            nargs='?', default=sys.stdout,
                            help="")

        args = parser.parse_args()
        log_level = args.log_level.upper()
        logging.basicConfig(level=log_level,
                            format="%(levelname)-10s:\t%(message)s")
        return args


def basic_node_unroll(nodes, function_dict = {},
                      command_alias_list={}, output_stream=sys.stdout):
	# Command substitutions are gonna be weird
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes: 
		if type(node) is not bashparse.node: raise ValueError('nodes must be of type bashparse.node')
	unrolled_nodes = []

	for node in nodes: 
		if node.kind == 'compound':
			unrolled_nodes += basic_node_unroll(node.list, function_dict, command_alias_list, output_stream=output_stream)
		elif node.kind == 'for':
			output_stream.write('for node: ' + str(node) + "\n")
			if len(node.parts) > 4:
				command_nodes = bashparse.return_paths_to_node_type(node.parts[4:], 'command')
				for command in command_nodes:
					unrolled_nodes += basic_node_unroll(command.node, function_dict, command_alias_list, output_stream=output_stream)
		elif node.kind == 'if':
			unrolled_nodes += [ node ]
		elif node.kind == 'command':
			command_alias_list = bashparse.return_command_aliasing(node, command_alias_list)
			node = bashparse.replace_command_aliasing(node, command_alias_list)
			node = bashparse.replace_functions(node, function_dict)
			for itr in node:
				if itr.kind == 'compound': # ie function replacement happened
					unrolled_nodes += basic_node_unroll(itr.list, function_dict, command_alias_list, output_stream=output_stream)
				else:
					unrolled_nodes += [ itr ]
		elif node.kind == 'function':
			function_dict = bashparse.build_function_dictionary(node, function_dict)
		elif hasattr(node, 'parts'):
			unrolled_nodes += basic_node_unroll(node.parts)
		elif hasattr(node, 'list'):
			unrolled_nodes += basic_node_unroll(node.list)
	return unrolled_nodes

def main():
        args = parse_args()
        
        text = args.input_file.read()
        
        nodes = bashparse.parse(text)
        
        var_list = {}
        replaced_nodes = bashparse.substitute_variables(nodes, var_list)
        
        unrolled_nodes = basic_node_unroll(replaced_nodes,
                                           output_stream=args.output_file)
        
        args.output_file.write('unrolled nodes: ')
        for ast in unrolled_nodes:
	            args.output_file.write(ast.dump() + "\n")


if __name__ == "__main__":
        main()


