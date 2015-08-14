import os
import sys
import time
import commands
import argparse
import random
import subprocess

def run(dataset_dir, output_dir):
    # clear
    reportPrecisionList = []
    logScoreList = []

    dataset_dir = os.path.abspath(dataset_dir)
    output_dir = os.path.abspath(output_dir)

    datasetList = os.popen("ls %s/" % dataset_dir).read().split('\n')[:-1]

    for onepass in datasetList:
        currentPassPath = dataset_dir + '/' + onepass

        reportList =  os.popen("ls %s/prediction_report_*" % currentPassPath).read().split('\n')[:-1]
        logList =  os.popen("ls %s/server_log_*" % currentPassPath).read().split('\n')[:-1]

        iLoop = len(reportList)
        while iLoop > 0:
            currReportDir = reportList[-iLoop]
            fReport = open(currReportDir, 'r')
            reportLines = fReport.readlines()
            reportPrecision = float(reportLines[18][reportLines[18].find('Precision:') + len('Precision:'):])
            reportPrecisionList.append(reportPrecision)
            fReport.close()

            currLogDir = logList[-iLoop]
            fLog = open(currLogDir, 'r')
            logLines = fLog.readlines()
            logEndScore = float(logLines[-1][logLines[-1].find('End score') + len('End score'):])
            logEdgeCount = float(logLines[-2][logLines[-2].find('Edge count') + len('Edge count'):])
            logScoreList.append(logEndScore / logEdgeCount)
            fLog.close()

            iLoop -= 1

    print 'reportPrecisionList: ' + str(len(reportPrecisionList))
    print 'logScoreList: ' + str(len(logScoreList))

    fSave = open('%s' % output_dir, 'w')
    for num in reportPrecisionList:
        fSave.write(str(num) + ' ')
    fSave.write('\n')
    for num in logScoreList:
        fSave.write(str(num) + ' ')
    fSave.write('\n')
    fSave.close()


def parse_args():
    """
    parse command line input
    generate options including host name, port number
    """
    parser = argparse.ArgumentParser(description="transform result data for plot")
    parser.add_argument("-i", action="store", dest="dataset_dir",
                        required=True, help="directory of test results (/path/to/runTestResult)")
    parser.add_argument("-o", action="store", dest="output_dir",
                        required=True, help="directory of test results")
    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()

    run(opts.dataset_dir,
        opts.output_dir)

    return


if __name__ == "__main__":
    main()