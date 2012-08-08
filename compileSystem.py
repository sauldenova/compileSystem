#!/usr/bin/python
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
#				 -=-=-=-=-=-=-=-=-=-
#				 - Compile System  -
#				 -=-=-=-=-=-=-=-=-=-
#
#     Compile, Evaluate and Debug C/C++ Programs
# 			Author:Saul de Nova Caballero
#
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

import fnmatch
import os
import re
import resource
import subprocess
import signal
import sys
import time
from optparse import OptionGroup, OptionParser

class bcolors:
	HEADER = '\033[1;95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	DEBUG = '\033[37m'
	ENDC = '\033[0m'

	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.ENDC = ''
    
    
def stringSplitByNumbers(x):
    r = re.compile('(\d+)')
    l = r.split(x)
    return [int(y) if y.isdigit() else y for y in l]
		
#Check if a string has search values
def specialMatch(strg, search=re.compile(r'[^A-Za-z0-9.]').search): 
	return bool(search(strg))

def TrueXor(*args):
	return sum(args)<=1

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def compileSource(sourceFile, verbose, optimized):
	'''Compile the source file provided by the parser'''
	#Check if source exists
	try:
		open(sourceFile, 'r')
	except IOError as e:
		sys.stderr.write(bcolors.FAIL + 'FILE ' + sourceFile + ' DOES NOT EXIST\n' + bcolors.ENDC)
		return ""
	
	#Check for file extension and set the correct compiler
	fileName, extension=os.path.splitext(sourceFile)
	if extension==".cpp":
		compiler="g++"
	elif extension==".c":
		compiler="gcc"
	else:
		sys.stderr.write(bcolors.FAIL + 'ERROR: UNKNOWN SOURCE FILE EXTENSION WITH ' + sourceFile + '\n' + bcolors.ENDC)
		return ""
	
	#Open the make configuration file
	optimization=""
	if(optimized):
		optimization=" -O2"
	makeFile=open('.makeFile', 'w')
	makeFile.write('all:\n\t' + compiler + ' -g ' + sourceFile + ' -o ' + fileName + optimization + '\n')
	makeFile.close()
	
	#Call make
	compileLog=open(".compile.log", "w")
	subprocess.call(['make', '-f', '.makeFile'], stdout=compileLog, stderr=compileLog)
	compileLog.close();
	
	#If make returned an error
	if 'error' in open('.compile.log').read() or 'ld returned' in open('.compile.log').read():
		sys.stderr.write(bcolors.FAIL + 'COMPILATION ERROR FOR ' + sourceFile + '\nTHE ERROR WAS:\n' + bcolors.ENDC)
		subprocess.call(['echo', '-ne', bcolors.DEBUG])
		subprocess.call(['cat', '.compile.log'])
		return ""
	
	#If make returned a warning
	elif 'warning' in open('.compile.log').read() and verbose:
		sys.stderr.write(bcolors.WARNING + 'WARNING ERROR FOR ' + sourceFile + '\nTHE WARNING WAS:\n' + bcolors.ENDC)
		subprocess.call(['echo', '-ne', bcolors.DEBUG])
		subprocess.call(['cat', '.compile.log'])
	
	#Check if output file exists
	try:
		open(fileName, 'r');
	except IOError as e:
		sys.stderr.write(bcolors.FAIL + 'COMPILATION ERROR UNKNOWN\nPLEASE REPORT THIS ERROR\n' + bcolors.ENDC)
		return ""
	
	subprocess.call(['chmod', '+x', fileName]) #Make file executable
	sys.stdout.write(bcolors.HEADER + 'COMPILATION SUCCESS OF ' + fileName + '\n' + bcolors.ENDC)
	return fileName

MAXTIME=1
MAXMEMBYTES=64*1024*1024
MAXSTACK=""
def processLimit():
	try:
		resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
	except ValueError:
		sys.stderr.write(bcolors.FAIL + 'Limit NPROC specified is invalid\n' + bcolors.ENDC)
	try:
		if(MAXSTACK=="UNLIMITED") :
			resource.setrlimit(resource.RLIMT_STACK, (RLIM_INFINITY, RLIM_INFINITY))
	except ValueError:
		sys.stderr.write(bcolors.FAIL + 'Limit STACK specified is invalid\n' + bcolors.ENDC)
	try:
		resource.setrlimit(resource.RLIMIT_CPU, (MAXTIME, MAXTIME))
	except ValueError:
		sys.stderr.write(bcolors.FAIL + 'Limit TIME specified is invalid\n' + bcolors.ENDC)
	try:
		resource.setrlimit(resource.RLIMIT_AS, (MAXMEMBYTES, MAXMEMBYTES))
	except ValueError:
		sys.stderr.write(bcolors.FAIL + 'Limit MEMORY specified is invalid\n' + bcolors.ENDC)


		
def evaluate(sourceFile, currentDirectory, maximumTime, verbose, ioiMode, memory, noOuts, multipleSolutions, alternateValues):
	'''Evaluate the source file with the .in cases found in dir'''
	total=0
	testCases=0
	totalTime=0.0;
	executable, extension = os.path.splitext(sourceFile)

	try:
		open(alternateValues, "r")
	except IOError:
		if(alternateValues!=""):
			sys.stderr.write(bcolors.FAIL + 'Failed to open table\n' + bcolors.ENDC);
		alternateValues=""
	
	if(alternateValues!=""):
		fileValues=open(alternateValues, "r")

	try:
		cslog=open('.cslog', 'w')
	except IOError:
		sys.stderr.write(bcolors.FAIL + 'ABANDON THE SHIP\n' + bcolors.ENDC);
		return
	#For each *.in* file found in the working directory sort the files
	for IN in sorted(locate("*.in*", currentDirectory), key = stringSplitByNumbers):
		#Search if file exists
		try:
			fileIn=open(IN, "r")
		except IOError:
			continue

		#Check OUT file exists
		OUT=IN.replace(".in", ".out")
		if not noOuts:
			try:
				fileOut=open(OUT, "r")
			except IOError:
				OUT=IN.replace(".in", ".sol")
				try:
					fileOut=open(OUT, "r")
				except IOError:
					continue

		if(alternateValues==""):
			testCases+=1

		#Obtain the case number from the IN name 
		caseNumber=IN.replace(os.path.dirname(IN), "")
		caseNumber=re.sub(r'[^0-9]', '', caseNumber);

		#Read values from table if specified
		value=1
		if(alternateValues!=""):
			try:
				value=float(fileValues.readline())
			except ValueError:
				sys.stderr.write(bcolors.FAIL + 'Invalid value from table\nTERMINATING' + bcolors.ENDC)
				break
		
		filecs=open('/tmp/cs.out', 'w')
		#Execute the process
		#ulimit kills the process if it uses more than the given time
		#Uses time for taking the time of the process
		#The output is stored in temporal.out file	
		global MAXMEMBYTES
		global MAXTIME
		MAXTIME=maximumTime
		MAXMEMBYTES=memory*1024*1024
		if ioiMode:
			global MAXSTACK
			MAXSTACK="UNLIMITED"
		if not specialMatch(executable):
			executable="./"+executable;
		
		timeStart=time.time()
		subprocessState=subprocess.Popen(executable, stdin=fileIn, stdout=filecs, preexec_fn=processLimit)
		subprocessState.wait()
		timeP=time.time()-timeStart
		timePrint='%.2f' % timeP

		fileIn.close()
		filecs.close()
		if timeP>maximumTime:
			if verbose:
				totalTime+=float(maximumTime);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":TLE\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + str(timePrint) + "\n" + bcolors.ENDC)
			continue
		if int(subprocessState.returncode)==-9:
			if verbose:
				totalTime+=float(timePrint);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":MLE\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + str(timePrint) + "\n" + bcolors.ENDC)
			continue
		if int(subprocessState.returncode)!=0:
			if verbose:
				totalTime+=float(timePrint);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":RTE\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + str(timePrint) + "\n" + bcolors.ENDC)
			continue
		#varMemory="ulimit -v " + str(memory*1024) + "; "
		#varStack=""
		#if ioiMode:
			#varStack="ulimit -s unlimited; "
		#if not specialMatch(executable):
			#executable="./"+executable;
		#varTime="ulimit -t " + str(maximumTime) + "; " 
		#globalLimits=varMemory + varStack + varTime
		#memoryError=False
		#try:
			#os.system(globalLimits + "time -o /tmp/cstime " + executable + " < " + IN + " > /tmp/cs.out 2> /tmp/cserror")
		#except MemoryError as e:
			#memoryError=True

		#For comparation of programs that have multiple solutions,
		#this script removes all spaces from files and turns them into strings
		try:
			filecs=open('/tmp/cs.out', 'r')
		except IOError:
			cslog.write('Error opening cs.out\n')
			continue
		filecs1=open('/tmp/cs1.out', 'w')
		subprocess.call(['tr', '-d', '\t\n\r\f'], stdin=filecs, stdout=filecs1)
		filecs.close()
		filecs1.close()
		try:
			temp1=open('/tmp/cs1.out', 'r')
		except IOError:
			cslog.write('Error opening cs1.out\n')
			continue
		str1=temp1.read()
		
		#Converts the output of the program to a string
		str2=""
		if not noOuts:
			filecs2=open('/tmp/cs2.out', "w")
			subprocess.call(['tr', '-d', '\t\n\r\f'], stdin=fileOut, stdout=filecs2)
			filecs2.close()

			try:
				temp2=open('/tmp/cs2.out', 'r')
			except IOError:
				cslog.write('Error opening cs2.out\n')
				continue
			str2=temp2.read()
			temp2.close()
		
		if (multipleSolutions and (str1 in str2))or(str1==str2)or(noOuts): #If output file string is in the case string
			if verbose:
				totalTime+=float(timePrint);
				strOut="OK"
				if noOuts or multipleSolutions:
					strOut="NP"
				sys.stdout.write(bcolors.OKGREEN + "CASE " + caseNumber + ":" + strOut + "\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + str(timePrint) + "\n" + bcolors.ENDC)
			total+=value
		else: #If not case is wrong
			if verbose:
				totalTime+=float(timePrint);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":WA\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + str(timePrint) + "\n" + bcolors.ENDC)
		if not noOuts:
			fileOut.close()
		
	if testCases>0 or alternateValues:
		if verbose:
			endValue=0
			if(alternateValues!=""):
				endValue=total
			else:
				endValue=total*100/testCases
			sys.stdout.write(bcolors.HEADER + "TOTAL: " + str(int(endValue)) + "\t\t")
			sys.stdout.write(bcolors.HEADER + "TOTAL TIME ELAPSED: " + '%.2f' % totalTime + "\n" + bcolors.ENDC)
		else:
			sys.stdout.write(str(total*100/testCases) + "\n")
	else:
		sys.stdout.write(bcolors.FAIL + "ERROR COULD NOT FIND CASES FOR " + sourceFile + "\n" + bcolors.ENDC)

def killProcess(sign, frame):
	sys.stdout.write(bcolors.ENDC);
	sys.stderr.write(bcolors.ENDC);
	os.killpg(os.getpgrp(), signal.SIGTERM)
	os.exit(0)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=MAIN START-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

signal.signal(signal.SIGINT, killProcess);

#PARSER
parser=OptionParser(usage="%prog [OPTION]... [FILE]...", 
					version="%prog 0.1",
					description="Compile, evaluate and debug C/C++ programs")

#RUNNING OPTIONS
parser.add_option("-g", "--compile", 
				  action="store_true", dest="compile", default=False,
				  help="If necessary compiles the SOURCE", metavar="SOURCE")
parser.add_option("-d", "--debug", 
				  action="store_true", dest="debug", default=False,
				  help="Starts the gdb debugger")
parser.add_option("-r", "--test", 
				  action="store_true", dest="test", default=False,
				  help="RUNS times runs the program")
parser.add_option("-e", "--evaluate", 
				  action="store_true", dest="evaluate", default=False,
				  help="Evaluates the code with the test cases found in DIR")

#MISCELLANEOUS UTILS
miscellaneousUtils=OptionGroup(parser, "Miscellaneous utilities")
miscellaneousUtils.add_option("--output-file",
				  action="store_true", dest="stdoutRedirection", default=False,
				  help="Pipes all std output STDOUT to csout.log and STDERR to cserr.log")
miscellaneousUtils.add_option("-c", "--copy",
				  action="store", type="string", dest="copyFile", default="",
				  help="Copies the contents of file SOURCE to the X11 clipboard", metavar="SOURCE")
miscellaneousUtils.add_option("--no-optimize",
				  action="store_false", dest="optimize", default=True,
				  help="Sets the -O2 option in the C/C++ compiler. It is true by default")
miscellaneousUtils.add_option("--no-compile",
				  action="store_true", dest="noCompile", default=False,
				  help="Forces the program to not compile the source file. It is false by default")
parser.add_option_group(miscellaneousUtils)

#TESTING UTILS
testingUtils=OptionGroup(parser, "Testing utilities")				  
testingUtils.add_option("-n", "--runs", 
				  action="store", type="int", dest="testingTimes", default=10,
				  help="Changes the number of RUNS. By default RUNS is 10", metavar="RUNS")
parser.add_option_group(testingUtils)

#EVALUATION UTILS
evaluationUtils=OptionGroup(parser, "Evaluation utilies")
evaluationUtils.add_option("-w", "--directory",
				  action="store", type="string", dest="workingDirectory", default=".",
				  help="Changes the working directory DIR. By default DIR is \'.\'", metavar="DIR")
evaluationUtils.add_option("-t", "--time",
				  action="store", type="int", dest="evaluationTime", default=1,
				  help="Defines TIME during the program can be evaluated. Is 1 by default", metavar="TIME")
evaluationUtils.add_option("-m", "--memory",
				  action="store", type="int", dest="totalMemory", default=64,
				  help="Defines maximum MEMORY available for the program during evaluation. Is 64MB by default", metavar="MEMORY")
evaluationUtils.add_option("--no-verbose",
				  action="store_false", dest="verbose", default=True,
				  help="Disables detailed output for evaluation. If not enables only prints total")
evaluationUtils.add_option("--no-output-files",
				  action="store_true", dest="noOuts", default=False,
				  help="Makes evaluator check only for TLE and MLE")
evaluationUtils.add_option("--multiple-solutions",
				  action="store_true", dest="multipleSolutions", default=False,
				  help="Changes evaluation to consider mutliple solutions")
evaluationUtils.add_option("--alternate-values",
				  action="store", type="string", dest="alternateValues", default="",
				  help="Allows to load an alternate points table", metavar="POINTS TABLE")
evaluationUtils.add_option("--new-ioi-mode",
				  action="store_true", dest="ioiMode", default=False,
				  help="Enables new IOI rules mode for evaluation of cases and unlimited stack size")
parser.add_option_group(evaluationUtils)

#optcomplete.autocomplete(parser)

(options, args)=parser.parse_args()

#CHECK IF MORE THAN ONE OPTION WAS USED
if not TrueXor(options.compile, options.debug, options.test, options.evaluate):
	#print options.compile
	#print options.debug
	#print options.test
	#print options.evaluate
	sys.stderr.write(bcolors.FAIL + "MORE THAN ONE CORE OPTION WAS USED\nKILLING PROCESS\n" + bcolors.ENDC);
	sys.exit()

#STDOUT REDIRECTION
if options.stdoutRedirection:
	sys.stdout=open("csout.log", "w")
	sys.stderr=open("cserr.log", "w")

#CLIPBOARD COPY
if options.copyFile != "":
	os.system("cat " + options.copyFile + " | xclip -selection c")	

#EXECUTE OPTIONS
for sourceFile in args:
	executable, extension=os.path.splitext(sourceFile)

	#Check if sourceFile exists
	try:
		open(sourceFile, "r")
	except IOError as e: #Compile
		sys.stderr(bcolors.FAIL + "ERROR FILE " + str(executable) + "DOES NOT EXIST\n" + bcolors.ENDC);
		continue
	
	#Compiling options
	if options.compile and not options.noCompile:
		compileSource(sourceFile, options.verbose, options.optimize)
		continue
	
	if not options.noCompile:
		compileSource(sourceFile, options.verbose, options.optimize)

	if options.debug: #Debug
		if executable != "":
			subprocess.call(['echo', '-ne', bcolors.DEBUG])
			subprocess.call(['gdb', '-q', executable])
	elif options.test: #Test
		if executable != "": 
			for i in range(1, options.testingTimes+1): #Run the program testingTimes
				sys.stdout.write(bcolors.DEBUG + 'Testing ' + executable + ': ' + str(options.testingTimes-i+1) + ' times\n' + bcolors.ENDC)
				subprocess.call(['./' + executable]); 
	elif options.evaluate: #Evaluate
		if executable != "":
			evaluate(sourceFile, options.workingDirectory, options.evaluationTime, options.verbose, 
					       options.ioiMode, options.totalMemory, options.noOuts, options.multipleSolutions, options.alternateValues)

