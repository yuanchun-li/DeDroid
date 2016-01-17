__author__ = 'yuanchun'

import os
import argparse
import re
import sys
import json


def run(request_json_file, result_json_file, report_file):

    """

    :param request_json_file:
    :param result_json_file:
    :param report_file:
    """
    request = open(request_json_file)
    result = open(result_json_file)
    report = open(report_file, "w")

    request_list = json.load(request)['assign']
    result_list = json.load(result)

    # print request_list
    # print result_list

    request_dict = list2dict(request_list)
    result_dict = list2dict(result_list)

    # print result_dict

    report_dict = compare_dict(request_dict, result_dict)
    json.dump(report_dict, report)

    request.close()
    result.close()
    report.close()


def list2dict(infer_list):
    infer_dict = {}
    for item in infer_list:
        if 'v' in item.keys() and 'inf' in item.keys():
            infer_dict[item['v']] = item['inf']
    return infer_dict


def compare_dict(request_dict, result_dict):
    report_dict = {}
    keys = sorted(set(request_dict.keys() + result_dict.keys()))
    total = len(keys)
    matched = 0
    for key in keys:
        request_value = safe_get(request_dict, key)
        result_value = safe_get(result_dict, key)
        if request_value == result_value and result_value != "?":
            tag = "Y"
            matched += 1
        else:
            tag = "N"
        report_str = "[%s]%s/%s" % (tag, request_value, result_value)
        # print report_str
        report_dict[key] = report_str
    print "total: %d; matched: %d; precision: %f" % (total, matched, safe_divide(matched, total))
    return report_dict

def safe_get(data_dict, key):
    if key in data_dict.keys():
        return data_dict[key]
    return "?"

def safe_divide(a, b):
    if b <= 0:
        return 1
    return float(a) / b

def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(description="compare nice2predict infer result with the infer request")
    parser.add_argument("--request", action="store", dest="request_json_file",
                        required=True, help="path to nice2predict request json file")
    parser.add_argument("--result", action="store", dest="result_json_file",
                        required=True, help="path to nice2predict prediction result")
    parser.add_argument("-o", action="store", dest="report_file",
                        required=True, help="directory of report file")

    options = parser.parse_args()
    # print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.request_json_file, opts.result_json_file, opts.report_file)

    return


if __name__ == "__main__":
    main()
