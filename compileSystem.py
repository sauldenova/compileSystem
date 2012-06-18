#!/usr/bin/python

#TODO CONTROL-C BEHAVIOR

import fnmatch
import os
import subprocess
import signal
import sys
import re
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


def isNumber(a):
	'''Check if a string is a number'''
	try:
		float(a)
		return True
	except ValueError:
		return False


def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def compileSource(sourceFile, verbose):
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
	makeFile=open('.makeFile', 'w')
	makeFile.write('all:\n\t' + compiler + ' -g ' + sourceFile + ' -o ' + fileName + ' -O2\n')
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

		
def evaluate(sourceFile, currentDirectory, maximumTime, verbose, ioiMode):
	'''Evaluate the source file with the .in cases found in dir'''
	total=0
	testCases=0
	totalTime=0.0;
	executable, extension = os.path.splitext(sourceFile)
	for IN in sorted(locate("*.in*", currentDirectory), key = stringSplitByNumbers) : #For each file that has .in
		OUT=IN.replace(".in", ".out")
		try: #If .out exists
			open(OUT, "r");
		except IOError as e:
			continue
		
		segFault=False
		#Execute the process
		#ulimit kills the process if it uses more than the given time
		#Uses time for taking the time of the process
		#The output is stored in temporal.out file
		varStack=""
		if ioiMode:
			varStack="ulimit -s unlimited; "
		if not specialMatch(executable):
			executable="./"+executable;
		globalLimits=varStack + "ulimit -t " + str(maximumTime) + "; " 
		try:
			os.system(globalLimits + "time -o /tmp/cstime " + executable + " < " + IN + " > /tmp/cs.out 2> /tmp/cserror")
		except MemoryError as e:
			segFault=True
		#For comparation of programs that have multiple solutions,
		#this script removes all spaces from files and turns them into strings
		os.system("tr -d ' \t\n\r\f' < /tmp/cs.out > /tmp/cs1.out") 
		os.system("tr -d ' \t\n\r\f' < " + OUT + " > /tmp/cs2.out")
		
		#Obtain the case number from the IN name 
		caseNumber=IN.replace(os.path.dirname(IN), "")
		caseNumber=re.sub(r'[^0-9]', '', caseNumber);

		#Open the file of strings
		temp1=open('/tmp/cs1.out', 'r')
		temp2=open('/tmp/cs2.out', 'r')
		errorFile=open('/tmp/cserror', 'r')

		str1=temp1.read()
		str2=temp2.read()
		strError=errorFile.read()

		#Find the time used by the program
		timeFile=open('/tmp/cstime', 'r')
		time=timeFile.readline()[0:4]
		if not isNumber(time):
			time=timeFile.readline()[0:4]
		#time=time.replace(".", "")
		
		if (float(time)+0.1)>=float(maximumTime) and not(str1==str2): #If time was exceded
			if verbose:
				totalTime+=float(maximumTime);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":TLE\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + str(maximumTime) + ".00\n" + bcolors.ENDC)
		elif strError != "" or str1 == "" or segFault:
			if verbose:
				totalTime+=float(time);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":RTE\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + time + "\n" + bcolors.ENDC)
		elif str1 in str2: #If output file string is in the case string
			if verbose:
				totalTime+=float(time);
				sys.stdout.write(bcolors.OKGREEN + "CASE " + caseNumber + ":OK\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + time + "\n" + bcolors.ENDC)
			total+=1
		else: #If not case is wrong
			if verbose:
				totalTime+=float(time);
				sys.stdout.write(bcolors.FAIL + "CASE " + caseNumber + ":WA\t\t")
				sys.stdout.write(bcolors.OKBLUE + "TIME ELAPSED: " + time + "\n" + bcolors.ENDC)
		testCases+=1
		
	if testCases>0:
		if verbose:
			sys.stdout.write(bcolors.HEADER + "TOTAL: " + str(total*100/testCases) + "\t\t")
			sys.stdout.write(bcolors.HEADER + "TOTAL TIME ELAPSED: " + str(totalTime) + "\n" + bcolors.ENDC)
		else:
			sys.stdout.write(str(total*100/testCases) + "\n")
	else:
		sys.stdout.write(bcolors.FAIL + "ERROR COULD NOT FIND CASES FOR " + sourceFile + "\n" + bcolors.ENDC)

def signalHandler(signal, frame):
	'''Kill subprocess for testing'''
	sys.stdout.write(bcolors.FAIL + "Subprocess received signal SIGINT stopping testing\n" + bcolors.ENDC)
	os.kill(testingProcess.pid, signal.SIGTERM)

def preexecFunction():
	'''Overwrite the SIGINT signal handler for signalHandler'''
	signal.signal(signal.SIGINT, signalHandler);

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=MAIN START-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

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
				  action="store", type="string", dest="evaluationTime", default=1,
				  help="Defines TIME during the program can be evaluated. Is 1 by default", metavar="TIME")
evaluationUtils.add_option("--no-verbose",
				  action="store_false", dest="verbose", default=True,
				  help="Disables detailed output for evaluation. If not enables only prints total")
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
for file in args:
	try:
		open(file, "r")
	except IOError as e: #Compile
		sys.stderr(bcolors.FAIL + "ERROR FILE " + file + "DOES NOT EXIST\n" + bcolors.ENDC);
	if options.compile:
		compileSource(file, options.verbose)
	elif options.debug: #Debug
		executable=compileSource(file, options.verbose)
		if executable != "":
			subprocess.call(['echo', '-ne', bcolors.DEBUG])
			subprocess.call(['gdb', '-q', executable])
	elif options.test: #Test
		executable=compileSource(file, options.verbose)
		if executable != "": 
			for i in range(1, options.testingTimes+1): #Run the program testingTimes
				sys.stdout.write(bcolors.DEBUG + 'Testing ' + executable + ': ' + str(options.testingTimes-i+1) + ' times\n' + bcolors.ENDC)
				subprocess.call(['./' + executable]); #TODO change Ctrl-C Behavior
	elif options.evaluate: #Evaluate
		executable=compileSource(file, options.verbose)
		if executable != "":
			evaluate(file, options.workingDirectory, options.evaluationTime, options.verbose, options.ioiMode)

