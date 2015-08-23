# coding: UTF-8

__author__ = 'liyc'
import argparse
import re
import sys
import json
import os
import difflib
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
from scipy.stats import linregress
import matplotlib.colors as colors
import matplotlib


def longest_common_substring(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]


def similarity_ratio(s1, s2):
    ratio = difflib.SequenceMatcher(a=s1, b=s2).ratio()
    # print s1, s2, ratio
    return ratio


def safe_divide(a, b):
    if b <= 0:
        return 1
    return float(a) / b


def safe_increase(data_dict, key):
    safe_add(data_dict, key, 1)


def safe_add(data_dict, key, num):
    if key in data_dict.keys():
        data_dict[key] += num
    else:
        data_dict[key] = num


def safe_append(data_dict, key, num):
    if key in data_dict.keys():
        data_dict[key].append(num)
    else:
        data_dict[key] = [num, ]


def safe_max(data_dict, key, num):
    if key in data_dict.keys():
        data_dict[key] = max(data_dict[key], num)
    else:
        data_dict[key] = num


def safe_get(data_dict, key):
    if key in data_dict.keys():
        return data_dict[key]
    else:
        return 0


def try_get(data_dict, key1, key2=None, key3=None):
    if key1 not in data_dict.keys():
        return None
    value = data_dict[key1]
    if key2 is None or not isinstance(value, dict):
        return value
    if key2 not in value.keys():
        return None
    value = value[key2]
    if key3 is None or not isinstance(value, dict):
        return value
    if key3 not in value.keys():
        return None
    return value[key3]


def sum_in_list(data_list, key1, key2=None, key3=None, start=0):
    new_list = []
    for item in data_list:
        value = try_get(item, key1, key2, key3)
        if value:
            new_list.append(value)
    return sum(new_list, start), len(new_list)


def average(list_data):
    return reduce(lambda x, y: x + y, list_data) / len(list_data)


def draw_regression(x, y, labelx, labely, title):
    """
    draw graph of x, y
    """
    matplotlib.rcParams.update({'font.size': 20})

    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    result = {
        "slope": slope, "intercept": intercept, "r_value": r_value, "p_value": p_value
    }
    print result
    fit_f = lambda xs: [slope * x + intercept for x in xs]
    # fit_f is now a function which takes in x and returns an estimate for y

    # draw with scatter
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    fig, ax = plt.subplots()
    ax.scatter(x, y, c=z, s=80, edgecolor='', cmap=plt.cm.Blues, marker=u'o', norm=colors.LogNorm())
    ax.plot(x, y, " ", x, fit_f(x), '--k', ms=5)
    plt.xlabel(labelx)
    plt.ylabel(labely)

    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1, x2, 0, 1))

    # plt.show()
    plt.savefig('figure/%s.png' % title)
    plt.savefig('figure/%s.pdf' % title)
    return result


def draw_cdf(data, labelx, labely, title):
    matplotlib.rcParams.update({'font.size': 20})

    plt.xlabel(labelx)
    plt.ylabel(labely)

    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1, x2, 0, 1))

    plt.hist(data, bins=10000, cumulative=True, normed=True, histtype="step", lw=2, ls='solid')
    # plt.show()
    plt.savefig('figure/%s.png' % title)
    plt.savefig('figure/%s.pdf' % title)


COMMON_SUBSTR_THRESHOLD = 3
SIMILARITY_RATIO_THRESHOLD = 0.5
MAPPING_LINE_RE = re.compile('^\[(.)\] .* (.*)/(.*)$')


class PredictionItem(object):
    def __init__(self, (origin_count, predict_count, tp)):
        self.origin_count = origin_count
        self.predict_count = predict_count
        self.tp = tp
        self.precision = safe_divide(tp, predict_count)
        self.recall = safe_divide(tp, origin_count)

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict())


