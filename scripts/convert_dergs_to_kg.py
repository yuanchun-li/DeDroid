#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

import utils
from derg import KnowledgeGraph


def run(dergs_dir, output_dir, derg_name):
    dergs = utils.load_dergs(dergs_dir, derg_name)
    kg = KnowledgeGraph(dergs)
    kg.output(output_dir)


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(
        description="covert the dergs in a directory to a knowledge graph.")
    parser.add_argument("-dergs_dir", action="store", dest="dergs_dir",
                        required=True, help="path to the dir of dergs")
    parser.add_argument("-output_dir", action="store", dest="output_dir",
                        required=True, help="path to output dir")
    parser.add_argument("-derg_name", action="store", dest="derg_name", default="derg.json",
                        required=False, help="the name of derg")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.dergs_dir, opts.output_dir, opts.derg_name)

    return


if __name__ == "__main__":
    main()
