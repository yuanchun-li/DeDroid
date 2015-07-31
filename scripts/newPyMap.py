#
# @Author: YZY
# @Date: 2015.7.31
#

import os
import sys
import argparse
import re

def run(proguard_mappings_dir, predict_mappings_dir, report_path):
	
	proguard_mappings_dir = os.path.abspath(proguard_mappings_dir)
	predict_mappings_dir = os.path.abspath(predict_mappings_dir)
	report_path = os.path.abspath(report_path)

	# for debug use, copying mapping files
	os.system('cp ' + proguard_mappings_dir + ' ' + report_path + '/mappings_proguard.txt')
	os.system('cp ' + predict_mappings_dir + ' ' + report_path + '/mappings_predict.txt')
	
	file_proguard = open(proguard_mappings_dir, 'r');
	strProguard = file_proguard.read()
	file_proguard.close()
	linesProguard = strProguard.split('\n')[:-1]

	file_predict = open(predict_mappings_dir, 'r');
	strPredict = file_predict.read()
	file_predict.close()
	linesPredict = strPredict.split('\n')[:-1]

	file_proguard_newmap = open(report_path + '/proguard_newmap.txt', 'w')
	file_predict_newmap = open(report_path + '/predict_newmap.txt', 'w')

	proguardLen = 0
	predictLen = 0
	
	dictClassPro = {}
	dictClassPre = {}
	dictCheck = {}
	# step1: construct a mapping from obfuscated to non-obfuscated name(1 to 1)
	currClass = '';
	currClassImg = ''
	for line in linesProguard:
		if line[0] == ' ' or line[0] == '\t':
			continue
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			# proguard map: from non-obfuscated obfuscated
			dictClassPro[currClassImg] = currClass
	# step1: construct a mapping from non-obfuscated to obfuscated name(1 to 1)
	for line in linesPredict:
		if line[0] == ' ' or line[0] == '\t':
			continue
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			# predict map: from predicted to obfuscated
			dictClassPre[currClassImg] = currClass

	# step2: generate pattern strings for fields and functions in pro's and pre's
	re_func = re.compile('([^\ ]+)\ ([^\ ]+)\((.*)\)')
	re_field = re.compile('([^\ ]+)\ ([^\ ]+)')

	currClass = ''

	for line in linesProguard:
		if line[0] == '\t' or line[0] == ' ':
			# clear blank
			if line[0] == '\t':
				[origin, obfuscated] = line[1:].split(' -> ')
			else:
				[origin, obfuscated] = line[4:].split(' -> ')

			strMatched = re_func.match(origin)
			
			if strMatched == None:
			
				# is a field
				patternList = re_field.match(origin).groups()
				# expel the same ones
				if patternList[1] != obfuscated:
					proguardLen += 1
					# whether is a obfuscated type. type is in patternList[0]
					idType = dictClassPro[patternList[0]] if dictClassPro.has_key(patternList[0]) else patternList[0]
					# type is in patternList[0], identifier in [1]
					leftStr = currClass + '.' + obfuscated + '/' + idType
					file_proguard_newmap.write(leftStr + ' -> ' + patternList[1] + '\n')
					if dictCheck.has_key(leftStr) == False:
						dictCheck[leftStr] = {'proguard': patternList[1], 'predict': ''}
					# in case...
					else:
						dictCheck[leftStr]['proguard'] = patternList[1]
			else:			
				# is a function
				patternList = re_func.match(origin).groups()
				# expel the same ones
				if patternList[1] != obfuscated:
				#	print patternList[1] + ' -> ' + obfuscated
					proguardLen += 1
					# whether return type is obfuscated
					retType = dictClassPro[patternList[0]] if dictClassPro.has_key(patternList[0]) else patternList[0]

					idType = retType + '('

					# check parameter types
					paraList = patternList[2].split(',')
					if paraList[0] != '':
						for paraType in paraList:
							idType += dictClassPro[paraType] if dictClassPro.has_key(paraType) else paraType
							idType += ','
						idType = idType[:-1]

					idType += ')'
					
					leftStr = currClass + '.' + obfuscated + '/' + idType
					file_proguard_newmap.write(leftStr + ' -> ' + patternList[1] + '\n')
					if dictCheck.has_key(leftStr) == False:
						dictCheck[leftStr] = {'proguard': patternList[1], 'predict': ''}			
					# in case...
					else:
						dictCheck[leftStr]['proguard'] = patternList[1]
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			# expel the same ones
			if currClass != currClassImg:
				currClassImgName = currClassImg.split('.')[-1]
				file_proguard_newmap.write(currClass + ' -> ' + currClassImgName + '\n')

				if dictCheck.has_key(currClass) == False:
					dictCheck[currClass] = {'proguard': currClassImg, 'predict': ''}			
				# in case
				else:
					dictCheck[currClass]['proguard'] = currClassImg

	# step3: check the predict mapping
	for line in linesPredict:
		if line[0] == '\t' or line[0] == ' ':
			# clear blank
			if line[0] == '\t':
				[origin, obfuscated] = line[1:].split(' -> ')
			else:
				[origin, obfuscated] = line[4:].split(' -> ')

			strMatched = re_func.match(origin)
			
			if strMatched == None:
			
				# is a field
				patternList = re_field.match(origin).groups()

				if patternList[1] != obfuscated:
					predictLen += 1
					# whether is a obfuscated type. type is in patternList[0]
					idType = dictClassPre[patternList[0]] if dictClassPre.has_key(patternList[0]) else patternList[0]
					# type is in patternList[0], identifier in [1]
					leftStr = currClass + '.' + obfuscated + '/' + idType
					file_predict_newmap.write(leftStr + ' -> ' + patternList[1] + '\n')
					if dictCheck.has_key(leftStr) == False:
						dictCheck[leftStr] = {'proguard': '', 'predict': patternList[1]}			
					# in case...
					else:
						dictCheck[leftStr]['predict'] = patternList[1]

			else:			
				# is a function
				patternList = re_func.match(origin).groups()
				# expel the same ones
				if patternList[1] != obfuscated:
				#	print patternList[1] + ' -> ' + obfuscated
					predictLen += 1
					# whether return type is obfuscated
					retType = dictClassPre[patternList[0]] if dictClassPre.has_key(patternList[0]) else patternList[0]

					idType = retType + '('

					# check parameter types
					paraList = patternList[2].split(',')
					if paraList[0] != '':
						for paraType in paraList:
							idType += dictClassPre[paraType] if dictClassPre.has_key(paraType) else paraType
							idType += ','
						idType = idType[:-1]

					idType += ')'
					leftStr = currClass + '.' + obfuscated + '/' + idType
					file_predict_newmap.write(leftStr + ' -> ' + patternList[1] + '\n')
					if dictCheck.has_key(leftStr) == False:
						dictCheck[leftStr] = {'proguard': '', 'predict': patternList[1]}			
					# in case...
					else:
						dictCheck[leftStr]['predict'] = patternList[1]

		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			# expel the same ones
			if currClass != currClassImg:
				currClassImgName = currClassImg.split('.')[-1]
				file_predict_newmap.write(currClass + ' -> ' + currClassImgName + '\n')

				if dictCheck.has_key(currClass) == False:
					dictCheck[currClass] = {'proguard': '', 'predict': currClassImg}			
				# in case
				else:
					dictCheck[currClass]['predict'] = currClassImg

	# step4: calc

	TP = 0
	correctTP = 0
	reportFile = open(report_path + '/report.txt', 'w')
	
	proguardRest = 0
	predictRest = 0
	#correctItemsFile = open(report_path + '/correct.txt', 'w')
	#proguardRestFile = open(report_path + '/proguard_rest.txt', 'w')
	#predictRestFile = open(report_path + '/predict_rest.txt', 'w')

	for key in dictCheck.keys():
		if dictCheck[key]['proguard'] == '':
			predictRest += 1
		elif dictCheck[key]['predict'] == '':
			proguardRest += 1
		else:
			TP += 1
			if dictCheck[key]['proguard'] == dictCheck[key]['predict']:
				correctTP += 1

	reportFile.close()
	file_predict_newmap.close()
	file_proguard_newmap.close()
	#correctItemsFile.close()
	#proguardRestFile.close()
	#predictRestFile.close()
	
	print 'TP: ' + str(TP)
	#print 'proguardLen: ' + str(proguardLen)
	print 'correctTP: ' + str(correctTP)
	print 'proguardRest: ' + str(proguardRest)
	print 'predictRest: ' + str(predictRest)
	print 'precision: ' + str(float(correctTP) / (TP + predictRest))
	print 'recall: ' + str(float(correctTP) / (TP + proguardRest))
	# return dictProguard


def parse_args():
	"""
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
	parser = argparse.ArgumentParser(description="comparing proguard-generated and predict mappings")
	parser.add_argument("--proguard", action="store", dest="proguard_mappings_dir",
						required=True, help="directory of proguard-generated mappings file")
	parser.add_argument("--predict", action="store", dest="predict_mappings_dir",
						required=True, help="directory of predict mappings file")
	parser.add_argument("-o", action="store", dest="report_path",
						required=True, help="directory of report file")

	options = parser.parse_args()
	print options
	return options


def main():
	"""
    the main function
    """
	opts = parse_args()
	run(opts.proguard_mappings_dir, opts.predict_mappings_dir, opts.report_path)

	return


if __name__ == "__main__":
	main()
