#
# @Author: YZY
# @Date: 2015.7.28
#

#TODO dictClassPro is not necessary in step 2

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

	UNCHECK_state = 0
	CHECKED_state = 1
	SAME_CLASS = 2

	# build proguard and predict dictionaries
	#proguardLen = len(linesProguard)
	#print str(proguardLen) + ' relevant items in Proguard.'
	# calc later, use incremental way
	proguardLen = 0
	
	#predictLen = len(linesPredict)
	#print str(predictLen) + ' relevant items in prediction.'
	#proguardLen = 0
	predictLen = 0
	
	dictClassPro = {}
	dictClassPre = {}
	mapClassToPatternBlock = {}
	dictPredict = {}

	# step1: construct a mapping from class to obfuscated name(1 to 1)
	currClass = '';
	currClassImg = ''
	for line in linesProguard:
		if line[0] == ' ' or line[0] == '\t':
			continue
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			# proguard map: from obfuscated to non-obfuscated
			dictClassPro[currClass] = currClassImg

	for line in linesPredict:
		if line[0] == ' ' or line[0] == '\t':
			continue
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			# predict map: from predicted to obfuscated
			dictClassPre[currClassImg] = currClass
			#print currClass
			#print currClass + ' <- ' + currClassImg

	# step2: generate pattern strings for fields and functions in pro's and pre's
	re_func = re.compile('([^\ ]+)\ ([^\ ]+)\((.*)\)')
	re_field = re.compile('([^\ ]+)\ ([^\ ]+)')

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
				if patternList[1] == obfuscated:
				#	print patternList[1] + ' -> ' + obfuscated
				#	proguardLen -= 1
					continue;
				else:
					proguardLen += 1
				# whether is a obfuscated type. type is in patternList[0]
				idType = dictClassPro[patternList[0]] if dictClassPro.has_key(patternList[0]) else patternList[0]
				
				# identifier is in patternList[1]
				if mapClassToPatternBlock[currClass]['field'].has_key(obfuscated) == False:
					mapClassToPatternBlock[currClass]['field'][obfuscated] = {idType: {'origin': patternList[1], 'state': UNCHECK_state}}
				else:
					mapClassToPatternBlock[currClass]['field'][obfuscated][idType] = {}
					mapClassToPatternBlock[currClass]['field'][obfuscated][idType]['origin'] = patternList[1]
					mapClassToPatternBlock[currClass]['field'][obfuscated][idType]['state'] = UNCHECK_state

			else:			
				# is a function
				patternList = re_func.match(origin).groups()
				# expel the same ones
				if patternList[1] == obfuscated:
				#	print patternList[1] + ' -> ' + obfuscated
				#	proguardLen -= 1
					continue;
				else:
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

				# identifier is in patternList[1]
				if mapClassToPatternBlock[currClass]['method'].has_key(obfuscated) == False:
					mapClassToPatternBlock[currClass]['method'][obfuscated] = {idType: {'origin': patternList[1], 'state': UNCHECK_state}}
				else:
					mapClassToPatternBlock[currClass]['method'][obfuscated][idType] = {}
					mapClassToPatternBlock[currClass]['method'][obfuscated][idType]['origin'] = patternList[1]
					mapClassToPatternBlock[currClass]['method'][obfuscated][idType]['state'] = UNCHECK_state
			
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			#mapClassToPatternBlock[currClass] = {currClassImg: {'field':{}, 'method':{}}}
			mapClassToPatternBlock[currClass] = {'field':{}, 'method':{}, 'origin': currClassImg, 'state': UNCHECK_state}

	# expel the same classes
	for obfuscatedClass in mapClassToPatternBlock.keys():
		originClass = mapClassToPatternBlock[obfuscatedClass]['origin']
		if originClass == obfuscatedClass:
			mapClassToPatternBlock[obfuscatedClass]['state'] = SAME_CLASS
			#proguardLen -= 1
			#if len(mapClassToPatternBlock[obfuscatedClass][originClass]['field']) == 0:
			#	if len(mapClassToPatternBlock[obfuscatedClass][originClass]['method']) == 0:
					#print obfuscatedClass			
			#		mapClassToPatternBlock.pop(obfuscatedClass)
		else:
			proguardLen += 1


	dictDebug = open(report_path + '/dict.txt', 'w')
	dictDebug.write(str(mapClassToPatternBlock))
	dictDebug.close()

	# step3: check the predict mapping
	TP = 0
	correctTP = 0
	reportFile = open(report_path + '/report.txt', 'w')
	
	proguardRest = 0
	predictRest = 0
	correctItemsFile = open(report_path + '/correct.txt', 'w')
	proguardRestFile = open(report_path + '/proguard_rest.txt', 'w')
	predictRestFile = open(report_path + '/predict_rest.txt', 'w')

	for line in linesPredict:
		if line[0] == '\t' or line[0] == ' ':
			# skip cleared classes
			if mapClassToPatternBlock.has_key(currClass) == False:
				continue
			# clear blank
			if line[0] == '\t':
				[origin, obfuscated] = line[1:].split(' -> ')
			else:
				[origin, obfuscated] = line[4:].split(' -> ')

			strMatched = re_func.match(origin)
			
			if strMatched == None:
			
				# is a field
				patternList = re_field.match(origin).groups()
				# whether is a obfuscated type. type is in patternList[0]
				# first retrieve obfuscated one from dictPre, then use it to check dictPro.
				fieldKey = dictClassPre[patternList[0]] if dictClassPre.has_key(patternList[0]) else patternList[0]
				idType = dictClassPro[fieldKey] if dictClassPro.has_key(fieldKey) else fieldKey
				# identifier is in patternList[1]
				
				if mapClassToPatternBlock[currClass]['field'].has_key(obfuscated) == False:
					# predictRestFile item
					predictRest += 1
					predictRestFile.write('\t' + obfuscated + ' -> ' + obfuscated + ' -> '  + origin + '\n')
					# print 'A non-existing obfuscated identifier: ' + line
				else:
					if mapClassToPatternBlock[currClass]['field'][obfuscated].has_key(idType):
						# we got the right type, but not necessary
						TP += 1
						mapClassToPatternBlock[currClass]['field'][obfuscated][idType]['state'] = CHECKED_state
						reportFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass]['field'][obfuscated][idType]['origin'] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						# non-dicted type that can be retrieved OR obfuscated dicted type
						if mapClassToPatternBlock[currClass]['field'][obfuscated][idType]['origin'] == patternList[1]:
							# the same identifier
							correctTP += 1
							correctItemsFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass]['field'][obfuscated][idType]['origin'] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						else:
							# wrong identifier
							continue
					else:
						# Type re-generation failed. It should not be possible.
						#print currClass
						#print idType
						print 'Type re-generation failed: ' + line
						#print 'Key: ' + fieldKey
						#print 'PatternList[0]: ' + patternList[0]

			else:			
				# is a function
				patternList = re_func.match(origin).groups()
				# whether return type is obfuscated
				#retType = dictClassPro[patternList[0]] if dictClassPro.has_key(patternList[0]) else patternList[0]
				retKey = dictClassPre[patternList[0]] if dictClassPre.has_key(patternList[0]) else patternList[0]
				retType = dictClassPro[retKey] if dictClassPro.has_key(retKey) else retKey

				idType = retType + '('

				# check parameter types
				paraList = patternList[2].split(',')
				if paraList[0] != '':
					for paraType in paraList:
						#idType += dictClassPro[paraType] if dictClassPro.has_key(paraType) else paraType
						paraKey = dictClassPre[paraType] if dictClassPre.has_key(paraType) else paraType
						idType += dictClassPro[paraKey] if dictClassPro.has_key(paraKey) else paraKey
						idType += ','
					idType = idType[:-1]

				idType += ')'
				
				if mapClassToPatternBlock[currClass]['method'].has_key(obfuscated) == False:
					# predictRestFile item
					predictRest += 1
					predictRestFile.write('\t' + obfuscated + ' -> ' + obfuscated + ' -> '  + origin + '\n')
					#print 'A non-existing obfuscated identifier: ' + line
				else:
					if mapClassToPatternBlock[currClass]['method'][obfuscated].has_key(idType):
						# we got the right type, but not necessary
						TP += 1
						mapClassToPatternBlock[currClass]['method'][obfuscated][idType]['state'] = CHECKED_state
						reportFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass]['method'][obfuscated][idType]['origin'] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						# non-dicted type that can be retrieved OR obfuscated dicted type
						if mapClassToPatternBlock[currClass]['method'][obfuscated][idType]['origin'] == patternList[1]:
							# the same identifier
							correctTP += 1
							correctItemsFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass]['method'][obfuscated][idType]['origin'] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						else:
							# wrong identifier
							continue
					else:
						# Type re-generation failed. It should not be possible.
						print 'Type re-generation failed: ' + line

		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]

			currClassName = mapClassToPatternBlock[currClass]['origin'].split('.')[-1]
			currClassImgName = currClassImg.split('.')[-1]

			if mapClassToPatternBlock.has_key(currClass) == False:
				# wrongly judged a class obfuscated
				# or a shell class
				# predictRestFile item
				if currClassName != currClassImgName:
					predictRest += 1
					predictRestFile.write(currClass + ' -> ' + currClass + ' -> '  + currClassImg + '\n')
				continue
			else:
				if mapClassToPatternBlock[currClass]['state'] == SAME_CLASS:
					# predictRestFile item
					#mapClassToPatternBlock[currClass]['state'] = CHECKED_state
					#predictRest += 1
					#predictRestFile.write(currClass + ' -> ' + currClass + ' -> '  + currClassImg + '\n')
					continue

				TP += 1
				mapClassToPatternBlock[currClass]['state'] = CHECKED_state

				#if mapClassToPatternBlock[currClass]['origin'] == currClassImg:
				
					# class name correct
				#print currClassName + ': ' + currClassImgName
				print currClassImg + ': ' + currClass
				if currClassName == currClassImgName:
					correctTP += 1
					reportFile.write(currClassImg + ' -> ' + currClass 
									 + ' -> ' + currClassImg + '\n')
					correctItemsFile.write(currClassImg + ' -> ' + currClass 
									 + ' -> ' + currClassImg + '\n')
				else:
					correctClass = mapClassToPatternBlock[currClass]['origin']
					reportFile.write(correctClass + 
									 ' -> ' + currClass + ' -> ' + currClassImg + '\n')
					# get correct class name
					currClassImg = correctClass

	# step4: find UNCHECKD ones in proguard
	for currClass in mapClassToPatternBlock.keys():
		currClassImg = mapClassToPatternBlock[currClass]['origin']
		#if mapClassToPatternBlock[currClass]['state'] != CHECKED_state:
		if mapClassToPatternBlock[currClass]['state'] == UNCHECK_state:
			proguardRest += 1
			proguardRestFile.write(currClassImg + ' -> ' + currClass + ' -> '  + currClass + '\n')
		for field in mapClassToPatternBlock[currClass]['field'].keys():
			for idType in mapClassToPatternBlock[currClass]['field'][field].keys():
				if mapClassToPatternBlock[currClass]['field'][field][idType]['state'] != CHECKED_state:
					proguardRest += 1
					proguardRestFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass]['field'][field][idType]['origin'] + 
										 ' -> ' + field + ' -> '  + idType + ' ' + field + '\n')
		for method in mapClassToPatternBlock[currClass]['method'].keys():
			for idType in mapClassToPatternBlock[currClass]['method'][method].keys():
				if mapClassToPatternBlock[currClass]['method'][method][idType]['state'] != CHECKED_state:
					proguardRest += 1
					proguardRestFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass]['method'][method][idType]['origin'] + 
										 ' -> ' + method + ' -> '  + idType + ' ' + method + '\n')


	reportFile.close()
	correctItemsFile.close()
	proguardRestFile.close()
	predictRestFile.close()
	
	print 'TP: ' + str(TP)
	print 'proguardLen: ' + str(proguardLen)
	print 'correctTP: ' + str(correctTP)
	print 'proguardRest: ' + str(proguardRest)
	print 'predictRest: ' + str(predictRest)
	print 'precision: ' + str(float(correctTP) / (TP + predictRest))
	print 'precision: ' + str(float(correctTP) / (TP + proguardRest))
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
