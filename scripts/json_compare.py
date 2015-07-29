__author__ = 'liyc'

import json, argparse

def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(description="compare two json files.")
    parser.add_argument("json1", help="json file 1")
    parser.add_argument("json2", help="json file 2")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    json_file_1 = open(opts.json1)
    json_file_2 = open(opts.json2)

    json_dict_1 = json.loads(json_file_1.read())
    json_dict_2 = json.loads(json_file_2.read())

    if json_dict_1 == json_dict_2:
        print "Same!"
    else:
        print "Different!"

    return


if __name__ == "__main__":
    main()
