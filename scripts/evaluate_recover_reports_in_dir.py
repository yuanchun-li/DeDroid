import subprocess, os, argparse

DEFAULT_REPORT_NAME = "recover_report.txt"
ROWS = ['p', 'P', 'c', 'C', 'f', 'F', 'm', 'M']
TAG_3LIB = '(3LIB)'
TAG_NICE = '(nice)'
COLS = [TAG_3LIB, TAG_NICE, '']

ELEMENT_TYPES = ['p', 'c', 'm', 'f']
LIB_TYPES = ['lib', 'nonlib']
COUNT_TYPES = ['tp', 'recovered', 'minified']


def evaluate_recover_reports_under_dir(working_dir, report_name):
    working_dir = os.path.abspath(working_dir)

    results = init_results()
    for root, dirs, files in os.walk(working_dir):
        for file_name in files:
            if file_name == report_name:
                report_path = os.path.join(root, file_name)
                report = RecoverReport(report_path)
                results = add_results(results, report.results)

    print gen_lib_portion_table(results)
    print gen_precision_table(results)


def gen_raw_table(result):
    table_str = "\nraw_data:\n"
    th = ['type'] + COLS
    th[-1] = "total"
    table_str += segs_to_table_line(th)
    for row in ROWS:
        tr = [row]
        for col in COLS:
            tr.append(str(result[row][col]))
        table_str += segs_to_table_line(tr)

    return table_str


def gen_lib_portion_table(result):
    table_str = "\n3rd-party library identification:\n"
    th = ['type'] + LIB_TYPES
    th.append('overall')
    table_str += segs_to_table_line(th)

    overall_count_lib = 0
    overall_count_nonlib = 0

    for element_type in ELEMENT_TYPES:
        count_lib = result[element_type]['lib']['minified']
        count_nonlib = result[element_type]['nonlib']['minified']
        overall_count_lib += count_lib
        overall_count_nonlib += count_nonlib

        count_overall = count_lib + count_nonlib
        portion_3lib = calculate_percent(count_lib, count_overall)
        portion_nice = calculate_percent(count_nonlib, count_overall)

        tr = [element_type, portion_3lib, portion_nice, str(count_overall)]
        table_str += segs_to_table_line(tr)

    overall_count_overall = overall_count_lib + overall_count_nonlib
    overall_portion_lib = calculate_percent(overall_count_lib, overall_count_overall)
    overall_portion_nonlib = calculate_percent(overall_count_nonlib, overall_count_overall)
    tr = ['overall', overall_portion_lib, overall_portion_nonlib, str(overall_count_overall)]
    table_str += segs_to_table_line(tr)

    return table_str


def gen_precision_table(result):
    table_str = "\nrecovering accuracy:\n"
    th = ['type'] + LIB_TYPES
    th.append('overall')
    table_str += segs_to_table_line(th)

    overall_lib_tp = 0
    overall_lib_minified = 0
    overall_lib_recovered = 0
    overall_nonlib_tp = 0
    overall_nonlib_minified = 0
    overall_nonlib_recovered = 0
    overall_tp = 0
    overall_minified = 0
    overall_recovered = 0

    for element_type in ELEMENT_TYPES:
        lib_tp = result[element_type]['lib']['tp']
        lib_minified = result[element_type]['lib']['minified']
        lib_recovered = result[element_type]['lib']['recovered']
        lib_precision = calculate_percent(lib_tp, lib_recovered)
        lib_recall = calculate_percent(lib_tp, lib_minified)

        nonlib_tp = result[element_type]['nonlib']['tp']
        nonlib_minified = result[element_type]['nonlib']['minified']
        nonlib_recovered = result[element_type]['nonlib']['recovered']
        nonlib_precision = calculate_percent(nonlib_tp, nonlib_recovered)
        nonlib_recall = calculate_percent(nonlib_tp, nonlib_minified)

        tp = lib_tp + nonlib_tp
        minified = lib_minified + nonlib_minified
        recovered = lib_recovered + nonlib_recovered
        precision = calculate_percent(tp, recovered)
        recall = calculate_percent(tp, minified)

        tr = [element_type,
              "%s, %s" % (lib_precision, lib_recall),
              "%s, %s" % (nonlib_precision, nonlib_recall),
              "%s, %s" % (precision, recall)]
        table_str += segs_to_table_line(tr)

        overall_lib_tp += lib_tp
        overall_lib_minified += lib_minified
        overall_lib_recovered += lib_recovered
        overall_nonlib_tp += nonlib_tp
        overall_nonlib_minified += nonlib_minified
        overall_nonlib_recovered += nonlib_recovered
        overall_tp += tp
        overall_minified += minified
        overall_recovered += recovered

    overall_lib_precision = calculate_percent(overall_lib_tp, overall_lib_recovered)
    overall_lib_recall = calculate_percent(overall_lib_tp, overall_lib_minified)
    overall_nonlib_precision = calculate_percent(overall_nonlib_tp, overall_nonlib_recovered)
    overall_nonlib_recall = calculate_percent(overall_nonlib_tp, overall_nonlib_minified)
    overall_precision = calculate_percent(overall_tp, overall_recovered)
    overall_recall = calculate_percent(overall_tp, overall_minified)
    tr = ["overall",
          "%s, %s" % (overall_lib_precision, overall_lib_recall),
          "%s, %s" % (overall_nonlib_precision, overall_nonlib_recall),
          "%s, %s" % (overall_precision, overall_recall)]
    table_str += segs_to_table_line(tr)

    return table_str


