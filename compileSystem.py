#!/usr/bin/env python
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#
#				   -=-=-=-=-=-=-=-=-=-
#				   - Compile System  -
#			 	   -=-=-=-=-=-=-=-=-=-
#
#       Compile, Evaluate and Debug C/C++ Programs
# 		   	  Author:Saul de Nova Caballero
#
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Global constants
VERSION = "0.5"
POSSIBLEFILEOUTEND = [".out", ".sol"]

# IMPLEMENT no fork()
# Check intro names with special characters
# Check for modifications in original code(change make behavior)

import os
import re
import resource
import subprocess
import signal
import time
from fnmatch import filter
from sys import stdout, stderr
from optparse import OptionGroup, OptionParser

# ASCII color codes for printing in terminal
class bcolors:
	HEADER = "\033[1;95m"
	OKBLUE = "\033[94m"
	OKGREEN = "\033[92m"
	WARNING = "\033[93m"
	FAIL = "\033[91m"
	DEBUG = "\033[37m"
	ENDC = "\033[0m"

	def disable(self):
		self.HEADER = ""
		self.OKBLUE = ""
		self.OKGREEN = ""
		self.WARNING = ""
		self.FAIL = ""
		self.ENDC = ""
    
# Object declaration for bcolors
bcolorsObject = bcolors()

def stringSplitByNumbers(x):
    r = re.compile("(\d+)")
    l = r.split(x)
    return [int(y) if y.isdigit() else y for y in l]
		
def routeSpecified(strg, search=re.compile(r"[^A-Za-z0-9.]").search): 
	"""
	Check if a string has only alphanumeric values, used for finding if a program has a path specified
	"""
	return bool(search(strg))

def TrueXor(*args):
	return sum(args)<=1

def locate(pattern, root=os.curdir):
    """Locate all files matching supplied filename pattern in and below
    supplied root directory."""
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in filter(files, pattern):
            yield os.path.join(path, filename)

def killProcess(sign, frame):
	stdout.write(bcolorsObject.ENDC);
	stderr.write(bcolorsObject.ENDC);
	os.killpg(os.getpgrp(), signal.SIGTERM)
	os.exit(0)

def compileSource(sourceFile, verbose=True, optimized=True):
	"""
	Compile the source file provided by the parser
	sourceFile is a string to the path of the file to be compiled
	verbose specifies if the code is to print the warning and error messages
	optimized adds the -O2 flag to the compiler
	returns the name of the executable file. It is compiled in the current directory(os.currdir)
	if an error was encountered, returns ""
	"""
	# Check if source exists
	try:
		open(sourceFile, "r")
	except IOError as e:
		print(bcolorsObject.FAIL + "File %s does not exist" % (sourceFile) + bcolorsObject.ENDC, file=stderr)
		return ""
	
	# Check for file extension and set the correct compiler
	fileName, extension = os.path.splitext(sourceFile)
	if extension==".cpp":
		compiler="g++"
	elif extension==".c":
		compiler="gcc"
	else:
		print(bcolorsObject.FAIL + "Error: Unknown file extension of %s" % (sourceFile) + bcolorsObject.ENDC, file = stderr)
		return ""
	
	# Open the make configuration file
	optimization = ""
	if(optimized):
		optimization = "-O2"
	makeFile = open(".makeFile", "w")
	print("all:\n\t %s -g %s -o %s %s" % (compiler, sourceFile, fileName, optimization), file = makeFile)
	makeFile.close()
	
	# Call make
	compileLog = open(".compile.log", "w")
	subprocess.call(["make", "-f", ".makeFile"], stdout = compileLog, stderr = compileLog)
	compileLog.close();
	
	# If make returned an error
	if "error" in open(".compile.log").read() or "ld returned" in open(".compile.log").read():
		print(bcolorsObject.FAIL + "Compilation error for %s\nThe error was:" % (sourceFile) + bcolorsObject.ENDC, file = stderr)
		subprocess.call(["echo", "-ne", bcolorsObject.DEBUG])
		subprocess.call(["cat", ".compile.log"])
		subprocess.call(["echo", "-ne", bcolorsObject.ENDC])
		return ""
	
	# If make returned a warning
	elif "warning" in open(".compile.log").read() and verbose:
		print(bcolorsObject.WARNING + "Warning error for %s\nThe warning was:" % (sourceFile) + bcolorsObject.ENDC, file = stderr)
		subprocess.call(["echo", "-ne", bcolorsObject.DEBUG])
		subprocess.call(["cat", ".compile.log"])
		subprocess.call(["echo", "-ne", bcolorsObject.ENDC])
	
	# Check if output file exists
	try:
		open(fileName, "r");
	except IOError as e:
		print(bcolorsObject.FAIL + "Error ocurred during compilation\nThis error is unknown" + bcolorsObject.ENDC, file = stderr)
		return ""
	
	subprocess.call(["chmod", "+x", fileName]) #Make file executable
	print(bcolorsObject.HEADER + "Compilation success of %s" % (fileName) + bcolorsObject.ENDC)
	return fileName