class MappingReport(object):
    def __init__(self, input_file):
        self.origin_count = {}
        self.predict_count = {}
        self.tp_count = {}
        self.substr_tp_count = {}
        self.similarity_tp_count = {}

        self.similarity_ratios = {}

        self._process_file(input_file)

        self.packages = PredictionItem(self.triple_safe_get_tp('p'))
        self.classes = PredictionItem(self.triple_safe_get_tp('c'))
        self.fields = PredictionItem(self.triple_safe_get_tp('f'))
        self.methods = PredictionItem(self.triple_safe_get_tp('m'))
        self.overall = PredictionItem(self.triple_safe_get_tp('s'))

        self.packages_substr = PredictionItem(self.triple_safe_get_substr_tp('p'))
        self.classes_substr = PredictionItem(self.triple_safe_get_substr_tp('c'))
        self.fields_substr = PredictionItem(self.triple_safe_get_substr_tp('f'))
        self.methods_substr = PredictionItem(self.triple_safe_get_substr_tp('m'))
        self.overall_substr = PredictionItem(self.triple_safe_get_substr_tp('s'))

        self.packages_similarity = PredictionItem(self.triple_safe_get_similarity_tp('p'))
        self.classes_similarity = PredictionItem(self.triple_safe_get_similarity_tp('c'))
        self.fields_similarity = PredictionItem(self.triple_safe_get_similarity_tp('f'))
        self.methods_similarity = PredictionItem(self.triple_safe_get_similarity_tp('m'))
        self.overall_similarity = PredictionItem(self.triple_safe_get_similarity_tp('s'))

    def triple_safe_get_tp(self, flag):
        return (safe_get(self.origin_count, flag),
                safe_get(self.predict_count, flag),
                safe_get(self.tp_count, flag))

    def triple_safe_get_substr_tp(self, flag):
        return (safe_get(self.origin_count, flag),
                safe_get(self.predict_count, flag),
                safe_get(self.substr_tp_count, flag))

    def triple_safe_get_similarity_tp(self, flag):
        return (safe_get(self.origin_count, flag),
                safe_get(self.predict_count, flag),
                safe_get(self.similarity_tp_count, flag))

    def _process_file(self, input_file):
        input_file_stream = open(input_file, 'r')
        for line in input_file_stream.readlines():
            m = MAPPING_LINE_RE.match(line)
            if not m:
                continue
            flag, origin, predict = m.group(1).lower(), m.group(2), m.group(3)
            if origin != "?":
                safe_increase(self.origin_count, flag)
            if predict != "?":
                safe_increase(self.predict_count, flag)
            if origin == predict:
                safe_increase(self.tp_count, flag)
                safe_increase(self.substr_tp_count, flag)
                safe_increase(self.similarity_tp_count, flag)
                safe_append(self.similarity_ratios, flag, 1.0)
            else:
                ratio = similarity_ratio(origin, predict)
                safe_append(self.similarity_ratios, flag, ratio)
                if len(longest_common_substring(origin, predict)) >= COMMON_SUBSTR_THRESHOLD:
                    safe_increase(self.substr_tp_count, flag)
                if ratio >= SIMILARITY_RATIO_THRESHOLD:
                    safe_increase(self.similarity_tp_count, flag)
        self.origin_count['s'] = sum(self.origin_count.values())
        self.predict_count['s'] = sum(self.predict_count.values())
        self.tp_count['s'] = sum(self.tp_count.values())
        self.substr_tp_count['s'] = sum(self.substr_tp_count.values())
        self.similarity_tp_count['s'] = sum(self.similarity_tp_count.values())
        self.similarity_ratios['s'] = sum(self.similarity_ratios.values(), [])

    def to_dict(self):
        result = {
            "equal": {
                "packages": self.packages.to_dict(),
                "classes": self.classes.to_dict(),
                "fields": self.fields.to_dict(),
                "methods": self.methods.to_dict(),
                "overall": self.overall.to_dict()
            },
            "common_substr": {
                "packages": self.packages_substr.to_dict(),
                "classes": self.classes_substr.to_dict(),
                "fields": self.fields_substr.to_dict(),
                "methods": self.methods_substr.to_dict(),
                "overall": self.overall_substr.to_dict()
            },
            "similar": {
                "packages": self.packages_similarity.to_dict(),
                "classes": self.classes_similarity.to_dict(),
                "fields": self.fields_similarity.to_dict(),
                "methods": self.methods_similarity.to_dict(),
                "overall": self.overall_similarity.to_dict()
            }
        }
        return result

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())

    def gen_similarity_ratio_cdf(self, output_file_stream):
        output_file_stream.write(json.dumps(self.similarity_ratios, indent=2))
        draw_cdf(self.similarity_ratios['s'], 'Similarity Ratio', 'CDF', 'similarity_ratio')


