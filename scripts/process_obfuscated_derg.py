import argparse
import os
import json

import utils


def run(mapping_file, obfuscated_derg, new_derg):
    """

    :param mapping_file:
    :param obfuscated_derg:
    :param new_derg
    """

    mapping_file = os.path.abspath(mapping_file)
    obfuscated_derg = os.path.abspath(obfuscated_derg)

    proguard = utils.IdentifierMapping(mapping_file=mapping_file)
    obfuscated_derg_file = open(obfuscated_derg, 'r')
    derg = json.load(obfuscated_derg_file)
    obfuscated_derg_file.close()

    for node in derg['nodes']:
        node_type = node['type']
        if node_type.endswith('_LIB'):
            continue
        if node_type.startswith('package') \
                or node_type.startswith('class') \
                or node_type.startswith('method') \
                or node_type.startswith('field'):
            node_unique_id = utils.convert_soot_sig_to_unique_id(node['sig'], node_type)
            if node_unique_id in proguard.mapping:
                original_name = proguard.mapping[node_unique_id]
            else:
                original_name = node['name']
            node['original_name'] = original_name

    new_derg_file = open(new_derg, 'w')
    json.dump(derg, new_derg_file, indent=2)
    new_derg_file.close()


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(
        description="add the original name (ground truth) of each node in the obfuscated derg")
    parser.add_argument("-mapping", action="store", dest="mapping_file",
                        required=True, help="path to proguard-generated mapping.txt")
    parser.add_argument("-obfuscated_derg", action="store", dest="obfuscated_derg",
                        required=True, help="path to the obfuscated derg")
    parser.add_argument("-new_derg", action="store", dest="new_derg",
                        required=True, help="path to the new derg with original names")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.mapping_file, opts.obfuscated_derg, opts.new_derg)

    return


if __name__ == "__main__":
    main()
