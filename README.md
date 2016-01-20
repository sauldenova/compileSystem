# Compile System

A series of tools that aid in the evaluation, testing and compiling of C++ IOI/ACM style programs

## compileSystem.py

Evaluates C/C++ programs in *nix type environments

Usage: compileSystem.py [OPTION]... [FILE]...

Options:
  version             show program's version number and exit
  help                show this help message and exit
  g, compile          If necessary compiles the SOURCE
  d, debug            Starts the gdb debugger
  r, test             RUNS times runs the program
  e, evaluate         Evaluates the code with the test cases found in DIR

  Miscellaneous utilities:
    output-file         Pipes all std output STDOUT to csout.log and STDERR to
                        cserr.log
    c [SOURCE], copy[SOURCE]
                        Copies the contents of file SOURCE to the X11
                        clipboard
    no-optimize         Sets the -O2 option in the C/C++ compiler. It is true
                        by default
    no-compile          Forces the program to not compile the source file. It
                        is false by default
    disable-colors      Disables the output colors. Is True by default

  Testing utilities:
    n RUNS, runs RUNS
                        Changes the number of RUNS. By default RUNS is 10

  Evaluation utilies:
    w DIR, directory DIR
                        Changes the working directory DIR. By default DIR is
                        '.'
    t TIME, time TIME
                        Defines TIME during the program can be evaluated. Is 1
                        by default
    m MEMORY, memory MEMORY
                        Defines maximum MEMORY available for the program
                        during evaluation. Is 64MB by default
    no-verbose          Disables detailed output for evaluation. If not
                        enables only prints total
    no-output-files     Makes evaluator check only for TLE and MLE
    multiple-solutions
                        Changes evaluation to consider mutliple solutions
    alternate-values POINTS TABLE
                        Allows to load an alternate points table
    new-ioi-mode        Enables new IOI rules mode for evaluation of cases and
                        unlimited stack size
## omegaup/dirgen.py

Generates the default directory structure for uploading OmegaUp problems.

Usage: dirgen.py [DIRECTORY_NAME]

## omegaup/casemove.py

Changes cases from COCI to the correct structure for OmegaUp problems.

Usage: casemove.py