def analyse_mapping_report(input_file, output_file_stream):
    MappingReport(input_file).dump(output_file_stream)


class MappingReports(object):
    def __init__(self, input_dir):
        self.result = {}
        self.similarity_ratios = {}
        self._process_dir(input_dir)

    def _process_dir(self, input_dir):
        all_mappings = []
        all_similarity_ratios = []
        for p, d, filenames in os.walk(input_dir):
            for filename in filenames:
                m = PREDICTION_REPORT_FILE_RE.match(filename)
                if m:
                    app_id = m.group(1)
                    if app_id not in self.result:
                        self.result[app_id] = {}
                    mapping_report_for_app = MappingReport(os.path.join(p, filename))
                    self.result[app_id]['mapping'] = mapping_report_for_app.to_dict()
                    all_mappings.append(self.result[app_id]['mapping'])
                    all_similarity_ratios.append(mapping_report_for_app.similarity_ratios)
                    continue
                m = SERVER_LOG_FILE_RE.match(filename)
                if m:
                    app_id = m.group(1)
                    if app_id not in self.result:
                        self.result[app_id] = {}
                    self.result[app_id]['score'] = ServerLog(os.path.join(p, filename)).to_dict()
                    continue

        overall = {}
        mapping_sample = all_mappings[0]
        for key1 in mapping_sample.keys():
            overall[key1] = {}
            for key2 in mapping_sample[key1].keys():
                overall[key1][key2] = {}
                for key3 in mapping_sample[key1][key2].keys():
                    if key3 in ['precision', 'recall']:
                        continue
                    overall[key1][key2][key3] = {}
                    value_sum, count = sum_in_list(all_mappings, key1, key2, key3)
                    overall[key1][key2][key3] = value_sum
                overall[key1][key2]['precision'] = safe_divide(overall[key1][key2]['tp'],
                                                               overall[key1][key2]['predict_count'])
                overall[key1][key2]['recall'] = safe_divide(overall[key1][key2]['tp'],
                                                            overall[key1][key2]['origin_count'])

        self.result['overall'] = overall

        overall = {}
        similarity_ratio_sample = all_similarity_ratios[0]
        for key in similarity_ratio_sample.keys():
            overall[key], count = sum_in_list(all_similarity_ratios, key, start=[])

        self.similarity_ratios = overall

    def to_dict(self):
        return self.result

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())

    def gen_similarity_ratio_cdf(self, output_file_stream):
        output_file_stream.write(json.dumps(self.similarity_ratios, indent=2))
        draw_cdf(self.similarity_ratios['s'], 'Similarity Ratio', 'CDF', 'similarity_ratio')


def analyse_mapping_reports(input_dir, output_file_stream):
    MappingReports(input_dir).dump(output_file_stream)


def analyse_similarity_ratio(input_file, output_file_stream):
    if os.path.isfile(input_file):
        MappingReport(input_file).gen_similarity_ratio_cdf(output_file_stream)
    else:
        MappingReports(input_file).gen_similarity_ratio_cdf(output_file_stream)


TEST_LOG_GREP = """
grep -e "^pass" -e "com.lynnlyc.Config init$" -e "training data samples.$" -e "Saving model done$" -e "com.lynnlyc.Predictor evaluateResult$"
""".strip()
PASS_GREP = re.compile('^pass: (.+)$')
TRAINING_START_GREP = re.compile('^I([0-9]+) ([0-9:.]+) .* training data samples.$')
TRAINING_END_GREP = re.compile('^I([0-9]+) ([0-9:.]+) .* Saving model done$')
PREDICT_START_GREP = re.compile('^.* ([0-9]+), [0-9]+ ([0-9:]+) .* com.lynnlyc.Config init$')
PREDICT_STOP_GREP = re.compile('^.* ([0-9]+), [0-9]+ ([0-9:]+) .* com.lynnlyc.Predictor evaluateResult$')


# MONTH_MAP = {"一月": "01", "二月": "02", "三月": "03", "四月": "04", "五月": "05", "六月": "06",
#              "七月": "07", "八月": "08", "九月": "09", "十月": "10", "十一月": "11", "十二月": "12"}


