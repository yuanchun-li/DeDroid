import os
import sys
import time
import commands
import argparse


def run(apk_dir, output_dir, path_to_unuglifyDEX, apk_limit):
	# clear
	apk_dir = os.path.abspath(apk_dir)
	output_dir = os.path.abspath(output_dir)
	path_to_unuglifyDEX = os.path.abspath(path_to_unuglifyDEX)
	training_file_name = "batTrainJsonList.txt"
	if apk_limit is not None:
		apk_limit = int(apk_limit)

	r = os.system("rm -rf %s/UnuglifyDex_TRAIN*/" % output_dir)
	if r != 0:
		print "rm failed"
		sys.exit(r)
	r = os.system("rm -rf %s/%s" % (output_dir, training_file_name))
	if r != 0:
		print "rm failed"
		sys.exit(r)
	time.sleep(2)

	apkList = os.popen("ls %s/*.apk" % apk_dir).read().split('\n')[:-1]
	sdkPara = '-force-android-jar $ANDROID_SDK_HOME/platforms/android-22/android.jar'

	fJsonList = open("%s/%s" % (output_dir, training_file_name), 'w')
	fJsonList.close()
	totalNum = len(apkList)
	iCount = 1

	for apk in apkList:
		if apk_limit is not None and iCount > apk_limit:
			break
		print(str(iCount) + '/' + str(totalNum))
		iCount = iCount + 1
		(retVal, dexLog) = commands.getstatusoutput("java -jar %s -i %s -o %s -m train %s" %
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

		# os.system('rm -rf %s/UnuglifyDex_TRAIN*' % output_dir)


def parse_args():
	"""
    parse command line input
    generate options including host name, port number
    """
	parser = argparse.ArgumentParser(description="generate training data of apks")
	parser.add_argument("-i", action="store", dest="apk_dir",
						required=True, help="directory of apks")
	parser.add_argument("-o", action="store", dest="output_dir",
						required=True, help="directory of output")
	parser.add_argument("-p", action="store", dest="path_to_unuglifyDEX",
						required=True, help="path to unuglifyDEX.jar")
	parser.add_argument("-l", action="store", dest="apk_limit",
						help="limit of number of training apks")
	options = parser.parse_args()
	print options
	return options


def main():
	"""
    the main function
    """
	opts = parse_args()
	run(opts.apk_dir, opts.output_dir, opts.path_to_unuglifyDEX, opts.apk_limit)
	return


if __name__ == "__main__":
	main()
