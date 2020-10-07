
class InputData:
    def __init__(self):
        self.companyName = None
        self.startDate = None
        self.endDate = None
        self.lastMonth = None
        self.departmentsOfPL = None
        self.departmentsOfHC = None
        self.sameDepartmentsOfPL = None
        self.staffLocation = None
    def print(self):
        print('Mebers of InputData')
        for attr in dir(self):
            if not callable(getattr(self, attr)) and not attr.startswith("__"):
                print ('>', attr, ' = ', getattr(self, attr))