class TestLog(object):
    def __init__(self, input_file):
        self.passes = {}
        self._process_file(input_file)

    def _process_file(self, input_file):
        input_stream = os.popen("%s %s" % (TEST_LOG_GREP, input_file))
        stage = 3
        last_time = None
        current_pass = None

        for line in input_stream.readlines():
            if stage == 1:
                m = TRAINING_START_GREP.match(line)
                if m:
                    date, time = m.group(1), m.group(2)
                    dt = datetime.strptime("%s %s" % (date, time), "%m%d %H:%M:%S.%f")
                    last_time = dt
                    stage = 2
                    continue
            elif stage == 2:
                m = TRAINING_END_GREP.match(line)
                if m:
                    date, time = m.group(1), m.group(2)
                    dt = datetime.strptime("%s %s" % (date, time), "%m%d %H:%M:%S.%f")
                    train_cost = dt - last_time
                    self.passes[current_pass]["training_cost"] = int(train_cost.total_seconds())
                    stage = 3
                    continue
            elif stage == 3:
                m = PREDICT_START_GREP.match(line)
                if m:
                    date, time = m.group(1), m.group(2)
                    dt = datetime.strptime("%s %s" % (date, time), "%d %H:%M:%S")
                    last_time = dt
                    stage = 4
                    continue
                m = PASS_GREP.match(line)
                if m:
                    current_pass = m.group(1)
                    self.passes[current_pass] = {}
                    stage = 1
                    continue
            elif stage == 4:
                m = PREDICT_STOP_GREP.match(line)
                if m:
                    date, time = m.group(1), m.group(2)
                    dt = datetime.strptime("%s %s" % (date, time), "%d %H:%M:%S")
                    predict_cost = dt - last_time
                    predict_cost_int = int(predict_cost.total_seconds())
                    safe_increase(self.passes[current_pass], "predict_count")
                    safe_add(self.passes[current_pass], "predict_cost_total", predict_cost_int)
                    safe_max(self.passes[current_pass], "predict_cost_max", predict_cost_int)
                    stage = 3
                    continue

        for pass_id in self.passes.keys():
            self.passes[pass_id]["predict_cost_average"] = safe_divide(
                safe_get(self.passes[pass_id], "predict_cost_total"),
                safe_get(self.passes[pass_id], "predict_count"))

    def to_dict(self):
        return self.passes

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())


def analyse_test_log(input_file, output_file_stream):
    TestLog(input_file).dump(output_file_stream)


END_SCORE_RE = re.compile('^.* End score *([0-9.]+)$')
EDGE_COUNT_RE = re.compile('^.* Edge count *([0-9]+)$')


class ServerLog(object):
    def __init__(self, input_file):
        self.crf_score = 0
        self.edge_count = 0
        self.dedroid_score = 0
        self._process_file(input_file)

    def _process_file(self, input_file):
        input_file_stream = open(input_file, 'r')
        for line in input_file_stream.readlines():
            m = END_SCORE_RE.match(line)
            if m:
                self.crf_score = float(m.group(1))
                continue
            m = EDGE_COUNT_RE.match(line)
            if m:
                self.edge_count = int(m.group(1))
                continue
        self.dedroid_score = safe_divide(self.crf_score, self.edge_count)

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())


def analyse_server_log(input_file, output_file_stream):
    ServerLog(input_file).dump(output_file_stream)


class TraningData(object):
    def __init__(self, input_file):
        self.edge_count = {}
        self._process_file(input_file)

    def _process_file(self, input_file):
        input_file_stream = open(input_file, 'r')

        for line in input_file_stream.readlines():
            training_data = json.loads(line)
            for e in training_data['query']:
                if 'f2' in e.keys():
                    edge_name = e['f2']
                    edge_type = edge_name[:2]
                    safe_increase(self.edge_count, edge_type)

        self.edge_count["overall"] = sum(self.edge_count.values())

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())


def analyse_training_data(input_file, output_file_stream):
    TraningData(input_file).dump(output_file_stream)


PREDICTION_REPORT_FILE_RE = re.compile('prediction_report_(.*).txt')
SERVER_LOG_FILE_RE = re.compile('server_log_(.*).log')


