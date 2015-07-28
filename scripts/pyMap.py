#
# @Author: YZY
# @Date: 2015.7.28
#

import os
import sys
import argparse
import re

def run(proguard_mappings_dir, predict_mappings_dir, report_path):
	
	proguard_mappings_dir = os.path.abspath(proguard_mappings_dir)
	predict_mappings_dir = os.path.abspath(predict_mappings_dir)
	report_path = os.path.abspath(report_path)
	
	file_proguard = open(proguard_mappings_dir, 'r');
	strProguard = file_proguard.read()
	file_proguard.close()
	linesProguard = strProguard.split('\n')[:-1]

	file_predict = open(predict_mappings_dir, 'r');
	strPredict = file_predict.read()
	file_predict.close()
	linesPredict = strPredict.split('\n')[:-1]

	# build proguard and predict dictionaries
	proguardLen = len(linesProguard)
	print str(proguardLen) + ' relevant items in Proguard.'
	predictLen = len(linesPredict)
	print str(predictLen) + ' relevant items in prediction.'
	
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
				# whether is a obfuscated type. type is in patternList[0]
				idType = dictClassPro[patternList[0]] if dictClassPro.has_key(patternList[0]) else patternList[0]
				
				# identifier is in patternList[1]
				if mapClassToPatternBlock[currClass][currClassImg]['field'].has_key(obfuscated) == False:
					mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated] = {idType: patternList[1]}
				else:
					mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated][idType] = patternList[1]

			else:			
				# is a function
				patternList = re_func.match(origin).groups()
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
				if mapClassToPatternBlock[currClass][currClassImg]['method'].has_key(obfuscated) == False:
					mapClassToPatternBlock[currClass][currClassImg]['method'][obfuscated] = {idType: patternList[1]}
				else:
					mapClassToPatternBlock[currClass][currClassImg]['method'][obfuscated][idType] = patternList[1]
			
		else:
			[currClassImg, currClass] = line.split(' -> ')
			currClass = currClass[:-1]
			mapClassToPatternBlock[currClass] = {currClassImg: {'field':{}, 'method':{}}}

	dictDebug = open('dict.txt', 'w')
	dictDebug.write(str(mapClassToPatternBlock))
	dictDebug.close()

	# step3: check the predict mapping
	TP = 0
	correctTP = 0
	reportFile = open('report.txt', 'w')
	correctItemsFile = open('correct.txt', 'w')

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
				# whether is a obfuscated type. type is in patternList[0]
				# first retrieve obfuscated one from dictPre, then use it to check dictPro.
				fieldKey = dictClassPre[patternList[0]] if dictClassPre.has_key(patternList[0]) else patternList[0]
				idType = dictClassPro[fieldKey] if dictClassPro.has_key(fieldKey) else fieldKey
				# identifier is in patternList[1]
				
				if mapClassToPatternBlock[currClass][currClassImg]['field'].has_key(obfuscated) == False:
					# this should be an impossible case.
					print 'A non-existing obfuscated identifier: ' + line
				else:
					if mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated].has_key(idType):
						# we got the right type, but not necessary
						TP += 1
						correctType = mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated].keys()[0]
						reportFile.write('\t' + correctType + ' ' + 
										 mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated][correctType] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						# non-dicted type that can be retrieved OR obfuscated dicted type
						if mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated][correctType] == patternList[1]:
							# the same identifier
							correctTP += 1
							correctItemsFile.write('\t' + correctType + ' ' + 
										 mapClassToPatternBlock[currClass][currClassImg]['field'][obfuscated][correctType] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						else:
							# wrong identifier
							continue
					else:
						# Type re-generation failed. It should not be possible.
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
				
				if mapClassToPatternBlock[currClass][currClassImg]['method'].has_key(obfuscated) == False:
					# this should be an impossible case.
					print 'A non-existing obfuscated identifier: ' + line
				else:
					if mapClassToPatternBlock[currClass][currClassImg]['method'][obfuscated].has_key(idType):
						# we got the right type, but not necessary
						TP += 1
						reportFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass][currClassImg]['method'][obfuscated][idType] + 
										 ' -> ' + obfuscated + ' -> '  + origin + '\n')
						# non-dicted type that can be retrieved OR obfuscated dicted type
						if mapClassToPatternBlock[currClass][currClassImg]['method'][obfuscated][idType] == patternList[1]:
							# the same identifier
							correctTP += 1
							correctItemsFile.write('\t' + idType + ' ' + 
										 mapClassToPatternBlock[currClass][currClassImg]['method'][obfuscated][idType] + 
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
			if mapClassToPatternBlock.has_key(currClass) == False:
				# wrongly judged a class obfuscated
				continue
			else:
				TP += 1
				if mapClassToPatternBlock[currClass].has_key(currClassImg) == True:
					# class name correct
					correctTP += 1
					reportFile.write(currClassImg + ' -> ' + currClass 
									 + ' -> ' + currClassImg + '\n')
					correctItemsFile.write(currClassImg + ' -> ' + currClass 
									 + ' -> ' + currClassImg + '\n')
				else:
					correctClass = mapClassToPatternBlock[currClass].keys()[0]
					reportFile.write(correctClass + 
									 ' -> ' + currClass + ' -> ' + currClassImg + '\n')
					# get correct class name
					currClassImg = correctClass

	reportFile.close()
	print 'TP: ' + str(TP)
	print 'correctTP: ' + str(correctTP)
	print 'precision: ' + str(float(TP) / float(predictLen))
	print 'recall: ' + str(float(TP) / float(proguardLen))
	print 'predict correct rate: ' + str(float(correctTP) / float(TP))
	# return dictProguard


def parse_args():
	"""
    parse command line input
    generate options including input proguard-generated mappings and predict mappings
    """
	parser = argparse.ArgumentParser(description="comparing proguard-generated and predict mappings")
	parser.add_argument("--proguard", action="store", dest="proguard_mappings_dir", nargs='?',
						required=True, help="directory of proguard-generated mappings file")
	parser.add_argument("--predict", action="store", dest="predict_mappings_dir", nargs='?',
						required=True, help="directory of predict mappings file")
	parser.add_argument("-o", action="store", dest="report_path", nargs='?',
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
