#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

import utils
from derg import KnowledgeGraph


def run(dergs_dir, output_dir, derg_name, include_3lib):
    dergs = utils.load_dergs(dergs_dir, derg_name)
    kg = KnowledgeGraph(dergs, include_3lib)
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
    parser.add_argument("-include_3lib", action="store_true", dest="include_3lib", default=False,
                        required=False, help="whether the knowledge includes third party library nodes")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.dergs_dir, opts.output_dir, opts.derg_name, opts.include_3lib)

    return


if __name__ == "__main__":
    main()