#Global variables for child process limit
MAXTIME=1.0
MAXMEMBYTES=64*1024*1024
MAXSTACK=""

def processLimit():
	try:
		resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
	except ValueError:
		stderr.write(bcolorsObject.FAIL + "Limit NPROC specified is invalid\n" + bcolorsObject.ENDC)
	try:
		if(MAXSTACK=="UNLIMITED") :
			resource.setrlimit(resource.RLIMIT_STACK, (RLIM_INFINITY, RLIM_INFINITY))
	except ValueError:
		stderr.write(bcolorsObject.FAIL + "Limit STACK specified is invalid\n" + bcolorsObject.ENDC)
	try:
		resource.setrlimit(resource.RLIMIT_CPU, (MAXTIME, MAXTIME))
	except ValueError:
		stderr.write(bcolorsObject.FAIL + "Limit TIME specified is invalid\n" + bcolorsObject.ENDC)
	try:
		resource.setrlimit(resource.RLIMIT_AS, (MAXMEMBYTES, MAXMEMBYTES))
	except ValueError:
		stderr.write(bcolorsObject.FAIL + "Limit MEMORY specified is invalid\n" + bcolorsObject.ENDC)
		
def evaluate(sourceFile, currentDirectory, maximumTime=1, verbose=False, 
			 ioiMode=False, memory=64, noOuts=False, multipleSolutions=False, alternateValues=""):
	"""
	Evaluate the source file with the .in cases found in currentDirectory
	By default the maximum time is the time for the program to be evaluated
	Verbose mode is true by default, if set to false, the program will only print errors and the end results
	ioiMode allows an infinite stack only to be limited by memory
	memory is the maximum size for the virtual memory
	noOuts only checks the program for Runtime Errors and Time Limit Exceeded not evaluating the result for each case
	multipleSolutions is similar to noOuts, only it check for a substring in the output file
	alternateValues is a specialized mode if some cases are worth more than others
	"""
	# Global limits variables specified
	global MAXMEMBYTES, MAXTIME, MAXSTACK
	MAXTIME, MAXMEMBYTES = maximumTime, memory*1024*1024
	if ioiMode:
		MAXSTACK="UNLIMITED"

	# Initialization of local variables
	total, testCases, totalTime = 0, 0, 0
	executable, extension = os.path.splitext(sourceFile)

	# Open a loging file for the errors
	try:
		cslog = open(".cslog", "a")
	except IOError:
		print(bcolorsObject.FAIL + "Will not log errors\n" + bcolorsObject.ENDC, file = stderr)
		return

	# If specified, load the alternate values table
	if alternateValues != "":
		try:
			open(alternateValues, "r")
		except IOError:
			print(bcolorsObject.FAIL + "Failed to open table\n" + bcolorsObject.ENDC, file = stderr)
			alternateValues = ""
	
	# For each *.in* file found in the working directory sort the files
	for fileInAddr in sorted(locate("*.in*", currentDirectory), key=stringSplitByNumbers):
		#Search if file exists
		try:
			fileIn = open(fileInAddr, "r")
		except IOError:
			print("Failed to open file %s" % (fileInAddr), file = cslog)
			continue

		#Check fileOutAddr file exists
		if not noOuts:
			for posibleEnding in POSSIBLEFILEOUTEND:
				fileOutAddr = fileInAddr.replace(".in", posibleEnding)
				try:
					fileOut = open(fileOutAddr, "r")
				except IOError:
					if posibleEnding == POSSIBLEFILEOUTEND[-1]:
						print("Failed to open file %s" % (fileOutAddr), file = cslog)
						continue

		# If no alternate table has been loaded augment the number of test cases
		if alternateValues == "":
			testCases += 1

		#Obtain the case number from the fileInAddr name 
		caseNumber = fileInAddr.replace(os.path.dirname(fileInAddr), "")
		caseNumber = re.sub(r"[^0-9]", "", caseNumber);

		#Read values from table if specified
		value=1
		if alternateValues!="" :
			try:
				value = float(fileValues.readline())
			except ValueError:
				print(bcolorsObject.FAIL + "Invalid value from table\nTERMINATING" + bcolorsObject.ENDC, file = stderr)
				break
		
		# fileOut opens a temporary file in the current directory for the stdout to be redirected
		fileTemporaryOut = open("cs.out", "w")
		if not routeSpecified(executable):
			executable="./"+executable;
		
		# Start the program evaluation. timeStart and timeUsed are used to determine how much the program took
		timeStart = time.time()
		evaluationSubprocess = subprocess.Popen(executable, stdin=fileIn, stdout=fileTemporaryOut, preexec_fn=processLimit)
		evaluationSubprocess.wait()
		evaluationReturnCode = evaluationSubprocess.returncode
		timeUsed = time.time() - timeStart

		# Now the .in file is no longer needed
		fileIn.close()
		# Also close the temporary out file so that it can be read
		fileTemporaryOut.close()

		# Check if in the execution an error was found.
		caseStatus = ""
		if timeUsed > maximumTime:
			caseStatus = "TLE"
		elif int(evaluationReturnCode)!=0:
			if int(evaluationReturnCode)==-9:
				caseStatus = "MLE"
			else:
				caseStatus = "RTE"

		# If execution errors were found, send the correct exit code
		totalTime += float(timeUsed);
		if caseStatus != "":
			if caseStatus == "TLE":
				totalTime += float(maximumTime - timeUsed);
			if verbose:
				print(bcolorsObject.FAIL + "CASE %s:%s\t\t" % (caseNumber, caseStatus) +
					  bcolorsObject.OKBLUE + "TIME ELAPSED: %.02f" % (float(timeUsed)) + bcolorsObject.ENDC)
			continue

		# Converts the output of the program to a string
		strOutput=""
		if not noOuts:
			strOutput = fileOut.read()
			fileOut.close()

		# Opens the output file from the program to 
		try:
			fileTemporaryOut = open("cs.out", "r")
		except IOError:
			print("Error opening cs.out", file = cslog)
			continue
		strOwnProgram = fileTemporaryOut.read()
		fileTemporaryOut.close()

		# Use regex sub to remove all whitespace from the string
		strOwnProgram = re.sub(r'\s', '', strOwnProgram)
		strOutput = re.sub(r'\s', '', strOutput)
		
		# Check if the result from the case is wrong or right
		if (multipleSolutions and strOwnProgram in strOutput) or strOwnProgram == strOutput or noOuts: #If output file string is in the case string
			colorOut = bcolorsObject.OKGREEN
			caseStatus = "OK"
			if noOuts or multipleSolutions:
				caseStatus = "NP"
			total+=value
		else: #If not case is wrong
			colorOut = bcolorsObject.FAIL
			caseStatus = "WA"

		# If verbose mode
		if verbose:
			print(colorOut + "CASE %s:%s\t\t" % (caseNumber, caseStatus) +
				  bcolorsObject.OKBLUE + "TIME ELAPSED: %.2f" % (float(timeUsed)) + bcolorsObject.ENDC)
		
	if testCases > 0 or alternateValues:
		if alternateValues == "":
			total = total*100/testCases
		if verbose:
			print(bcolorsObject.HEADER + "TOTAL SCORE: %d\t\t" % (total) +
				  bcolorsObject.HEADER + "TOTAL TIME ELAPSED: %.2f" % (totalTime) + bcolorsObject.ENDC)
		else:
			print(total)
	else:
		print(bcolorsObject.FAIL + "Error: Could not find test cases for %s" % (sourceFile) + bcolorsObject.ENDC)

