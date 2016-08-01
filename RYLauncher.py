"""""
Worked as the launcher of the preprocessor
"""""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# File:         hybrid_checker_scanner.py
# Created:      2016-03-01
# Purpose:      Entrance file of the checker
# Author:       Ruiyi-He
# Important notes : This is the scanner which serves for preprocess of my dissertation, I just build my scanner
# ON-TOP-OF the smalisca environment with more details add in and programatically
# Noted that, [-s] means single application, you need to provide extra application name whereas [-c] means composite applications, in this case, make sure
# your file folder in the root path is named as your application name.
from RYScanner import RYScanner
from RYWriter import  RYWriter
import sys
import os
#get the file path and the cmd
appCommand = sys.argv[1]
fileLocation = sys.argv[2]

iccWidget = {}

if appCommand == '-s':
    appName = sys.argv[3]
    parser = RYScanner(fileLocation,'smali')
    parser.startParsing()
    iccWidget[appName] = parser.getICCWidget()
else:
    fileList = os.listdir(fileLocation)
    for line in fileList:
        filepath = os.path.join(fileLocation,line)
        if os.path.isdir(filepath):
            parser = RYScanner(filepath,'smali')
            parser.startParsing()
            iccWidget[line] = parser.getICCWidget()

writer = RYWriter(fileLocation,iccWidget)
writer.packResult()

print 'Scanning finished, result saved at %s' % (fileLocation)



#create the parser and do the parse job/Users/reillyhe/Desktop/HKStudy/Course/Disertation/myCode/testedExample1/Dcomplie
# parser = RYScanner(fileLocation,'smali')
# parser.startParsing()
# for foundedClass in parser.classes:
#     foundedClass.toString()
# print '----------Parsing Finish --------'
# iccWidgets = parser.getICCWidget()
# print '----------ICC Widget---------'
# for targetClass in iccWidgets:
#     print 'Class -> %s' % (targetClass.name)
#     for iccWidget in iccWidgets[targetClass]:
#         print '----- %s' % iccWidget.variableName





