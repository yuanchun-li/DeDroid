# Fetching INFERs from nice2server using test data.
# Author: YZY
# Date: 2015.7.18

import pyjsonrpc
import json
import sys, getopt

# nice2server's default port number is 5745
port = 5745

opts, args = getopt.getopt(sys.argv[1:], "i:o:p:")

for op, value in opts:
	if op == '-i':
		input_file = value
	elif op == '-o':
		output_file = value
	elif op == '-p':
		port = value


fOpen = open(input_file, 'r')
cRead = fOpen.read()
fOpen.close()

#cREQList = cRead.split('\n')
cREQList = [cRead]

http_client = pyjsonrpc.HttpClient(url = 'http://localhost:' + str(port))

fWrite = open(output_file, 'w')

for cREQ in cREQList:
	if cREQ == '':
		break

	callParaDict = json.loads(cREQ)
	
	inferDict = http_client.call(
		'infer', query = callParaDict['query'], assign = callParaDict['assign']
	)
	inferJSON = json.dumps(inferDict)

	fWrite.write(str(inferJSON).replace(' ', '') + '\n')

fWrite.close()
