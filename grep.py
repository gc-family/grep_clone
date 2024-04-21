from functools import wraps
import sys
import os
import time
import fnmatch
import gzip
import bz2
from colorama import Fore, init
import argparse
import string

init()
totalFiles = 0
success = 0
start = time.time()

__VERSION__ = "<<< File search version 0.1 >>>"


def is_folder(path):
    if os.path.isdir(path):
        return True
    else:
        return False


def red_color(data, change=False):
    if type(data) == str:
        if change:
            data = Fore.YELLOW + data + Fore.RESET
        else:
            return Fore.RED + data + Fore.RESET
        return data
    else:
        return data


def coroutine(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        g = func(*args, **kwargs)
        next(g)
        return g

    return wrapper


@coroutine
def find_files(Opener):
    global totalFiles
    global success
    print(red_color('the file reader already started'))
    while True:
        startDir, pattern = (yield)
        print(red_color('the started folder is : {}'.format(os.path.abspath(startDir)), change=True))
        if is_folder(startDir):
            for root, subDir, fileList in os.walk(startDir):
                for name in fileList:
                    if fnmatch.fnmatch(name, pattern):
                        fullPath = os.path.join(root, name)
                        print(red_color(fullPath))
                        Opener.send(fullPath)
                        success += 1
                    else:
                        totalFiles += 1
        else:
            print('there is no folder with {} folderName'.format(os.path.abspath(startDir)))


@coroutine
def opener(reader):
    while True:
        name = (yield)
        if name.endswith(".gz"):
            f = gzip.open(name)
        elif name.endswith(".bz2"):
            f = bz2.BZ2File(name)
        else:
            f = open(name, 'r')
        reader.send((f, name))


@coroutine
def cat(pattern_checker):
    while True:
        f, name = (yield)
        try:
            lineNumber = 0
            for line in f:
                pattern_checker.send((line, name, lineNumber))
                lineNumber += 1
        except UnicodeDecodeError:
            print(red_color('this is unicodeDecodeError', change=True))


@coroutine
def grep(pattern, Printer):
    while True:
        line, name, lineNumber = (yield)
        if pattern in line:
            Printer.send((line, name, lineNumber))




@coroutine
def printer(resultLog):
    counter = 0
    if resultLog:
        file = open('result.txt','w')
    while True:
        line, fileName, lineNumber = (yield)
        colored_result = red_color('{} '.format(str(counter)), change=True)
        matched = colored_result + ' ' + str(lineNumber) + ' ' + line
        sys.stdout.write(matched)
        if resultLog:
            print(matched,file=file)
        counter += 1


def main(pattern, string_, path,resultLog):
    finder = find_files(opener(cat(grep(string_, printer(resultLog)))))
    finder.send((path, pattern))
    finder.close()
    print('------------successfully closed the finder------------'.upper())
    print(red_color('we have scanned {0} files in {1} seconds and we get {2} success'.
          format(totalFiles, time.time() - start, success),change=True))
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='this simple Sting finder',
        prefix_chars="-+/"
    )
    parser.add_argument("-f", "/f", "--folder",dest='folder',action='store',default=os.getcwd())
    parser.add_argument("-p", "--pattern",dest='pattern',action='store',default='*.txt')
    parser.add_argument("-n", "--name",dest='substring',action='store',default="print")
    parser.add_argument("-w", "--write",dest='write_to_file',action='store_true',default=False)
    parser.add_argument('-v',"--version", action='version',version=string.capwords(__VERSION__))

    argument = parser.parse_args()
    print(argument.write_to_file)

    main(
        argument.pattern,
        argument.substring,
        argument.folder,
        argument.write_to_file
      )
