import os
import sys
import time
import commands
import argparse
import random
import subprocess


# input: apk-release directories
# output: prediction_report_num
def runPredict(dataset_dir, dataList, output_dir, path_to_androidjar,
               path_to_unuglifyDEX, path_to_nice2predict, enable_compare, featurePara=""):
    # clear
    print "apk list:"
    print dataList

    output_dir = os.path.abspath(output_dir)
    path_to_unuglifyDEX = os.path.abspath(path_to_unuglifyDEX)
    path_to_nice2predict = os.path.abspath(path_to_nice2predict)

    r = os.system("rm -rf %s/UnuglifyDex_PREDICT*/" % output_dir)
    if r != 0:
        print "rm failed"
        sys.exit(r)
    time.sleep(2)
    sdkPara = '-sdk %s' % path_to_androidjar

    pwd = os.popen('pwd').read().split('\n')[0]

    print "starting nice2server"
    os.chdir(path_to_nice2predict)
    server_args = ["bin/server/nice2server", "-logtostderr", "-graph_loopy_bp_passes", "0", "-v", "2"]
    serverP = subprocess.Popen(server_args, stderr=subprocess.PIPE)
    read_until(serverP.stderr, "started")
    print "nice2server started"
    os.chdir(pwd)

    apkList = map(lambda x: dataset_dir + '/' + x, dataList)
    if enable_compare:
        apkList = map(lambda x: dataset_dir + '/' + x + '/app-release.apk', dataList)

    totalNum = len(apkList)
    iCount = 0

    print 'Predicting...'
    for apk in apkList:
        print(str(iCount + 1) + '/' + str(totalNum))
        print apk

        (retVal, dexLog) = commands.getstatusoutput("java -jar %s -i %s -o %s %s %s" %
                                                    (path_to_unuglifyDEX, apk, output_dir, sdkPara, featurePara))
        print retVal, dexLog
        
        resultMapPath = os.popen('ls %s/UnuglifyDex_PREDICT*/mapping.txt' % output_dir).read().split('\n')[0]
        os.system('cp %s %s/predict_mapping_%s.txt' % (resultMapPath, output_dir, dataList[iCount]))

        if enable_compare:
            originMapPath = dataset_dir + '/' + dataList[iCount] + '/mapping.txt'
            
            os.system('python mapping_compare.py --proguard %s --predict %s -o %s' %
                      (originMapPath, resultMapPath, output_dir))
            os.system('cp %s %s/proguard_mapping_%s.txt' % (originMapPath, output_dir, dataList[iCount]))
            
            os.system('mv %s/compare_report.txt %s/prediction_report_%s.txt' %
                      (output_dir, output_dir, dataList[iCount]))
            
            os.system('rm %s/predict_result.txt' % output_dir)
            os.system('rm %s/proguard_result.txt' % output_dir)

        os.system('rm -rf %s/UnuglifyDex_PREDICT*' % output_dir)

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


def read_app_list(app_list_file):
    f = open(app_list_file, 'r')
    return f.read().split()

def run(dataset_dir, output_dir, app_list_file, enable_compare,
        path_to_unuglifyDEX, path_to_nice2predict, path_to_androidjar):
    app_list = read_app_list(app_list_file)
    os.system('rm -rf %s' % output_dir)
    os.system('mkdir %s' % output_dir)

    runPredict(dataset_dir, app_list, output_dir, path_to_androidjar,
               path_to_unuglifyDEX, path_to_nice2predict, enable_compare)


def parse_args():
    """
    parse command line input
    generate options including host name, port number
    """
    parser = argparse.ArgumentParser(description="run deobfuscation of apps")
    parser.add_argument("-i", action="store", dest="dataset_dir",
                        required=True, help="directory of apks")
    parser.add_argument("-o", action="store", dest="output_dir",
                        required=True, help="directory of output")
    parser.add_argument("-a", action="store", dest="app_list_file",
                        required=True, help="app list file, in which each app name is a line")
    parser.add_argument("-p", action="store", dest="path_to_unuglifyDEX",
                        required=True, help="path to unuglifyDEX.jar")
    parser.add_argument("-s", action="store", dest="path_to_nice2predict",
                        required=True, help="path to nice2predict root")
    parser.add_argument("-sdk", action="store", dest="path_to_androidjar",
                        required=True, help="path to android.jar")
    parser.add_argument("-enable_compare", action="store_true", dest="enable_compare",
                        help="enable comparing with original version. If true, each app should be a dir containing app-release.apk, app-debug.apk, and mapping.txt")
    options = parser.parse_args()
    print options
    return options


def main():
    """
    the main function
    """
    opts = parse_args()

    run(
        opts.dataset_dir,
        opts.output_dir,
        opts.app_list_file,
        opts.enable_compare,
        opts.path_to_unuglifyDEX,
        opts.path_to_nice2predict,
        opts.path_to_androidjar)

    return


if __name__ == "__main__":
    main()
