import subprocess, os, argparse

DEFAULT_REPORT_NAME = "recover_report.txt"
ROWS = ['p', 'P', 'c', 'C', 'f', 'F', 'm', 'M']
TAG_3LIB = '(3LIB)'
TAG_NICE = '(degd)'
COLS = [TAG_3LIB, TAG_NICE, '']


def evaluate_recover_reports_under_dir(working_dir, report_name):
    working_dir = os.path.abspath(working_dir)

    result = {}
    for row in ROWS:
        result[row] = {}
        for col in COLS:
            regex = '^\[%s\]%s' % (row, col)
            count = get_count(working_dir, report_name, regex)
            result[row][col] = count

    print gen_raw_table(result)
    print gen_3LIB_identification_table(result)
    print gen_precision_table(result)


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


def gen_3LIB_identification_table(result):
    table_str = "\n3rd-party library identification:\n"
    th = ['type'] + COLS
    th[-1] = "overall"
    table_str += segs_to_table_line(th)

    overall_count_3lib = 0
    overall_count_nice = 0

    for row in ROWS:
        if row.islower():
            continue

        row_lower = row.lower()
        count_3lib = result[row][TAG_3LIB] + result[row_lower][TAG_3LIB]
        count_nice = result[row][TAG_NICE] + result[row_lower][TAG_NICE]
        overall_count_3lib += count_3lib
        overall_count_nice += count_nice

        count_overall = count_3lib + count_nice
        portion_3lib = calculate_percent(count_3lib, count_overall)
        portion_nice = calculate_percent(count_nice, count_overall)

        tr = [row, portion_3lib, portion_nice, str(count_overall)]
        table_str += segs_to_table_line(tr)

    overall_count_overall = overall_count_3lib + overall_count_nice
    overall_portion_3lib = calculate_percent(overall_count_3lib, overall_count_overall)
    overall_portion_nice = calculate_percent(overall_count_nice, overall_count_overall)
    tr = ['overall', overall_portion_3lib, overall_portion_nice, str(overall_count_overall)]
    table_str += segs_to_table_line(tr)

    return table_str


def gen_precision_table(result):
    table_str = "\nrecovering precision:\n"
    th = ['type'] + COLS
    th[-1] = "overall"
    table_str += segs_to_table_line(th)

    overall_tp_3lib = 0
    overall_total_3lib = 0
    overall_tp_nice = 0
    overall_total_nice = 0

    for row in ROWS:
        if row.islower():
            continue

        row_lower = row.lower()
        tp_3lib = result[row_lower][TAG_3LIB]
        total_3lib = result[row][TAG_3LIB] + result[row_lower][TAG_3LIB]
        tp_nice = result[row_lower][TAG_NICE]
        total_nice = result[row][TAG_NICE] + result[row_lower][TAG_NICE]

        overall_tp_3lib += tp_3lib
        overall_total_3lib += total_3lib
        overall_tp_nice += tp_nice
        overall_total_nice += total_nice

        tp_overall = tp_3lib + tp_nice
        total_overall = total_3lib + total_nice

        precision_3lib = calculate_percent(tp_3lib, total_3lib)
        precision_nice = calculate_percent(tp_nice, total_nice)
        precision_overall = calculate_percent(tp_overall, total_overall)

        tr = [row, precision_3lib, precision_nice, str(precision_overall)]
        table_str += segs_to_table_line(tr)

    overall_tp_overall = overall_tp_3lib + overall_tp_nice
    overall_total_overall = overall_total_3lib + overall_total_nice

    overall_precision_3lib = calculate_percent(overall_tp_3lib, overall_total_3lib)
    overall_precision_nice = calculate_percent(overall_tp_nice, overall_total_nice)
    overall_precision_overall = calculate_percent(overall_tp_overall, overall_total_overall)

    tr = ["overall", overall_precision_3lib, overall_precision_nice, str(overall_precision_overall)]
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
