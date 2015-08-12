import os
import sys
import time
import commands
import argparse
import random
import subprocess


def processDataSet(dataset_dir):
    dataset_dir = os.path.abspath(dataset_dir)
    datasetList = os.popen("ls %s/" % dataset_dir).read().split('\n')[:-1]

    random.shuffle(datasetList)
    return datasetList


# input: apk-debug directories
# output: batTrainJsonList.txt, models at nice2predict folder
def runTrain(dataset_dir, dataList, output_dir,
             path_to_unuglifyDEX, path_to_nice2predict):
    # clear
    output_dir = os.path.abspath(output_dir)
    path_to_unuglifyDEX = os.path.abspath(path_to_unuglifyDEX)
    path_to_nice2predict = os.path.abspath(path_to_nice2predict)

    training_file_name = "batTrainJsonList.txt"

    r = os.system("rm -rf %s/UnuglifyDex_TRAIN*/" % output_dir)
    if r != 0:
        print "rm failed"
        sys.exit(r)
    r = os.system("rm -rf %s/%s" % (output_dir, training_file_name))
    if r != 0:
        print "rm failed"
        sys.exit(r)
    time.sleep(2)

    sdkPara = '-sdk $ANDROID_SDK_HOME/platforms/android-22/android.jar'

    fJsonList = open("%s/%s" % (output_dir, training_file_name), 'w')
    fJsonList.close()

    apkList = map(lambda x: dataset_dir + '/' + x + '/app-debug.apk', dataList)

    totalNum = len(apkList)
    iCount = 1

    print 'Generating batTrainJsonList...'
    for apk in apkList:
        print(str(iCount) + '/' + str(totalNum))
        iCount = iCount + 1
        (retVal, dexLog) = commands.getstatusoutput("java -jar %s -i %s -o %s -train %s" %
                                                    (path_to_unuglifyDEX, apk, output_dir, sdkPara))

        if retVal != 0:
            print dexLog
            continue

        resultPath = os.popen('ls %s/UnuglifyDex_TRAIN*/train.json' % output_dir).read().split('\n')[0]

        jsonFile = open(resultPath, 'r')
        jsonObject = jsonFile.read()
        jsonFile.close()

        fJsonList = open("%s/%s" % (output_dir, training_file_name), 'a')
        fJsonList.write(jsonObject)
        fJsonList.close()

        os.system('rm -rf %s/UnuglifyDex_TRAIN*' % output_dir)

    # now get batTrainJsonList.txt at output dir
    trainData = output_dir + '/' + training_file_name

    pwd = os.popen('pwd').read().split('\n')[0]

    os.chdir(path_to_nice2predict)
    os.system('bin/training/train -logtostderr --input %s' % trainData)
    os.chdir(pwd)

    os.system('rm %s' % trainData)
    os.system('cp %s/model_features %s/model_features' % (path_to_nice2predict, output_dir))
    os.system('cp %s/model_strings %s/model_strings' % (path_to_nice2predict, output_dir))