def parseExpressions():
	"""
	Function that implements the parsing of expressions with python module optparse
	Returns the list of the parsed options and the remaining args of the expression
	"""
	# Parser object declaration
	parser = OptionParser(usage = "%prog [OPTION]... [FILE]...", 
						  version = "%prog " + str(VERSION), 
						  description = "Compile, evaluate and debug C/C++ programs")

	# Running the parser
	parser.add_option("-g", "--compile", 
					  action = "store_true", dest = "compile", default = False,
					  help = "If necessary compiles the SOURCE", metavar = "SOURCE")
	parser.add_option("-d", "--debug", 
					  action = "store_true", dest = "debug", default = False,
					  help = "Starts the gdb debugger")
	parser.add_option("-r", "--test", 
					  action = "store_true", dest = "test", default = False,
					  help = "RUNS times runs the program")
	parser.add_option("-e", "--evaluate", 
					  action = "store_true", dest = "evaluate", default = False,
					  help = "Evaluates the code with the test cases found in DIR")

	# Miscellaneous utils
	miscellaneousUtils = OptionGroup(parser, "Miscellaneous utilities")
	miscellaneousUtils.add_option("--output-file",
					  action = "store_true", dest = "stdoutRedirection", default = False,
					  help = "Pipes all std output STDOUT to csout.log and STDERR to cserr.log")
	miscellaneousUtils.add_option("-c", "--copy",
					  action = "store", type = "string", dest = "copyFile", default = "",
					  help = "Copies the contents of file SOURCE to the X11 clipboard", metavar = "SOURCE")
	miscellaneousUtils.add_option("--no-optimize",
					  action = "store_false", dest = "optimize", default = True,
					  help = "Sets the -O2 option in the C/C++ compiler. It is true by default")
	miscellaneousUtils.add_option("--no-compile",
					  action = "store_true", dest = "noCompile", default = False,
					  help = "Forces the program to not compile the source file. It is false by default")
	miscellaneousUtils.add_option("--disable-colors",
					  action = "store_false", dest = "terminalColors", default = True,
					  help = "Disables the output colors. Is True by default")
	parser.add_option_group(miscellaneousUtils)

	# Testing utils
	testingUtils = OptionGroup(parser, "Testing utilities")				  
	testingUtils.add_option("-n", "--runs", 
					  action = "store", type = "int", dest = "testingTimes", default = 10,
					  help = "Changes the number of RUNS. By default RUNS is 10", metavar = "RUNS")
	parser.add_option_group(testingUtils)

	# Evaluation utils
	evaluationUtils = OptionGroup(parser, "Evaluation utilies")
	evaluationUtils.add_option("-w", "--directory",
					  action = "store", type = "string", dest = "workingDirectory", default = ".",
					  help = "Changes the working directory DIR. By default DIR is \".\"", metavar = "DIR")
	evaluationUtils.add_option("-t", "--time",
					  action = "store", type = "float", dest = "evaluationTime", default = 1,
					  help = "Defines TIME during the program can be evaluated. Is 1 by default", metavar = "TIME")
	evaluationUtils.add_option("-m", "--memory",
					  action = "store", type = "int", dest = "totalMemory", default = 64,
					  help = "Defines maximum MEMORY available for the program during evaluation. Is 64MB by default", metavar = "MEMORY")
	evaluationUtils.add_option("--no-verbose",
					  action = "store_false", dest = "verbose", default = True,
					  help = "Disables detailed output for evaluation. If not enables only prints total")
	evaluationUtils.add_option("--no-output-files",
					  action = "store_true", dest = "noOuts", default = False,
					  help = "Makes evaluator check only for TLE and MLE")
	evaluationUtils.add_option("--multiple-solutions",
					  action = "store_true", dest = "multipleSolutions", default = False,
					  help = "Changes evaluation to consider mutliple solutions")
	evaluationUtils.add_option("--alternate-values",
					  action = "store", type = "string", dest = "alternateValues", default = "",
					  help = "Allows to load an alternate points table", metavar = "POINTS TABLE")
	evaluationUtils.add_option("--new-ioi-mode",
					  action = "store_true", dest = "ioiMode", default = False,
					  help = "Enables new IOI rules mode for evaluation of cases and unlimited stack size")
	parser.add_option_group(evaluationUtils)

	#optcomplete.autocomplete(parser)
	return parser.parse_args()


