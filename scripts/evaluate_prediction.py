__author__ = 'yuanchun'

import os
import argparse
import re
import sys
import json
from mapping_convert import DetailedMapping


def run(original_derg, obfuscated_derg, proguard_mapping, infer_result, report_file):
    origin_sig_2_obfuscate_sig = {}
    origin_sig_2_origin_node = {}
    obfuscate_sig_2_obfuscate_node = {}
    obfuscate_sig_2_predicted_name = {}

    original_derg = json.load(open(original_derg))
    obfuscated_derg = json.load(open(obfuscated_derg))
    infer_result = json.load(open(infer_result))
    origin_sig_2_obfuscate_sig = DetailedMapping(proguard_mapping).origin2new

    node_id_2_predicted_name = {}
    for item in infer_result:
        if 'inf' not in item.keys():
            continue
        node_id_2_predicted_name[item['v']] = item['inf']

    for item in original_derg['nodes']:
        sig = safe_get(item, 'sig')
        if sig != "?" and sig != "" and sig in origin_sig_2_obfuscate_sig.keys():
            origin_sig_2_origin_node[sig] = item

    for item in obfuscated_derg['nodes']:
        sig = safe_get(item, 'sig')
        if sig != "?" and sig != "" and sig in origin_sig_2_obfuscate_sig.values():
            obfuscate_sig_2_obfuscate_node[sig] = item
            obfuscate_sig_2_predicted_name[sig] = node_id_2_predicted_name[item['id']]

    report_strs = []
    keys = sorted(origin_sig_2_obfuscate_sig.keys())
    total = len(keys)
    matched = 0
    for key in keys:
        origin_name = origin_sig_2_origin_node[key]['name']
        obfuscate_sig = origin_sig_2_obfuscate_sig[key]
        obfuscated_name = obfuscate_sig_2_obfuscate_node[obfuscate_sig]['name']
        predicted_name = obfuscate_sig_2_predicted_name[obfuscate_sig]
        tag = origin_sig_2_origin_node[key]['type'][0]
        if origin_name == predicted_name and origin_name != "?":
            tag = tag.upper()
            matched += 1
        else:
            tag = tag.lower()
        report_str = "[%s]%s %s/%s/%s\n" % (tag, key, origin_name, obfuscated_name, predicted_name)
        # print report_str
        report_strs.append(report_str)
    print "total: %d; matched: %d; precision: %f" % (total, matched, safe_divide(matched, total))
    report_file = open(report_file, "w")
    report_file.writelines(report_strs)
    report_file.close()


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
    parser = argparse.ArgumentParser(description="evaluate nice2predict infer result")
    parser.add_argument("--original_derg", action="store", dest="original_derg",
                        required=True, help="path to original derg.json file")
    parser.add_argument("--obfuscated_derg", action="store", dest="obfuscated_derg",
                        required=True, help="path to obfuscated derg.json file")
    parser.add_argument("--mapping", action="store", dest="proguard_mapping",
                        required=True, help="path to proguard mapping file")
    parser.add_argument("--infer", action="store", dest="infer_result",
                        required=True, help="path to nice2predict inferrd result")
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
    run(opts.original_derg, opts.obfuscated_derg, opts.proguard_mapping, opts.infer_result, opts.report_file)

    return


if __name__ == "__main__":
    main()
