import os
import argparse
import sys

import utils

DEFAULT_REPORT_NAME = "deguard_recover_report.txt"


def run(mapping_file, recovered_derg, deguard_mapping_file, match_mode, report_dir, report_name):

    """

    :param mapping_file:
    :param recovered_derg:
    :param report_dir:
    """

    mapping_file = os.path.abspath(mapping_file)
    recovered_derg = os.path.abspath(recovered_derg)
    report_dir = os.path.abspath(report_dir)

    proguard = utils.IdentifierMapping(mapping_file=mapping_file)
    # proguard.dump_report(report_dir + "/minify_result.txt")

    recover = utils.IdentifierMapping(recovered_derg=recovered_derg)
    third_party_sigs = recover.sigs_3lib
    # recover.dump_report(report_dir + "/recover_result.txt")

    if deguard_mapping_file is not None:
        deguard_mapping_file = os.path.abspath(deguard_mapping_file)
        deguard = utils.IdentifierMapping(de_mapping_file=deguard_mapping_file)
        # deguard.update(recover)
        recover = deguard

    utils.dump_statistics(proguard, recover, sys.stdout)
    compare_report = open(os.path.join(report_dir, report_name), "w")
    utils.dump_report(proguard, recover, match_mode, third_party_sigs, compare_report)


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(description="evaluate the recovered derg by comparing with ground truth mapping file")
    parser.add_argument("-mapping", action="store", dest="mapping_file",
                        required=True, help="path to proguard-generated mapping.txt")
    parser.add_argument("-recovered_derg", action="store", dest="recovered_derg",
                        required=True, help="path to recovered derg")
    parser.add_argument("-deguard_mapping", action="store", dest="deguard_mapping_file",
                        help="path to deguard-generated mapping.txt")
    parser.add_argument("-o", action="store", dest="report_dir",
                        default=".", help="directory of report files")
    parser.add_argument("-report_name", action="store", dest="report_name",
                        default=DEFAULT_REPORT_NAME, help="name of report file")
    parser.add_argument("-match_mode", action="store", dest="match_mode",
                        default=utils.MATCH_MODE_EXACT, help="match mode")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.mapping_file, opts.recovered_derg, opts.deguard_mapping_file, opts.match_mode, opts.report_dir, opts.report_name)

    return


if __name__ == "__main__":
    main()
