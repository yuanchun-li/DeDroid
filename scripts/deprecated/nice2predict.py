# Fetching INFERs from nice2server using test data.
# Author: YZY, Liyc
# Date: 2015.7.18, 2016.1.16

import pyjsonrpc
import json
import sys, argparse


def parse_args():
    """
    parse command line input
    """
    parser = argparse.ArgumentParser(description="generate training data of apks")
    parser.add_argument("-i", action="store", dest="input_file",
                        required=True, help="input json file to predict")
    parser.add_argument("-o", action="store", dest="output_file",
                        required=True, help="file path to store predicted data")
    parser.add_argument("-server", action="store", dest="server_url", default="http://localhost:5745",
                        required=False, help="url of nice2predict server")
    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()

    fOpen = open(opts.input_file, 'r')
    cRead = fOpen.read()
    fOpen.close()
    cREQList = [cRead]

    http_client = pyjsonrpc.HttpClient(url=opts.server_url)

    fWrite = open(opts.output_file, 'w')

    for cREQ in cREQList:
        if cREQ == '':
            break

        callParaDict = json.loads(cREQ)

        inferDict = http_client.call(
            'infer', query=callParaDict['query'], assign=callParaDict['assign']
        )
        inferJSON = json.dumps(inferDict)

        fWrite.write(str(inferJSON).replace(' ', '') + '\n')

    fWrite.close()


if __name__ == "__main__":
    main()
