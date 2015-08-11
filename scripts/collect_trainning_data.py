__author__ = 'yuanchun'
import argparse
import sys
import re


def run(mapping_file, apks_file, out_file=None, start_id=None):
    if out_file is None:
        out_file = sys.stdout
    else:
        out_file = open(out_file, "w")

    if start_id is None:
        start_id = 0
    else:
        start_id = int(start_id)

    mappings = read_mappings(mapping_file)
    apk_debugs, apk_releases = read_apks(apks_file)

    mapping_apk_dict = {}

    for key1 in mappings.keys():
        for key2 in mappings[key1].keys():
            mapping = mappings[key1][key2]
            if key1 not in apk_debugs.keys() or key1 not in apk_releases.keys():
                print "Cannot match: " + mapping
                continue

            debug_matched = False
            if len(apk_debugs[key1].keys()) == 1:
                k2 = apk_debugs[key1].keys()[0]
                safe_put_with_check(mapping_apk_dict, mapping, "debug", apk_debugs[key1][k2])
                debug_matched = True
            elif key2 in apk_debugs[key1].keys():
                safe_put_with_check(mapping_apk_dict, mapping, "debug", apk_debugs[key1][key2])
                debug_matched = True
            else:
                key2 = generalized(key2)
                for k2 in apk_debugs[key1].keys():
                    if key2 in generalized(k2):
                        safe_put_with_check(mapping_apk_dict, mapping, "debug", apk_debugs[key1][k2])
                        debug_matched = True
                        break

            release_matched = False
            if len(apk_releases[key1].keys()) == 1:
                k2 = apk_releases[key1].keys()[0]
                safe_put_with_check(mapping_apk_dict, mapping, "release", apk_releases[key1][k2])
                release_matched = True
            elif key2 in apk_releases[key1].keys():
                safe_put_with_check(mapping_apk_dict, mapping, "release", apk_releases[key1][key2])
                release_matched = True
            else:
                key2 = generalized(key2)
                for k2 in apk_releases[key1].keys():
                    if key2 in generalized(k2):
                        safe_put_with_check(mapping_apk_dict, mapping, "release", apk_releases[key1][k2])
                        release_matched = True
                        break

            if debug_matched and release_matched:
                continue

            print "[key1] %s, [key2] %s" % (key1, key2)
            print apk_debugs[key1].keys()
            print apk_releases[key1].keys()

    for key in mapping_apk_dict.keys():
        out_file.write("mkdir ./%d\n" % start_id)
        out_file.write("cp %s ./%d/mapping.txt\n" % (key.strip(), start_id))
        out_file.write("cp %s ./%d/app-debug.apk\n" % (mapping_apk_dict[key]["debug"].strip(), start_id))
        out_file.write("cp %s ./%d/app-release.apk\n" % (mapping_apk_dict[key]["release"].strip(), start_id))
        out_file.write("echo %s >> ./%d/app_path.txt\n" % (key.strip(), start_id))
        out_file.write("echo %s >> ./%d/app_path.txt\n" % (mapping_apk_dict[key]["debug"].strip(), start_id))
        out_file.write("echo %s >> ./%d/app_path.txt\n" % (mapping_apk_dict[key]["release"].strip(), start_id))

        start_id += 1


def generalized(str):
    return ''.join(c for c in str.lower() if c.isalnum())


def read_mappings(mapping_file):
    mapping_file_f = open(mapping_file)
    mappings = mapping_file_f.readlines()

    gradle_mapping_RE = re.compile('^(.*)\/build\/outputs\/mapping(.*)\/release\/mapping.txt$')
    ant_mapping_RE = re.compile('^(.*)\/bin\/proguard\/mapping.txt$')

    mapping_dict = {}

    for mapping in mappings:
        gradle_match = gradle_mapping_RE.match(mapping)
        if gradle_match:
            key1 = gradle_match.group(1)
            key2 = gradle_match.group(2)
            safe_put_with_check(mapping_dict, key1, key2, mapping)
            continue

        ant_match = ant_mapping_RE.match(mapping)
        if ant_match:
            key1 = ant_match.group(1)
            key2 = ""
            safe_put_with_check(mapping_dict, key1, key2, mapping)
            continue

        print "Unrecognized mapping: " + mapping
    return mapping_dict


def read_apks(apks_file):
    apks_file_f = open(apks_file)
    apks = apks_file_f.readlines()

    unaligned_apk_RE = re.compile('^.*unaligned.apk$')
    gradle_apk_debug_RE = re.compile('^(.*)\/build\/outputs\/apk\/(.*)-debug.apk$')
    gradle_apk_release_RE = re.compile('^(.*)\/build\/outputs\/apk\/(.*)-release(-unsigned)?.apk$')
    ant_apk_debug_RE = re.compile('^(.*)\/bin\/.*\-debug.apk$')
    ant_apk_release_RE = re.compile('^(.*)\/bin\/.*\-release(\-unsigned)?.apk$')

    apk_debug_dict = {}
    apk_release_dict = {}

    for apk in apks:
        unaligned_match = unaligned_apk_RE.match(apk)
        if unaligned_match:
            continue

        gradle_debug_match = gradle_apk_debug_RE.match(apk)
        if gradle_debug_match:
            key1 = gradle_debug_match.group(1)
            key2 = gradle_debug_match.group(2)
            safe_put_with_check(apk_debug_dict, key1, key2, apk)
            continue

        gradle_release_match = gradle_apk_release_RE.match(apk)
        if gradle_release_match:
            key1 = gradle_release_match.group(1)
            key2 = gradle_release_match.group(2)
            safe_put_with_check(apk_release_dict, key1, key2, apk)
            continue

        ant_debug_match = ant_apk_debug_RE.match(apk)
        if ant_debug_match:
            key1 = ant_debug_match.group(1)
            key2 = ""
            safe_put_with_check(apk_debug_dict, key1, key2, apk)
            continue

        ant_release_match = ant_apk_release_RE.match(apk)
        if ant_release_match:
            key1 = ant_release_match.group(1)
            key2 = ""
            safe_put_with_check(apk_release_dict, key1, key2, apk)
            continue

        print "Unrecognized apk: " + apk
    return apk_debug_dict, apk_release_dict


def safe_put_with_check(data_dict, key1, key2, value):
    assert isinstance(data_dict, dict)
    if key1 not in data_dict.keys():
        data_dict[key1] = {}
    assert key2 not in data_dict[key1].keys()
    data_dict[key1][key2] = value


def safe_get(data_dict, key1, key2):
    assert isinstance(data_dict, dict)
    if key1 in data_dict.keys():
        if key2 in data_dict[key1].keys():
            return data_dict[key1][key2]
    return None


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(description="comparing proguard-generated and predict mappings")
    parser.add_argument("--mappings", action="store", dest="mappings_file",
                        required=True, help="a file containing a list of mapping.txt paths")
    parser.add_argument("--apks", action="store", dest="apks_file",
                        required=True, help="a file containing a list of apk files")
    parser.add_argument("-o", action="store", dest="out_file", help="output file")
    parser.add_argument("-i", action="store", dest="start_id", help="start id")

    options = parser.parse_args()
    # print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.mappings_file, opts.apks_file, opts.out_file, opts.start_id)

    return


if __name__ == "__main__":
    main()
