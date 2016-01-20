#!/usr/local/bin/python3

import os, sys

def main():
    basedir = './' + str(sys.argv[1])
    os.mkdir(basedir)
    print('Created: ' + basedir)

    casedir = basedir + '/cases'
    os.mkdir(casedir)
    print('Created: ' + casedir)

    statedir = basedir + '/statements'
    os.mkdir(statedir)
    print('Created: ' + statedir)

    markdown = statedir + '/es.markdown'
    f = open(markdown, 'w')
    f.close()
    print('Created: ' + markdown)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Incorrect argument count')
    else:
        main()