# input: apk-release directories
# output: prediction_report_num
def runPredict(dataset_dir, dataList, output_dir,
               path_to_unuglifyDEX, path_to_nice2predict):
    # clear
    output_dir = os.path.abspath(output_dir)
    path_to_unuglifyDEX = os.path.abspath(path_to_unuglifyDEX)
    path_to_nice2predict = os.path.abspath(path_to_nice2predict)

    r = os.system("rm -rf %s/UnuglifyDex_PREDICT*/" % output_dir)
    if r != 0:
        print "rm failed"
        sys.exit(r)
    time.sleep(2)
    sdkPara = '-sdk $ANDROID_SDK_HOME/platforms/android-22/android.jar'

    pwd = os.popen('pwd').read().split('\n')[0]

    os.chdir(path_to_nice2predict)
    server_args = ["bin/server/nice2server", "-logtostderr", "-graph_loopy_bp_passes", "5", "-v", "2"]
    serverP = subprocess.Popen(server_args, stderr=subprocess.PIPE)
    read_until(serverP.stderr, "started")
    os.chdir(pwd)

    apkList = map(lambda x: dataset_dir + '/' + x + '/app-release.apk', dataList)

    totalNum = len(apkList)
    iCount = 0

    print 'Predicting...'
    for apk in apkList:
        print(str(iCount + 1) + '/' + str(totalNum))

        (retVal, dexLog) = commands.getstatusoutput("java -jar %s -i %s -o %s %s" %
                                                    (path_to_unuglifyDEX, apk, output_dir, sdkPara))
        print retVal, dexLog

        resultMapPath = os.popen('ls %s/UnuglifyDex_PREDICT*/mapping.txt' % output_dir).read().split('\n')[0]
        originMapPath = dataset_dir + '/' + dataList[iCount] + '/mapping.txt'

        os.system('python mapping_compare.py --proguard %s --predict %s -o %s' %
                  (originMapPath, resultMapPath, output_dir))
        # backup mappings.txt
        os.system('cp %s %s/predict_mapping_%s.txt' % (resultMapPath, output_dir, dataList[iCount]))
        os.system('cp %s %s/proguard_mapping_%s.txt' % (originMapPath, output_dir, dataList[iCount]))

        os.system('mv %s/compare_report.txt %s/prediction_report_%s.txt' %
                  (output_dir, output_dir, dataList[iCount]))

        os.system('rm -rf %s/UnuglifyDex_PREDICT*' % output_dir)
        os.system('rm %s/predict_result.txt' % output_dir)
        os.system('rm %s/proguard_result.txt' % output_dir)

        server_logs = read_until(serverP.stderr, "End score")

        f = open("%s/server_log_%s.log" % (output_dir, dataList[iCount]), 'w')
        f.writelines(server_logs)
        f.close()

        iCount = iCount + 1

    # serverP.terminate()
    serverP.kill()


def read_until(stream_file, token):
    lines = []
    while True:
        line = stream_file.readline()
        lines.append(line)
        if token in line:
            break
    return lines


def run(dataset_dir, output_dir,
        path_to_unuglifyDEX, path_to_nice2predict, bLoop):
    dataList = processDataSet(dataset_dir)
    dataLen = len(dataList)
    predictLen = dataLen / 10
    iLoop = 1

    if bLoop:
        iLoop = 10

    os.system('rm -rf %s/runTestResult' % output_dir)
    os.system('mkdir %s/runTestResult' % output_dir)
    while iLoop > 0:
        currentPassPath = '%s/runTestResult/pass_%s' % (output_dir, 11 - iLoop)

        os.system('mkdir %s' % currentPassPath)

        fApkPredictList = open('%s/train.txt' % currentPassPath, 'w')
        for apkID in dataList[:-predictLen]:
            fApkPredictList.write(apkID + '\n')
        fApkPredictList.close()

        # runTrain(dataset_dir, dataList[:-predictLen], currentPassPath,
        #          path_to_unuglifyDEX, path_to_nice2predict)
        #
        # runPredict(dataset_dir, dataList[-predictLen:], currentPassPath,
        #            path_to_unuglifyDEX, path_to_nice2predict)

        # roll
        dataList = dataList[-predictLen:] + dataList[:-predictLen]
        iLoop -= 1


def parse_args():
    """
    parse command line input
    generate options including host name, port number
    """
    parser = argparse.ArgumentParser(description="generate training data of apks")
    parser.add_argument("-i", action="store", dest="dataset_dir",
                        required=True, help="directory of apks")
    parser.add_argument("-o", action="store", dest="output_dir",
                        required=True, help="directory of output")
    parser.add_argument("-p", action="store", dest="path_to_unuglifyDEX",
                        required=True, help="path to unuglifyDEX.jar")
    parser.add_argument("-s", action="store", dest="path_to_nice2predict",
                        required=True, help="path to nice2predict root path")
    parser.add_argument("--loop", action="store_true",
                        help="loop the dataset 10 times")
    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()

    run(opts.dataset_dir,
        opts.output_dir,
        opts.path_to_unuglifyDEX,
        opts.path_to_nice2predict,
        opts.loop)

    return


if __name__ == "__main__":
    main()