class SinglePass(object):
    def __init__(self, input_dir):
        self.result = {}
        self._process_dir(input_dir)

    def _process_dir(self, input_dir):
        all_mappings = []
        for filename in os.listdir(input_dir):
            m = PREDICTION_REPORT_FILE_RE.match(filename)
            if m:
                app_id = m.group(1)
                if app_id not in self.result:
                    self.result[app_id] = {}
                self.result[app_id]['mapping'] = MappingReport(os.path.join(input_dir, filename)).to_dict()
                all_mappings.append(self.result[app_id]['mapping'])
                continue
            m = SERVER_LOG_FILE_RE.match(filename)
            if m:
                app_id = m.group(1)
                if app_id not in self.result:
                    self.result[app_id] = {}
                self.result[app_id]['score'] = ServerLog(os.path.join(input_dir, filename)).to_dict()
                continue

        overall = {}
        mapping_sample = all_mappings[0]
        for key1 in mapping_sample.keys():
            overall[key1] = {}
            for key2 in mapping_sample[key1].keys():
                overall[key1][key2] = {}
                for key3 in mapping_sample[key1][key2].keys():
                    if key3 in ['precision', 'recall']:
                        continue
                    overall[key1][key2][key3] = {}
                    value_sum, count = sum_in_list(all_mappings, key1, key2, key3)
                    overall[key1][key2][key3] = value_sum
                overall[key1][key2]['precision'] = safe_divide(overall[key1][key2]['tp'],
                                                               overall[key1][key2]['predict_count'])
                overall[key1][key2]['recall'] = safe_divide(overall[key1][key2]['tp'],
                                                            overall[key1][key2]['origin_count'])

        self.result['overall'] = overall

    def to_dict(self):
        return self.result

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())


def analyse_1pass(input_dir, output_file_stream):
    SinglePass(input_dir).dump(output_file_stream)


PASS_DIR_RE = re.compile('pass_(.*)')
EVALUATION_LOG_FILE_RE = re.compile('.*\.log')


class CrossValidation(object):
    def __init__(self, input_file, from_json=False):
        self.result = {}

        if from_json:
            self._load_from_json(input_file)
        else:
            self._process_dir(input_file)

    def _load_from_json(self, input_file):
        input_file_stream = open(input_file, 'r')
        data = json.load(input_file_stream)
        self.result = data

    def _process_dir(self, input_dir):
        per_pass_results = []
        for filename in os.listdir(input_dir):
            m = PASS_DIR_RE.match(filename)
            if not m:
                continue
            pass_id = m.group(1)
            per_pass_result = SinglePass(os.path.join(input_dir, filename)).to_dict()['overall']
            self.result[pass_id] = per_pass_result
            per_pass_results.append(per_pass_result)

        overall = {}
        mapping_sample = per_pass_results[0]
        for key1 in mapping_sample.keys():
            overall[key1] = {}
            for key2 in mapping_sample[key1].keys():
                overall[key1][key2] = {}
                for key3 in mapping_sample[key1][key2].keys():
                    if key3 in ['precision', 'recall']:
                        continue
                    overall[key1][key2][key3] = {}
                    value_sum, count = sum_in_list(per_pass_results, key1, key2, key3)
                    overall[key1][key2][key3] = value_sum
                overall[key1][key2]['precision'] = safe_divide(overall[key1][key2]['tp'],
                                                               overall[key1][key2]['predict_count'])
                overall[key1][key2]['recall'] = safe_divide(overall[key1][key2]['tp'],
                                                            overall[key1][key2]['origin_count'])

        self.result['overall'] = overall

    def to_dict(self):
        return self.result

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())

    def gen_table(self, output_file):
        seperator = ","
        heads = ["item", ]
        for head in self.result['overall'].keys():
            heads += ["TP_%s" % head, "precision_%s" % head, "recall_%s" % head]
        output_file.write("%s\n" % seperator.join(heads))
        for key in ["packages", "classes", "fields", "methods", "overall"]:
            values = []
            for head in self.result['overall'].keys():
                values += [
                           "%d" % self.result['overall'][head][key]['tp'],
                           "{0:.2f}%".format(100 * self.result['overall'][head][key]['precision']),
                           "{0:.2f}%".format(100 * self.result['overall'][head][key]['recall'])]
            output_file.write("%s\n" % seperator.join(values))


