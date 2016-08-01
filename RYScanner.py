"""""
This class worked as a scanner of the preprocessor
It will scan the smali project in a "Class by Class" manner
"""""
import codecs
import os
import re
from RYModel import *


class RYScanner:

    def __init__(self, location, suffix = 'smali'):
        self.location = location
        self.suffix = suffix
        self.currentWorkingPath = ''
        self.currentClass = None
        self.currentMethod = None
        # flag to illustrate that we are in a method block
        self.inMethodBlock = False
        self.classes = []
        # used for variable tracing, should be updated in a "method by method" manner
        self.variablePool = {}
        self.insideOfSwitchBlock = False
        self.currentSwitchCase = None


    # Trigger method
    def startParsing(self):
        self.walkthrough()

    # Work out the ICC Widget based on DFS manner
    def getICCWidget(self):
        iccWidget = {}
        for foundedClass in self.classes:
            widgetListForCurrentClass = []
            for widget in foundedClass.widgets:
                # for each widget, we need to find out the corresponding onClick trrigger
                # using widget -> dstClass -> onClick
                dstClassName = widget.dstLink
                for targetClass in self.classes:
                    if dstClassName == targetClass.name:
                        onClickMethod = targetClass.searchForOnClickMethod()
                        if onClickMethod:
                            # if this method contains no condition block
                            # then we assume that this onClick method is just used for the current widget
                            relatedMethodCall = None
                            if len(onClickMethod.conditionBlock) == 0:
                                relatedMethodCall = onClickMethod.methodCallingPool
                            else:
                                # then we try to link its condition pool
                                idValue = widget.widgetID.encode('utf-8')
                                switchCase = onClickMethod.isSwitchCaseValueExist(idValue)
                                if switchCase:
                                    relatedMethodCall = onClickMethod.conditionBlock[switchCase]
                                else:
                                    relatedMethodCall = onClickMethod.methodCallingPool
                            if self.containsICCMethodCall(relatedMethodCall):
                                widgetListForCurrentClass.append(widget)
            if len(widgetListForCurrentClass) > 0:
                iccWidget[foundedClass.name] = widgetListForCurrentClass
        return iccWidget

    # Find the ICC method call based on method call in a DFS manner
    def containsICCMethodCall(self, relatedMethodCall):
        import copy
        frontiers = copy.deepcopy(relatedMethodCall)
        while len(frontiers) != 0:
            currentMethodCall = frontiers.pop()
            if currentMethodCall.isICCCalling():
                return True
            # if not, then we should go to the called method to get the successor calls
            dstClassName = currentMethodCall.calleeClassName
            for targetClass in self.classes:
                if targetClass.name == dstClassName:
                    targetMethod = targetClass.searchMethodByName(currentMethodCall.callee)
                    for successorMethodCall in targetMethod.methodCallingPool:
                        frontiers.append(successorMethodCall)
        return False

    # File walk through
    def walkthrough(self):
        for root, dirs, files in os.walk(self.location):
            for f in files:
                # Basically, one smali file = one class
                self.currentClass = None
                if f.endswith(self.suffix):
                    file_path = root + "/" + f

                    # Set current path
                    self.currentWorkingPath = file_path

                    # Parse file
                    self.parsingFile(self.currentWorkingPath)

    # File parsing worker
    def parsingFile(self, filePath):
        with codecs.open(filePath, 'rw', encoding='utf8') as f:
             lines = f.readlines()
             # for index in range(0,len(lines)):
             index = 0
             while index < len(lines):
                l = lines[index]
                # find the class definition
                if '.class' in l:
                    match_class = self.is_class(l)
                    if match_class:
                        current_class = self.extract_class(match_class)
                        self.classes.append(current_class)
                        self.currentClass = current_class
                # find the class var in the current class
                elif '.field' in l:
                    match_class_property = self.is_class_property(l)
                    if match_class_property:
                        widget = self.extract_class_property(match_class_property)
                        if widget:
                            self.currentClass.widgets.append(widget)
                # method definition
                elif '.method' in l:
                    # updated the pool
                    self.variablePool = {'p0':self.currentClass.name}
                    self.inMethodBlock = True
                    match_class_method = self.is_class_method(l)
                    if match_class_method:
                        m = self.extract_class_method(match_class_method)
                        self.currentClass.methods.append(m)
                        self.currentMethod = m
                # end tag of the method
                elif '.end method' in l:
                    self.inMethodBlock = False
                    self.currentMethod = None
                # const def of local var
                elif 'const' in l and self.inMethodBlock:
                    match_const_var = self.is_const_value(l)
                    if match_const_var:
                        self.extract_const_value(match_const_var)
                # method invocation
                elif 'invoke' in l:
                    match_method_call = self.is_method_call(l)
                    if match_method_call:
                        methodCall = self.extract_method_call(match_method_call)
                        self.currentMethod.methodCallingPool.append(methodCall)
                        if methodCall.isFindViewByID():
                            # Add it to the calling stack
                            self.currentMethod.widgetFindViewByIDStack.append(methodCall)
                        if methodCall.isSetOnClickListener():
                            # Find the corresponding widget, and link it with dstLink
                            callingWidgetName = methodCall.iniParam
                            matchedWidget = self.currentClass.searchWidgetByName(callingWidgetName)
                            if matchedWidget:
                                # line the input param with the corresponding widget
                                if len(methodCall.inputParam) > 0:
                                    matchedWidget.dstLink = methodCall.inputParam[0]
                        if self.insideOfSwitchBlock and self.currentSwitchCase:
                            # then we also need to add this invoke into the conditional block
                            if self.currentMethod:
                                self.currentMethod.conditionBlock[self.currentSwitchCase].append(methodCall)
                # field assignment
                elif 'iput-object' in l:
                    match_field_assign = self.is_field_assign(l)
                    if match_field_assign:
                        self.extract_field_assignment(match_field_assign)
                # field retrieve
                elif 'iget-object' in l:
                    match_field_retir = self.is_field_retieve(l)
                    if match_field_retir:
                        self.extract_field_retrieve(match_field_retir)
                # obj initialization
                elif 'new-instance' in l:
                    match_new_instance = self.is_new_instance(l)
                    if match_new_instance:
                        self.extract_new_instance_variable(match_new_instance)
                # switch statement start
                elif ('packed-switch' in l or 'sparse-switch' in l) and ('.' not in l):
                    if self.currentMethod.isOnClickMethod():
                        # if this is the switch statement inside of onClick method
                        # we need to analyze it
                        self.insideOfSwitchBlock = True
                # switch statement end
                elif '.sparse-switch' in l or '.packed-switch' in l:
                    if self.currentMethod.isOnClickMethod():
                        # if this is the switch statement inside of onClick method
                        # we need to analyze it
                        self.insideOfSwitchBlock = False
                        self.currentSwitchCase = None
                        # and if we found something like that, then following will be the case value definiton
                        if '.packed-switch' in l:
                            # Analyze the case value based on packed switch
                            self.extractPackedSwitchValue(index,lines)
                        if '.sparse-switch' in l:
                            # Analyze the case value based on sparse switch
                            self.extractSparseSwitchValue(index,lines)

                # switch case
                elif (':pswitch' in l or ':sswitch' in l) and ('_data_' not in l):
                    if self.currentMethod.isOnClickMethod() and self.insideOfSwitchBlock:
                        foundedSwitchCase = self.extract_switch_case(l)
                        if foundedSwitchCase and (not self.currentMethod.isSwitchCaseExist(foundedSwitchCase.name)):
                            self.currentSwitchCase = foundedSwitchCase
                            self.currentMethod.conditionBlock[self.currentSwitchCase] = []

                index = index + 1

    def extractPackedSwitchValue(self, index, lines):
        # retrive the initial value
        currentLine = lines[index]
        match = re.search("\s+.packed-switch\s+(?P<initialValue>.*)", currentLine)
        if match:
            caseValue = int(match.group('initialValue'),16)
            index = index + 1
            currentLine = lines[index]
            print 'CaseValue = %s' % (caseValue)
            while '.end packed-switch' not in currentLine:
                matchCaseName = re.search("\s+(?P<matchCaseName>.*)\s+", currentLine)
                if matchCaseName:
                    caseName = matchCaseName.group('matchCaseName')
                    print 'caseName = %s' % (caseName)
                    switchCase = self.currentMethod.searchForCaseSwitch(caseName)
                    if switchCase:
                        switchCase.caseValue = '0x%x' % (caseValue)
                        caseValue = caseValue + 1
                index = index + 1
                currentLine = lines[index]

    def extractSparseSwitchValue(self, index, lines):
        # retrive the initial value
        currentLine = lines[index]
        match = re.search("\s+.sparse-switch\s+", currentLine)
        if match:
            index = index + 1
            currentLine = lines[index]
            while '.end sparse-switch' not in currentLine:
                matchCaseName = re.search("\s+(?P<caseValue>.*)\s+->\s+(?P<caseName>.*)", currentLine)
                if matchCaseName:
                    caseName = matchCaseName.group('caseName')
                    print 'caseName = %s' % (caseName)
                    caseValue = matchCaseName.group('caseValue')
                    switchCase = self.currentMethod.searchForCaseSwitch(caseName)
                    if switchCase:
                        switchCase.caseValue = (caseValue)
                index = index + 1
                currentLine = lines[index]

    def is_class(self, line):
        """Check if line contains a class definition

        Args:
            line (str): Text line to be checked

        Returns:
            bool: True if line contains class information, otherwise False

        """
        match = re.search("\.class\s+(?P<class>.*);", line)
        if match:
            # print ("Found class: %s" % match.group('class'))
            return match.group('class')
        else:
            return None

    def extract_class(self, data):
        """Extract class information

        Args:
            data (str): Data would be sth like: public static Lcom/a/b/c

        Returns:
            dict: Returns a RYClass object, otherwise None

        """
        class_info = data.split(" ")
        name = class_info[-1]
        foundedClass = RYClass(name)
        return foundedClass

    def is_class_property(self, line):
        """Check if line contains a field definition

        Args:
            line (str): Text line to be checked

        Returns:
            bool: True if line contains class property information,
                  otherwise False

        """
        match = re.search("\.field\s+(?P<property>.*);", line)
        if match:
            # print ("\t\tFound property: %s" % match.group('property'))
            return match.group('property')
        else:
            return None

    def extract_class_property(self, data):
        """Extract class property info

        Args:
            data (str): Data would be sth like: private cacheSize:I

        Returns:
            dict: Returns a widget object, otherwise None

        """
        prop_info = data.split(" ")

        # A field/property is usually saved in this form
        #  <name>:<type>
        prop_name_split = prop_info[-1].split(':')
        name = prop_name_split[0]
        type = prop_name_split[1] if len(prop_name_split) > 1 else ''
        if 'widget' in type or 'view' in type:
            # we only wants to find widget
            foundedWidget = RYWidget(name,type)
            return foundedWidget
        return None

    def is_class_method(self, line):
        """Check if line contains a method definition

        Args:
            line (str): Text line to be checked

        Returns:
            bool: True if line contains method information, otherwise False

        """
        match = re.search("\.method\s+(?P<method>.*)$", line)
        if match:
            # print ("\t\tFound method: %s" % match.group('method'))
            return match.group('method')
        else:
            return None

    def extract_class_method(self, data):
        """Extract class method info

        Args:
            data (str): Data would be sth like:
                public abstract isTrue(ILjava/lang/..;ILJava/string;)I

        Returns:
            dict: Returns a method object, otherwise None

        """
        method_info = data.split(" ")

        # A method looks like:
        #  <name>(<arguments>)<return value>
        m_name = method_info[-1]
        m_args = None
        m_ret = None

        # Search for name, arguments and return value
        match = re.search(
            "(?P<name>.*)\((?P<args>.*)\)(?P<return>.*)", method_info[-1])

        if match:
            m_name = match.group('name')
            m_args = match.group('args')
            m_ret = match.group('return')

        argList = m_args.split(';')
        foundedMethod = RYMethod(m_name,argList,m_ret)
        return foundedMethod

    def is_const_value(self, line):
        """Check if line contains const def

        Args:
            line (str): Text line to be checked

        Returns:
            bool: True if line contains const-string information,
                  otherwise False

        """
        match = re.search("const\S*\s+(?P<const>.*)", line)
        if match:
            # print ("\t\tFound const-value: %s" % match.group('const'))
            return match.group('const')
        else:
            return None

    def extract_const_value(self, data):
        """Extract const string info

        Args:
            data (str): Data would be sth like: v0, "this is a string"

        Returns:
            dict: Returns a property object, otherwise None

        """
        match = re.search('(?P<var>.*),\s+(?P<value>.*)', data)

        if match:
            # A const string is usually saved in this form
            #  <variable name>,<value>
            name = match.group('var')
            value = match.group('value')
            # update the pool
            self.variablePool[name] = value
            # print 'Name = %s' % (name)
            # print 'Value = %s' % (value)

    def is_method_call(self, line):
        """

        Args:
            line (str): Text line to be checked

        Returns:
            bool: True if line contains call information, otherwise False

        """
        match = re.search("invoke-\w+(?P<invoke>.*)", line)
        if match:
            # print("\t\t Found invoke: %s" % match.group('invoke'))
            return match.group('invoke')
        else:
            return None

    def extract_method_call(self, data):
        """Extract method call information

        Args:
            data (str): Data would be sth like:
            {v0}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

        Returns:
            dict: Returns a call object, otherwise None
        """
        # Default values
        c_dst_class = data
        c_dst_method = None
        c_local_args = None
        c_dst_args = None
        c_ret = None

        # The call looks like this
        #  <destination class>) -> <method>(args)<return value>
        match = re.search(
            '(?P<local_args>\{.*\}),\s+(?P<dst_class>.*);->' +
            '(?P<dst_method>.*)\((?P<dst_args>.*)\)(?P<return>.*)', data)

        if match:
            c_dst_class = match.group('dst_class')
            c_dst_method = match.group('dst_method')
            c_dst_args = match.group('dst_args')
            c_local_args = match.group('local_args')
            c_ret = match.group('return')

        # Added by Ruiyi-He in 2016-03-02 to track varaible retrieve
        variableMatch = re.search('\{(?P<variableSets>.*)\}',c_local_args)
        setsStr = variableMatch.group('variableSets')
        varList = setsStr.split(', ')
        caller = self.currentMethod
        callee = c_dst_method
        returnValue = c_ret
        initiatParam = ''
        inputParam = []
        if len(varList) != 0:
            if varList[0] in self.variablePool:
                initiatParam = self.variablePool[varList[0]]
            inputVarList = varList[1:]
            for inputVar in inputVarList:
                if inputVar in self.variablePool:
                    inputParam.append(self.variablePool[inputVar])
        # print 'initParam = %s' % (initiatParam)
        foundedMethodCall = RYMethodCalling(caller,callee, c_dst_class,initiatParam,inputParam,returnValue)
        return foundedMethodCall

    def is_field_assign(self, line):
        """Check [Whether the line contains a field assignment (iput-*)

        Args:
            line: Str text line to be checked

        Returns:
            bools: True if the line contains variable retrieving
        """
        match = re.search("iput-\w+(?P<iput>.*)", line)
        if match:
            return match.group('iput')
        else:
            return None

    def extract_field_assignment(self, data):
        """
        This method is actually intends to assign the value of the register var to the field
        Args:
            data: the data source

        Returns:
            It will return NOTHING, but changes the current value in the currentVaraiblePool
        """
        assignedField = None #v0
        param = None #p0
        field = None
        caller = None
        type = None

        # The call looks like this
        #  v0, p0, caller;->ActualField:FieldType
        match = re.search(
            '\s+(?P<assignedField>.*),\s+(?P<param>.*),\s+' +
            '(?P<Caller>.*);->(?P<ActualField>.*):(?P<FieldType>.*)', data)
        if match:
            assignedField = match.group('assignedField')
            param = match.group('param')
            field = match.group('ActualField')
            caller = match.group('Caller')
            type = match.group('FieldType')
            if 'widget' in type or 'view' in type:
                # indicates that it maybe a widget
                matchedWidget = self.currentClass.searchWidgetByName(field)
                if matchedWidget:
                    # we find a widget assignment
                    # now we need to assign the id to this widget
                    if len(self.currentMethod.widgetFindViewByIDStack) > 0:
                        nearestFindViewByIDCalling = self.currentMethod.widgetFindViewByIDStack.pop()
                        if nearestFindViewByIDCalling and len(nearestFindViewByIDCalling.inputParam) > 0:
                            matchedWidget.widgetID = nearestFindViewByIDCalling.inputParam[0]


    def is_field_retieve(self, line):
        """Check [Whether the line contains a field retrive (iget-*)

        Args:
            line: Str text line to be checked

        Returns:
            bools: True if the line contains variable retrieving
        """
        match = re.search("iget-\w+(?P<iget>.*)", line)
        if match:
            return match.group('iget')
        else:
            return None

    def extract_field_retrieve(self, data):
        """
        This method is actually intends to assign the value of the register var to the field
        Args:
            data: the data source

        Returns:
            It will return NOTHING, but changes the current value in the currentVaraiblePool
        """
        registerVar = None #v0
        param = None #p0
        field = None
        caller = None

        # The call looks like this
        #  v0, p0, caller;->ActualField:FieldType
        match = re.search(
            '\s+(?P<registerVar>.*),\s+(?P<param>.*),\s+' +
            '(?P<Caller>.*);->(?P<ActualField>.*):(?P<FieldType>.*)', data)
        if match:
            registerVar = match.group('registerVar')
            param = match.group('param')
            field = match.group('ActualField')
            caller = match.group('Caller')
            self.variablePool[registerVar] = field

    def is_new_instance(self, line):
        """Check [Whether the line contains a local variable retrieving (new-instance-*)

        Args:
            line: Str text line to be checked

        Returns:
            bools: True if the line contains variable retrieving
        """
        match = re.search("new-instance+(?P<newinstance>.*)", line)
        if match:
            return match.group('newinstance')
        else:
            return None

    def extract_new_instance_variable(self, data):
        """
        This method is actually intends to link the v0 with the exact new-instance
        Args:
            data: the data source

        Returns:
            It will return NOTHING, but changes the current value in the currentVaraiblePool
        """
        localVariable = None #v0
        objName = None
        # The call looks like this
        #  v1, created-obj
        match = re.search(
            '\s+(?P<registerVar>.*),\s+(?P<obj>.*);', data)
        if match:
            registerVar = match.group('registerVar')
            objName = match.group('obj')
            self.variablePool[registerVar] = objName
            print objName

    def extract_switch_case(self, data):
        """
        This method is actually intends to extract the switch case tag
        Args:
            data: the data source

        Returns:
            It will a swtich case obj
        """
        # The call looks like this
        #  :sswitch_0
        match = re.search(
            '\s+(?P<switchCase>.*)\s+', data)
        if match:
            switchCaseName = match.group('switchCase')
            foundedSwitchCase = RYSwtichCase(switchCaseName)
            print 'foundCase %s' % (switchCaseName)
            return foundedSwitchCase
        return None
