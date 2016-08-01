"""""
Result output helper, will output the analyzed result as JSON formmat
"""""
import json
from RYModel import RYWidget
class RYWriter:

    def __init__(self, location, result):
        self.fileLocation = location
        self.iccWidgetDist = result

    def packResult(self):
        jsString = json.dumps(self.iccWidgetDist, default=RYWidget.toJSONSerializable)
        with open(self.fileLocation+"/result.txt","w+") as f:
            f.write(jsString)