def analyse_cross_validation(input_dir, output_file_stream):
    CrossValidation(input_dir).dump(output_file_stream)


def analyse_cross_validation_result(input_file, output_file_stream):
    CrossValidation(input_file, from_json=True).gen_table(output_file_stream)


class FeatureEvaluation(object):
    def __init__(self, input_file, from_json=False):
        self.result = {}
        self.performance = {}

        if from_json:
            self._load_from_json(input_file)
        else:
            self._process_dir(input_file)

    def _load_from_json(self, input_file):
        input_file_stream = open(input_file, 'r')
        data = json.load(input_file_stream)
        self.result = data['result']
        self.performance = data['performance']

    def _process_dir(self, input_dir):
        per_pass_results = []
        for filename in os.listdir(input_dir):
            m = EVALUATION_LOG_FILE_RE.match(filename)
            if m:
                self.performance = TestLog(os.path.join(input_dir, filename)).to_dict()
                break
        passes_dir = os.path.join(input_dir, "runTestResult")
        for filename in os.listdir(passes_dir):
            m = PASS_DIR_RE.match(filename)
            if not m:
                continue
            pass_id = m.group(1)
            per_pass_result = SinglePass(os.path.join(passes_dir, filename)).to_dict()['overall']
            self.result[pass_id] = per_pass_result
            per_pass_results.append(per_pass_result)

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())

    def gen_table(self, output_file):
        seperator = ","
        heads = ["mode", "training_time(s)", "prediction_time_average(s)", "prediction_time_max(s)"]

        result_sample = self.result.values()[0]
        for head in result_sample.keys():
            heads += ["precision_%s" % head, "recall_%s" % head]

        output_file.write("%s\n" % seperator.join(heads))
        for key in sorted(self.result.keys()):
            values = [
                key,
                "%d" % self.performance[key]['training_cost'],
                "%d" % int(self.performance[key]['predict_cost_average']),
                "%d" % int(self.performance[key]['predict_cost_max'])]
            for head in result_sample.keys():
                values += [
                    "{0:.2f}%".format(100 * self.result[key][head]['overall']['precision']),
                    "{0:.2f}%".format(100 * self.result[key][head]['overall']['recall'])]
            output_file.write("%s\n" % seperator.join(values))


def analyse_feature_evaluation(input_dir, output_file_stream):
    FeatureEvaluation(input_dir).dump(output_file_stream)


def analyse_feature_evaluation_result(input_file, output_file_stream):
    FeatureEvaluation(input_file, from_json=True).gen_table(output_file_stream)


class ScoreRegression(object):
    def __init__(self, input_file):
        self.scores = []
        self.precisions_equal = []
        self.recalls_equal = []
        self.precisions_substr = []
        self.recalls_substr = []
        self.precisions_equal_regress = {}
        self.recalls_equal_regress = {}
        self.precisions_substr_regress = {}
        self.recalls_substr_regress = {}
        self._process_file(input_file)
        self.draw_regression_graphs()

    def _process_file(self, input_file):
        input_file_stream = open(input_file, 'r')
        data = json.load(input_file_stream)

        data.pop('overall')
        for key in data.keys():
            score = data[key]['score']['dedroid_score']
            precision_equal = data[key]['mapping']['equal']['overall']['precision']
            recall_equal = data[key]['mapping']['equal']['overall']['recall']
            precision_substr = data[key]['mapping']['common_substr']['overall']['precision']
            recall_substr = data[key]['mapping']['common_substr']['overall']['recall']
            self.scores.append(score)
            self.precisions_equal.append(precision_equal)
            self.recalls_equal.append(recall_equal)
            self.precisions_substr.append(precision_substr)
            self.recalls_substr.append(recall_substr)

    def draw_regression_graphs(self):
        self.precisions_equal_regress = \
            draw_regression(self.scores, self.precisions_equal,
                            "DeDroid Score", "Precision (equal)", "regression_precisions_equal")
        self.recalls_equal_regress = \
            draw_regression(self.scores, self.recalls_equal,
                            "DeDroid Score", "Recall (equal)", "regression_recalls_equal")
        self.precisions_substr_regress = \
            draw_regression(self.scores, self.precisions_substr,
                            "DeDroid Score", "Precision (3-letter common sub-string)", "regression_precisions_substr")
        self.recalls_substr_regress = \
            draw_regression(self.scores, self.recalls_substr,
                            "DeDroid Score", "Recall (3-letter common sub-string)", "regression_recalls_substr")

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())