def segs_to_table_line(segs):
    fixed_len_segs = [seg.rjust(10) for seg in segs]
    return "\t".join(fixed_len_segs) + "\n"


def get_count(working_dir, report_name, regex):
    # cmd_args = ["find %s -name %s | xargs cat | grep \"%s\" | wc -l" % (working_dir, REPORT_NAME, regex)]
    print "get_count(working_dir='%s', report_name='%s', regex='%s')" % (working_dir, report_name, regex)
    find_cmd_args = ['find', working_dir, '-name', report_name]
    find_process = subprocess.Popen(find_cmd_args, stdout=subprocess.PIPE)
    cat_cmd_args = ['xargs', 'cat']
    cat_process = subprocess.Popen(cat_cmd_args, stdin=find_process.stdout, stdout=subprocess.PIPE)
    grep_cmd_args = ['grep', regex]
    grep_process = subprocess.Popen(grep_cmd_args, stdin=cat_process.stdout, stdout=subprocess.PIPE)
    wc_cmd_args = ['wc', '-l']
    output = subprocess.check_output(wc_cmd_args, stdin=grep_process.stdout)
    print "result: %s" % output
    return int(output)


def calculate_percent(a, b):
    if b == 0:
        return "-"
    else:
        return "%.2f%%" % (a * 100.0 / b)


def safe_divide(a, b):
    if b <= 0:
        return 1
    return float(a) / b


def init_results():
    results = {}
    for element_type in ELEMENT_TYPES:
        results[element_type] = {}
        for lib_type in LIB_TYPES:
            results[element_type][lib_type] = {}
            for count_type in COUNT_TYPES:
                results[element_type][lib_type][count_type] = 0
    return results


def add_results(results1, results2):
    results = {}
    for element_type in ELEMENT_TYPES:
        results[element_type] = {}
        for lib_type in LIB_TYPES:
            results[element_type][lib_type] = {}
            for count_type in COUNT_TYPES:
                results[element_type][lib_type][count_type] = results1[element_type][lib_type][count_type] + results2[element_type][lib_type][count_type]
    return results


class RecoverReport(object):
    def __init__(self, report_path):
        print("processing " + report_path)
        self.results = self.parse_report(report_path)

    def parse_report(self, report_path):
        report_lines = open(report_path).readlines()
        results = init_results()

        lib_packages = set()
        for line in report_lines:
            segs = line.split()
            if len(segs) != 3 or len(segs[0]) != 9:
                continue
            if segs[0] == "[p](3LIB)":
                lib_packages.add(segs[1])
            elif segs[0] == "[c](3LIB)":
                lib_packages.add(segs[1][:segs[1].rfind('.')])

        for line in report_lines:
            segs = line.split()
            if len(segs) != 3 or len(segs[0]) != 9:
                continue
            t = segs[0][1]
            element_type = t.lower()
            if element_type == 'p':
                package = segs[1]
                is_lib = True if package in lib_packages else False
            elif element_type == 'c':
                package = segs[1][:segs[1].rfind('.')]
                is_lib = True if package in lib_packages else False
            else:
                class_name = segs[1][:segs[1].rfind(';->')]
                package = class_name[:class_name.rfind('.')]
                is_lib = True if package in lib_packages else False
            lib_type = "lib" if is_lib else "nonlib"

            is_tp = True if t.islower() else False
            is_minified = not segs[2].startswith("?/")
            is_recovered = not segs[2].endswith("/?")
            if is_tp:
                results[element_type][lib_type]['tp'] += 1
            if is_minified:
                results[element_type][lib_type]['minified'] += 1
            if is_recovered:
                results[element_type][lib_type]['recovered'] += 1

        return results


def parse_args():
    """
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
    parser = argparse.ArgumentParser(description="evaluate all of the mapping reports under a directory")
    parser.add_argument("-d", action="store", dest="working_dir",
                        required=True, help="path to directory containing all mapping reports")
    parser.add_argument("-report_name", action="store", dest="report_name",
                        default=DEFAULT_REPORT_NAME, help="name of report file")

    options = parser.parse_args()
    # print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()
    evaluate_recover_reports_under_dir(opts.working_dir, opts.report_name)

    return


if __name__ == "__main__":
    main()
