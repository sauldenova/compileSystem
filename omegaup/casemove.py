#!/usr/local/bin/python3

import re, os

def main():
    numFiles = 0
    inRegex = re.compile('^.*\.in\.\d{1,2}$')
    outRegex = re.compile('^.*\.out\.\d{1,2}$')

    for root, dirs, files in os.walk('./'):
        for name in files:
            if inRegex.match(name):
                newName = name.replace('.in', '')
                newName = newName + '.in'
                os.rename(name, newName)
                print(name + ' -> ' + newName)
                numFiles += 1
            elif outRegex.match(name):
                newName = name.replace('.out', '')
                newName = newName + '.out'
                os.rename(name, newName)
                print(name + ' -> ' + newName)
                numFiles += 1

    print('')
    print('Moved ' + str(numFiles) + ' cases')

if __name__ == '__main__':
    main()