def score_regression(input_file, output_file_stream):
    ScoreRegression(input_file).dump(output_file_stream)


class ObfuscationRates(object):
    def __init__(self, input_file):
        self.obfuscation_rates = {}
        self._process_file(input_file)

    def _process_file(self, input_file):
        f = open(input_file, 'r')
        app = None
        for line in f.readlines():
            try:
                num = float(line)
                assert app is not None
                self.obfuscation_rates[app] = num
            except ValueError:
                app = line[2:-1]
        for key in self.obfuscation_rates.keys():
            if "/" in key:
                self.obfuscation_rates.pop(key)

    def to_dict(self):
        return self.obfuscation_rates

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    def dump(self, output_file):
        output_file.write(self.to_json())

    def gen_cdf(self):
        draw_cdf(self.obfuscation_rates.values(), 'Obfuscation Rate', 'CDF', 'obfuscation_rate_cdf')


def analyse_obfuscation_rates(input_file, output_file_stream):
    ObfuscationRates(input_file).gen_cdf()


def run(input_file, output_file, mode):
    output_file_stream = open(output_file, 'w') if output_file is not None else sys.stdout
    if mode == "mapping_report":
        analyse_mapping_report(input_file, output_file_stream)
    if mode == "mapping_reports":
        analyse_mapping_reports(input_file, output_file_stream)
    elif mode == "test_log":
        analyse_test_log(input_file, output_file_stream)
    elif mode == "server_log":
        analyse_server_log(input_file, output_file_stream)
    elif mode == "training_data":
        analyse_training_data(input_file, output_file_stream)
    elif mode == "1pass":
        analyse_1pass(input_file, output_file_stream)
    elif mode == "cross_validation":
        analyse_cross_validation(input_file, output_file_stream)
    elif mode == "feature_evaluation":
        analyse_feature_evaluation(input_file, output_file_stream)
    elif mode == "score_regression":
        score_regression(input_file, output_file_stream)
    elif mode == "cross_validationR":
        analyse_cross_validation_result(input_file, output_file_stream)
    elif mode == "feature_evaluationR":
        analyse_feature_evaluation_result(input_file, output_file_stream)
    elif mode == "similarity_ratio":
        analyse_similarity_ratio(input_file, output_file_stream)
    elif mode == "obfuscation_rate":
        analyse_obfuscation_rates(input_file, output_file_stream)
    else:
        print "Unknown mode: " + mode


def parse_args():
    """
    parse command line input
    generate options including host name, port number
    """
    mode_help = """available modes are:
    mapping_report      analyse the mapping report generated by mapping_compare.py
    mapping_reports     analyse the mapping reports under a directory
    test_log            analyse the test log generated by run_cross_validation.py or run_feature_evaluation.py
    server_log          analyse the analysis log generated by nice2server
    training_data       analyse the traning data generated by batTrain.py or UnuglifyDEX
    1pass               analyse the result directory of one pass generated by run_cross_validation.py or run_feature_evaluation.py
    cross_validation    analyse the cross validation result generated by run_cross_validation.py
    feature_evaluation  analyse the feature evaluation result generated by run_feature_evaluation.py
    score_regression    regression analysis with the json generated in mapping_reports mode
    cross_validationR   analyse the json generated in cross_validation, and gen table
    feature_evaluationR analyse the json generated in feature_evaluation, and gen table
    similarity_ratio    get the cdf for the similarity ratios between deobfuscated names and origins
    obfuscation_rate    get the cdf for obfuscation rate
    """

    parser = argparse.ArgumentParser(description="evaluation data analyser of DeDroid",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", action="store", dest="input_file",
                        required=True, help="directory/file of results")
    parser.add_argument("-o", action="store", dest="output_file",
                        help="output file, default is stdout")
    parser.add_argument("-m", action="store", dest="analysis_mode",
                        required=True, help=mode_help)

    options = parser.parse_args()
    # print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()

    run(opts.input_file,
        opts.output_file,
        opts.analysis_mode)

    return


if __name__ == "__main__":
    main()
