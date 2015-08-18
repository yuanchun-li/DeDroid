__author__ = 'liyc'
import numpy as np
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def gen_cdf(sample):
    plt.xlabel("Obfuscation Rate")
    plt.ylabel("CDF")

    plt.hist(sample, bins=10000, cumulative=True, normed=True, histtype="step", lw=2, ls='solid')
    plt.show()


def read_obfuscation_rates():
    f = open("/home/liyc/temp/unuglifyDEX_output/obfuscation_rates/obfuscation_rates_of_kuan_app.txt")
    app = None
    obfuscate_rates = {}
    for line in f.readlines():
        try:
            num = float(line)
            assert app is not None
            obfuscate_rates[app] = num
        except ValueError:
            app = line[2:-1]
    for key in obfuscate_rates.keys():
        if "/" in key:
            obfuscate_rates.pop(key)

    # out_file = open("/home/liyc/temp/unuglifyDEX_output/obfuscation_rates/obf_rates_kuan.json", "w")
    # out_file.write(json.dumps(obfuscate_rates))
    return obfuscate_rates.values()


if __name__ == '__main__':
    gen_cdf(read_obfuscation_rates())