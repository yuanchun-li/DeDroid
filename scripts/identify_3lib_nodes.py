#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from derg import DERG, ThirdPartyLibRepo


def run(obfuscated_derg_path, new_derg_path, lib_repo_path, recover=False):
    print("Loading third party library repository %s" % lib_repo_path)
    repo = ThirdPartyLibRepo()
    repo.load(lib_repo_path)

    print("Loading input derg %s." % lib_repo_path)
    obfuscated_derg = DERG(derg_path=obfuscated_derg_path)

    print("Identifying")
    new_derg = repo.identify_3lib_packages(obfuscated_derg)

    if recover:
        print("Recovering")
        new_derg = repo.recover_derg(new_derg)

    new_derg.export(new_derg_path)
    print("Done")


def parse_args():
    """
    parse command line input
    """
    parser = argparse.ArgumentParser(
        description="identify 3rd-party lib nodes in dergs based on a library repository.")
    parser.add_argument("-obfuscated_derg", action="store", dest="obfuscated_derg",
                        required=True, help="path to the derg to recover")
    parser.add_argument("-new_derg", action="store", dest="new_derg",
                        required=True, help="path to output the recovered derg")
    parser.add_argument("-lib_repo", action="store", dest="lib_repo",
                        required=True, help="path to the third party library repository")
    parser.add_argument("-recover", action="store_true", dest="recover", default=False,
                        required=False, help="recover the third party nodes")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.obfuscated_derg, opts.new_derg, opts.lib_repo, opts.recover)
    return


if __name__ == "__main__":
    main()
