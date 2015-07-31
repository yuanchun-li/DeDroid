__author__ = 'yuanchun'

import os
import argparse
import re


RE_CLASS_LINE = re.compile('([^\ ]+) -> ([^\ ]+):\n')
RE_METHOD_LINE = re.compile('([^\ ]+)\ ([^\ ]+)\((.*)\) -> ([^\ ]+)\n')
RE_FIELD_LINE = re.compile('([^\ ]+)\ ([^\ \)]+) -> ([^\ ]+)\n')


class ObfuscationMapping(object):
    """
    describe a mapping.txt generated by proguard or UnuglifyDEX
    """
    def __init__(self, mapping_file):
        self.lines = open(mapping_file).readlines()
        self.package_mapping = {}
        self.class_mapping = {}
        self.class_origin2obfus = {}
        self._build_package_class_mapping()
        self.field_mapping = {}
        self.method_mapping = {}
        self._build_field_method_mapping()
        self.mapping = {}
        self.mapping.update(self.package_mapping)
        self.mapping.update(self.class_mapping)
        self.mapping.update(self.field_mapping)
        self.mapping.update(self.method_mapping)

    def dump(self, out_file):
        for key in sorted(self.mapping):
            out_file.write("%s -> %s\n" % (key, self.mapping[key]))

    def get_all_lines(self):
        all_lines = set()
        for key in self.mapping.keys():
            all_lines.add("%s -> %s\n" % (key, self.mapping[key]))
        return all_lines

    def _build_package_class_mapping(self):
        for line in self.lines:
            m = RE_CLASS_LINE.search(line)
            if not m:
                continue
            class_origin, class_obfus = m.group(1), m.group(2)
            package_origin, package_obfus = \
                ".".join(class_origin.split('.')[:-1]), ".".join(class_obfus.split('.')[:-1])
            self._add_class_map(class_origin, class_obfus)
            self._add_package_map(package_origin, package_obfus)

    def _build_field_method_mapping(self):
        current_cls_id = None
        for line in self.lines:
            m = RE_CLASS_LINE.search(line)
            if m:
                current_cls_id = m.group(2)
                continue
            m = RE_FIELD_LINE.search(line)
            if m:
                assert current_cls_id is not None
                field_type, origin_name, obfus_name = \
                    m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                if origin_name == obfus_name:
                    continue
                field_id = self._get_unique_field_id(current_cls_id, obfus_name, field_type)
                assert field_id not in self.field_mapping.keys()
                self.field_mapping[field_id] = origin_name
                continue
            m = RE_METHOD_LINE.search(line)
            if m:
                assert current_cls_id is not None
                ret_type, origin_name, param_types, obfus_name = \
                    m.group(1).strip(), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
                if origin_name == obfus_name:
                    continue
                method_id = self._get_unique_method_id(current_cls_id, obfus_name, param_types)
                assert method_id not in self.method_mapping.keys()
                self.method_mapping[method_id] = origin_name

    def _add_class_map(self, class_origin, class_obfus):
        if class_origin == class_obfus:
            return
        self.class_mapping[class_obfus] = class_origin.split('.')[-1]
        self.class_origin2obfus[class_origin] = class_obfus

    def _add_package_map(self, package_origin, package_obfus):
        if package_origin == package_obfus:
            return
        self.package_mapping[package_obfus] = package_origin.split('.')[-1]

    def _get_unique_field_id(self, class_id, field_name, field_type):
        type_id = self._get_unique_class_id(field_type)
        return "%s;->%s:%s" % (class_id, field_name, type_id)

    def _get_unique_method_id(self, class_id, method_name, param_types):
        param_ids = []
        for param_type in param_types.split(','):
            param_ids.append(self._get_unique_class_id(param_type))
        return "%s;->%s(%s)" % (class_id, method_name, ",".join(param_ids))

    def _get_unique_class_id(self, class_name):
        if class_name in self.class_origin2obfus.keys():
            return self.class_origin2obfus[class_name]
        else:
            return class_name


def run(proguard_mapping_file, predict_mapping_file, report_dir):

    """

    :param proguard_mapping_file:
    :param predict_mapping_file:
    :param report_dir:
    """

    proguard_mapping_file = os.path.abspath(proguard_mapping_file)
    predict_mapping_file = os.path.abspath(predict_mapping_file)
    report_dir = os.path.abspath(report_dir)

    proguard_mapping = ObfuscationMapping(proguard_mapping_file)
    proguard_mapping_report = open(os.path.join(report_dir, "proguard_result.txt"), "w")
    proguard_mapping.dump(proguard_mapping_report)
    proguard_mapping_report.close()
    proguard_mapping_set = proguard_mapping.get_all_lines()

    predict_mapping = ObfuscationMapping(predict_mapping_file)
    predict_mapping_report = open(os.path.join(report_dir, "predict_result.txt"), "w")
    predict_mapping.dump(predict_mapping_report)
    predict_mapping_report.close()
    predict_mapping_set = predict_mapping.get_all_lines()

    true_positives = proguard_mapping_set & predict_mapping_set

    print 'Proguard obfuscated %d items, UnuglifyDEX deobfuscated %d items.\n' \
          'TP: %d, precision: %f, recall: %f\n' % \
          (len(proguard_mapping_set), len(predict_mapping_set), len(true_positives),
           safe_devide(len(true_positives), len(predict_mapping_set)),
           safe_devide(len(true_positives), len(proguard_mapping_set)))


def safe_devide(a, b):
    if b <= 0:
        return 1
    return float(a) / b


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(description="comparing proguard-generated and predict mappings")
    parser.add_argument("--proguard", action="store", dest="proguard_mappings_dir",
                        required=True, help="directory of proguard-generated mappings file")
    parser.add_argument("--predict", action="store", dest="predict_mappings_dir",
                        required=True, help="directory of predict mappings file")
    parser.add_argument("-o", action="store", dest="report_path",
                        required=True, help="directory of report file")

    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    run(opts.proguard_mappings_dir, opts.predict_mappings_dir, opts.report_path)

    return


if __name__ == "__main__":
    main()