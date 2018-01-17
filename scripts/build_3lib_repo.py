#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

import utils
from derg import ThirdPartyLibRepo


def run(dergs_dir, output_path, derg_name, min_freq):
    dergs = utils.load_dergs(dergs_dir, derg_name)
    print("Finish loading dergs.")
    repo = ThirdPartyLibRepo()
    repo.collect_from_dergs(dergs, min_freq)
    repo.export(output_path)


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(
        description="collect third party library dergs from dergs in a directory.")
    parser.add_argument("-dergs_dir", action="store", dest="dergs_dir",
                        required=True, help="path to the dir of input dergs")
    parser.add_argument("-output_path", action="store", dest="output_path",
                        required=True, help="path to a file where the third party library repository will be stored")
    parser.add_argument("-derg_name", action="store", dest="derg_name", default="derg.json",
                        required=False, help="the name of input derg")
    parser.add_argument("-min_freq", action="store", dest="min_freq", default=2,
                        required=False, help="minimum frequency of package to be considered as a third party library")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.dergs_dir, opts.output_path, opts.derg_name, int(opts.min_freq))

    return


if __name__ == "__main__":
    main()
