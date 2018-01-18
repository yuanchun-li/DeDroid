#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from derg import DERG, ThirdPartyLibRepo
import utils


def run(dergs_dir, derg_name, lib_repo_path, recover=False, output_suffix=""):
    print("Loading third party library repository %s ..." % lib_repo_path)
    repo = ThirdPartyLibRepo()
    repo.load(lib_repo_path)

    print("Loading dergs %s %s ..." % (dergs_dir, derg_name))
    dergs = utils.load_dergs(dergs_dir, derg_name)

    print("Identifying ...")
    for derg in dergs:
        print("- identifying %s" % derg.derg_path)
        repo.identify_3lib_packages(derg)

    if recover:
        print("Recovering")
        for derg in dergs:
            print("- recovering %s" % derg.derg_path)
            repo.recover_derg(derg)

    print("Outputting ...")
    for derg in dergs:
        derg.export(derg.derg_path + output_suffix)

    print("Done")


def parse_args():
    """
    parse command line input
    """
    parser = argparse.ArgumentParser(
        description="identify 3rd-party lib nodes in dergs based on a library repository.")
    parser.add_argument("-dergs_dir", action="store", dest="dergs_dir",
                        required=True, help="path to the dir of the dergs")
    parser.add_argument("-derg_name", action="store", dest="derg_name",
                        required=True, help="the file name of the dergs")
    parser.add_argument("-lib_repo", action="store", dest="lib_repo",
                        required=True, help="path to the third party library repository")
    parser.add_argument("-recover", action="store_true", dest="recover", default=False,
                        required=False, help="whether to recover the third party nodes using graph matching.")
    parser.add_argument("-output_suffix", action="store", dest="output_suffix", default="",
                        required=False, help="the suffix added to the new derg file. "
                                             "default will overwrite the original file.")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.dergs_dir, opts.derg_name, opts.lib_repo, opts.recover, opts.output_suffix)
    return


if __name__ == "__main__":
    main()
