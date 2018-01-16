import re
import operator


WORKING_DIR = "data/"


def get_word2freq_from_file(word2freq_file_name, freq_threshold=0):
    word2freq_file = open(word2freq_file_name)
    word2freq_lines = word2freq_file.readlines()

    word2freq = {}
    word2freq_re = re.compile("^(\d+) (.*)$")

    for line in word2freq_lines:
        m = word2freq_re.match(line)
        if not m:
            print "warning: unexpected line: %s" % line
            continue

        freq = int(m.group(1))
        word = m.group(2).strip()

        if freq < freq_threshold:
            continue

        word2freq[word] = freq

    word2freq_file.close()
    return word2freq


def filter_app_words():
    marketapp_word2freq = get_word2freq_from_file(WORKING_DIR + "marketapp_word2freq.txt")
    brown_word2freq = get_word2freq_from_file(WORKING_DIR + "brown_dict.txt")
    filtered_words = []
    for word in marketapp_word2freq:
        freq = marketapp_word2freq[word]
        if freq > 700:
            filtered_words.append(word)
        elif len(word) > 2 and word in brown_word2freq:
            filtered_words.append(word)

    filtered_word2freq = [(marketapp_word2freq[word], word) for word in filtered_words]
    filtered_word2freq_sorted = sorted(filtered_word2freq, key=operator.itemgetter(0), reverse=True)
    filtered_word2freq_lines = ["%d %s\n" % (freq, word) for freq, word in filtered_word2freq_sorted]
    word2id_lines = ["%d %s\n" % (i, filtered_word2freq_sorted[i][1]) for i in range(0, len(filtered_word2freq_sorted))]

    output_file = open(WORKING_DIR + "filtered_word2freq.txt", "w")
    output_file.writelines(filtered_word2freq_lines)
    output_file.close()

    output_file = open(WORKING_DIR + "word2id.txt", "w")
    output_file.writelines(word2id_lines)
    output_file.close()


filter_app_words()