def main():
	"""
	Main entrance to the program if called as a script. Overrides SIGINT behavior, parses the input and
	decides the correct options
	"""
	#TODO Check if terminal has color support

	# Override SIGINT Ctrl^C behavior
	signal.signal(signal.SIGINT, killProcess); 

	# Expresion parsing
	(options, args) = parseExpressions()

	# Stdout redirection
	if options.stdoutRedirection:
		stdout = open("csout.log", "w")
		stderr = open("cserr.log", "w")

	# If no terminal colors
	if not options.terminalColors:
		bcolorsObject.disable()

	# Check if more than one option is used
	if not TrueXor(options.compile, options.debug, options.test, options.evaluate):
		print(bcolorsObject.FAIL + "More than one core option was used\nKilling process" + bcolorsObject.ENDC, file = stderr)
		return

	# Copy file to clipboard option
	if options.copyFile != "":
		try:
			open(options.copyFile, "r")
		except IOError:
			print(bcolorsObject.FAIL + "Error: Could not find file for copying" + bcolorsObject.ENDC, file = stderr)
		else:
			os.system("cat " + options.copyFile + " | xclip -selection c")	

	# Execute options
	for sourceFile in args:
		#Check if sourceFile exists
		try:
			open(sourceFile, "r")
		except IOError as e:
			print(bcolorsObject.FAIL + "Error: File %s does not exist" % (str(sourceFile)) + bcolorsObject.ENDC, file = stderr)
			continue
		
		#Compiling options
		if options.compile or not options.noCompile:
			executable = compileSource(sourceFile, options.verbose, options.optimize)
		
		if executable == "":
			continue

		if options.debug: #Debug
			subprocess.call(["echo", "-ne", bcolorsObject.DEBUG])
			subprocess.call(["gdb", "-q", executable])
			subprocess.call(["echo", "-ne", bcolorsObject.ENDC])
		elif options.test: #Test
			for i in range(options.testingTimes): #Run the program testingTimes
				print(bcolorsObject.DEBUG + "Testing %s: %s times" % (str(executable), str(options.testingTimes - i)) + bcolorsObject.ENDC)
				subprocess.call(["./" + executable]); 
		elif options.evaluate: #Evaluate
			evaluate(sourceFile, options.workingDirectory, options.evaluationTime, options.verbose, 
					 options.ioiMode, options.totalMemory, options.noOuts, options.multipleSolutions, options.alternateValues)


if __name__ == "__main__" :
	main() # Call to the main function

