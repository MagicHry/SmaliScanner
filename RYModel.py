"""""
Represents a "Class" in smali file
"""""

class RYClass:

    def __init__(self,fullName):
        self.name = fullName
        self.widgets = []
        self.methods = []

    def searchWidgetByName(self, widgetName):
        for widget in self.widgets:
            if widget.variableName == widgetName:
                return widget
        return None

    def searchMethodByName(self, methodName):
        for method in self.methods:
            if method.name == methodName:
                return method
        return None

    # def searchForMethod(self, methodName):
    def toString(self):
        print '--------------------'
        print 'Class Name = %s' % (self.name)
        print 'Contains Widget :'
        for widget in self.widgets:
            print widget.toString()
        print 'Contains Method :'
        for method in self.methods:
            print method.name
            if len(method.conditionBlock) > 0:
                print 'Contains Conditional Block in OnClick:'
                for case in method.conditionBlock:
                    print 'Case Name = %s Case Value = %s' % (case.name, case.caseValue)
                    print '\s Call -> %s' % (method.conditionBlock[case][0].callee)
            # for methodCall in method.methodCallingPool:
            #     methodCall.toString()
        print '--------------------'

    def searchForOnClickMethod(self):
        for method in self.methods:
            if method.isOnClickMethod():
                return method
        return None

"""""
Represents a "UIWidget" in smali file
"""""

class RYWidget:

    def __init__(self, variableName, type):
        self.variableName = variableName
        self.type = type
        self.widgetID = ''
        self.dstLink = ''

    def toString(self):
        print 'Name = %s ID = %s DstLink = %s' % (self.variableName,self.widgetID,self.dstLink)

    def toJSONSerializable(self):
        dist = {"name":self.variableName,
                "type":self.type,
                "id":self.widgetID}
        return dist

"""""
Represents a "method" in smali file
It contains several components
    - Whether this method contains ICC event
    - All the method calling happens inside of this method
    - method information (name,param,return value....)
    - code block, this is only implemented for a method contains IF-ELSE/SWITCH statement
"""""

class RYMethod:

    def __init__(self,name,params,returnValue):
        self.name = name
        self.params = params
        self.returnValue = returnValue
        self.ICCMethod = False
        self.methodCallingPool = []
        self.widgetFindViewByIDStack = []
        self.conditionBlock = {}

    def isOnClickMethod(self):
        return 'onClick' in self.name

    def isSwitchCaseExist(self,switchCaseName):
        for switchCase in self.conditionBlock:
            if switchCase.name == switchCaseName:
                return True
        return False

    def isSwitchCaseValueExist(self, switchCaseValue):
        for switchCase in self.conditionBlock:
            if switchCase.caseValue == switchCaseValue:
                return switchCase
        return None

    def searchForCaseSwitch(self,switchCaseName):
        for switchCase in self.conditionBlock:
            if switchCase.name == switchCaseName:
                return switchCase
        return None

"""""
Represents a "switch-case" in smali file
It contains several components
    - name of this case
    - actual value of this case
"""""
class RYSwtichCase:

    def __init__(self,name):
        self.name = name
        self.caseValue = ''


"""""
Represents a "method calling" in method definition block
It contains several components
    - caller (as default, it will always be the method contains this method calling)
    - callee class (class name where the called method belongs to)
    - callee (the called method name)
    - initiate param, the object initiates the method calling
    - input params, the input param of the called method
    - return value, the return value after calling
"""""

class RYMethodCalling:
    def __init__(self, caller, callee, calleeClassName, iniParam, inputParam, retV):
        self.caller = caller
        self.callee = callee
        self.calleeClassName = calleeClassName
        self.iniParam = iniParam
        self.inputParam = inputParam
        self.retV = retV

    def isFindViewByID(self):
        return self.callee == 'findViewById'

    def isSetOnClickListener(self):
        return self.callee == 'setOnClickListener'

    def isICCCalling(self):
        # matches
        # - startActivity
        # - startActivities
        # - startActivityByResult
        return 'startActivit' in self.callee

    def toString(self):
        print '%s -> %s with input %s' % (self.iniParam,self.callee,self.inputParam)