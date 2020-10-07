from django.conf import settings
import pywintypes
import xlwings as xw
import time
import os
import pythoncom
from adminApp.models import AdminSetting
import numpy as np

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def excel_style(col, row):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col-1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)

class ExcelManager:
    # Create Manager and Init Template FileName
    def __init__(self):
        # self.temp_file_name = os.path.join(settings.BASE_DIR, r'public\VBAFIle.xlsm')
        # self.temp_file_name = r'Financial Model Template_MD_TEMPLATE (25.7).xlsm'
        # self.temp_file_name = r'Financial Model Template_MD_TEMPLATE (27.4).xlsm'
        self.temp_file_name = AdminSetting.getField('TemplateFileName')
        if self.temp_file_name == "":
            self.temp_file_name = r'Financial Model Template_MD_TEMPLATE (29.2 No-CDATA).xlsm'

        self.save_file_name = r'result.xlsm'
        self.temp_file_path = os.path.join(settings.PUBLIC_DIR, self.temp_file_name)
        self.save_file_path = os.path.join(settings.PUBLIC_DIR, self.save_file_name)

    # companyName
    # startDate
    # endDate
    # lastMonth
    # departmentsOfPL
    # sameDepartmentsOfPL
    # departmentsOfHC
    # staffLocation
    def refreshSaveFileName(self, runMacro):
        # self.save_file_name = r'result_' + time.strftime("%Y%m%d_%H%M%S") +'.xlsx'
        self.save_file_name = self.companyName + " - Financial Model " + time.strftime("%Y%m%d_%H%M%S")
        if runMacro or self.isRollForward:
            self.save_file_name += '.xlsx'
        else :
            self.save_file_name += '.xlsm'

        self.save_file_path = os.path.join(settings.PUBLIC_DIR, self.save_file_name)

    # Read Data From Session
    def loadData(self, session):
        self.companyName = ''
        self.accountingBasis = ''
        self.departmentsOfPL = []
        self.sameDepartmentsOfPL = False
        self.departmentsOfHC = []
        self.staffLocation = []

        if 'companyName' in session: self.companyName = session['companyName']
        if 'accountingBasis' in session: self.accountingBasis = session['accountingBasis']
        if 'departmentsOfPL' in session: self.departmentsOfPL = session['departmentsOfPL']
        if 'sameDepartmentsOfPL' in session: self.sameDepartmentsOfPL = session['sameDepartmentsOfPL']
        if 'departmentsOfHC' in session: self.departmentsOfHC = session['departmentsOfHC']
        if 'staffLocation' in session: self.staffLocation = session['staffLocation']

    # Map Input Form Data
    def create(self, session, startDate, endDate, lastMonth, reportType='Report'):
        self.startDate = startDate
        self.endDate = endDate
        self.lastMonth = lastMonth
        self.reportType = reportType
        self.isRollForward =  self.reportType == "RollForward"
        print("SPIDER", 1)
        pythoncom.CoInitialize()
        print("SPIDER", 11)
        self.app = xw.App(visible=False)
        print("SPIDER", 12)
        self.app.display_alerts = False
        print("SPIDER", 2)

        try:
            if not self.isRollForward:
                self.wb = self.app.books.open(self.temp_file_path)
            else:
                self.wb = self.app.books.add()
                self.wb.sheets['Sheet1'].name = 'PBC - Account List'
                self.wb.sheets.add(name='PBC - Balance Sheet')
                self.wb.sheets.add(name='PBC - Income Statement')
            self.wb.app.calculation = 'manual'
        except Exception as error:
            print('[SPIDER] [XLManager] [Create] Template Not Found Exception :' + repr(error))
            return False
        self.loadData(session)
        print("SPIDER", 3)

        if self.isRollForward:
            return True

        self.sht = self.wb.sheets['Setup']
        self.sht.range('E5').value = self.companyName
        self.sht.range('E6').value = self.startDate
        self.sht.range('E7').value = self.endDate
        self.sht.range('E8').value = self.accountingBasis
        print("SPIDER", 4)

        i = 0
        for department in self.departmentsOfPL:
            self.sht.range('D'+str(11+i)).value = department
            i += 1

        # i = 0
        # for department in self.departmentsOfHC:
        #     self.sht.range('E'+str(11+i)).value = department
        #     i += 1

        i = 0
        for location in self.staffLocation:
            self.sht.range('E'+str(11+i)).value = location
            i += 1

        self.sht = self.wb.sheets['Drivers']
        self.sht.range('E10').value = self.lastMonth
        print("SPIDER", 5)

        return True

    # Close and Get Saved FileName
    def close(self, runMacro):
        self.refreshSaveFileName(runMacro)
        self.wb.app.calculation = 'automatic'
        if runMacro:
            try:
                print('[SPIDER] [XLManager] [Macro] START')
                macroFunc = self.wb.macro('MainWorkflow')
                macroFunc()
                print('[SPIDER] [XLManager] [Macro] SUCCESS')
            except Exception as error:
                print('[SPIDER] [XLManager] [Macro] Exception : ' + repr(error))
                # return [False, None]
        else:
            self.wb.save(self.save_file_path)
        try:
            self.wb.close()
        except Exception as error:
            print('[SPIDER] [XLManager] [Close] Exception : ' + repr(error))

        print('3')
        self.app.quit()
        print('4')

        if not runMacro:
            return [True, self.save_file_name]

        self.src_file_path = os.path.join(settings.PUBLIC_DIR, 'Result ' + self.companyName + '.xlsx')
        os.rename(self.src_file_path, self.save_file_path)
        return [True, self.save_file_name]
    def isColEmpty(self, coldatas):
        col = 1
        for coldata in coldatas:
            if col != 1:
                value = coldata['value']
                if value is '': value = '0'
                if float(value) != 0:
                    return False
            col += 1
        return True

    # Parse ProfitAndLoss & Balance Sheet Response to Array
    def parseData(self, datakey, data, depth = 0, isHeader = 0):
        headerId = -1
        summaryId = -1
        isAllEmpty = True
        for key in data:
            if key == 'Header':
                [isEmpty, headerId] = self.parseData(key, data[key], depth+1, isHeader = 1)
            elif key == 'Summary':
                [isEmpty, summaryId] = self.parseData(key, data[key], depth+1, isHeader = 2)
            elif key == 'Rows':
                isEmpty = self.parseData(key, data[key], depth)
            elif key == 'Row':
                isEmpty = True
                for dat in data[key]:
                    isRowEmpty = self.parseData(key, dat, depth+1)
                    if isRowEmpty == False:
                        isEmpty = False
            elif key == 'ColData':
                self.values.append(data[key])
                isEmpty = self.isColEmpty(data[key])
                self.isEmpty.append(isEmpty)
                # if isHeader == 1 or isHeader == 2:                
                #     self.isEmpty[len(self.values) - 1] = False
                if isHeader == 1:
                    retHeaderId = len(self.values) - 1
                if isHeader == 2:
                    retSummaryId = len(self.values) - 1
            # Update isAllEmpty
            if isEmpty == False:
                isAllEmpty = False
        # Update Header Value
        if headerId != -1:
            self.isEmpty[headerId] = isAllEmpty
            if depth <= 1:
                self.isEmpty[headerId] = False
        if summaryId != -1:
            if depth <= 1:
                self.isEmpty[summaryId] = False

        # return for header       
        if isHeader == 1:
            return [isAllEmpty, retHeaderId]
        if isHeader == 2:
            return [isAllEmpty, retSummaryId]
        return isAllEmpty

    def fillSheet(self, datas, sheetname, sheet_type):
        self.sht = self.wb.sheets[sheetname]
        self.sht.range('A7').value = 'Account'

        status, data = datas
        if status == False:
            print('[SPIDER] [XLManager] api request failed')
            return
        
        coldatas = data['Columns']['Column']
        nCol = len(coldatas)
        col = 1
        for coldata in coldatas:
            if col == 1:
                pass
            elif sheet_type == 0 and col == nCol:
                pass
            else:
                self.sht.range(excel_style(col, 7)).number_format = 'mmm-yy'
                self.sht.range(excel_style(col, 7)).value = coldata['MetaData'][1]['Value']
            col = col + 1

        self.values = []
        self.isEmpty = []
        self.parseData('Rows', data['Rows'])


        aRow = 0
        i = 0
        for coldatas in self.values:
            # Ignore empty rows
            if self.isEmpty[i] == True:
                i = i + 1
                continue
            aRow = aRow + 1
            i = i + 1

        if aRow == 0:
            return
        aCol = nCol - 1
        if sheet_type == 0:
            aCol = aCol - 1
        arr = np.zeros(shape=(aRow, aCol))

        row = 8
        i = 0
        srow = 0
        for coldatas in self.values:
            # Ignore empty rows
            if self.isEmpty[i] == True:
                i = i + 1
                continue

            nCol = len(coldatas)
            col = 1
            for coldata in coldatas:
                if sheet_type == 0 and col == nCol:
                    pass
                else:
                    value = coldata['value']
                    if value is '': value = '0'
                    if col == 1:
                        self.sht.range(excel_style(col, row)).value = value
                    else :
                        arr[srow, col-2] = value
                col = col + 1
            row = row + 1
            srow = srow + 1
            i = i + 1
        self.sht.range('B8').options(expend='table').value = arr

    # Parse apiProfitAndLoss response and Write to Excel
    def writeProfitAndLoss(self, datas):
        self.fillSheet(datas, 'PBC - Income Statement', 0)

    # Parse apiBalanceSheet response and Write to Excel
    def writeBalanceSheet(self, datas):
        self.fillSheet(datas, 'PBC - Balance Sheet', 1)

    def get_data(self, account, param1, param2, default=''):
        if account.get(param1) == None:
            return default
        return account.get(param1).get(param2, default)

    # Parse apiAccountListDetail response and Write to Excel
    def writeAccountListDetail(self, datas):
        self.sht = self.wb.sheets['PBC - Account List']

        try:
            status, data = datas
            if status == False:
                return False
            accounts = data['QueryResponse']['Account']
        except Exception as error:
            print('[SPIDER] [SERVICE] [AccountListDetail] Exception : ' + repr(error), data)
            return False
        
        self.sht.range('A7').value = 'Id'
        self.sht.range('B7').value = 'SyncToken'
        self.sht.range('C7').value = 'MetaData_CreateTime'
        self.sht.range('D7').value = 'MetaData_LastUpdatedTime'
        self.sht.range('E7').value = 'Name'
        self.sht.range('F7').value = 'SubAccount'
        self.sht.range('G7').value = 'ParentRef'
        self.sht.range('H7').value = 'ParentRef_Name'
        self.sht.range('I7').value = 'FullyQualifiedName'
        self.sht.range('J7').value = 'Description'
        self.sht.range('K7').value = 'Active'
        self.sht.range('L7').value = 'Classification'
        self.sht.range('M7').value = 'AccountType'
        self.sht.range('N7').value = 'AccountSubType'
        self.sht.range('O7').value = 'AcctNum'
        self.sht.range('P7').value = 'CurrentBalance'
        self.sht.range('Q7').value = 'CurrentBalanceWithSubAccounts'
        self.sht.range('R7').value = 'CurrencyRef'
        self.sht.range('S7').value = 'CurrencyRef_Name'
        self.sht.range('T7').value = 'TaxCodeRef'

        row = 8
        srow = 0
        # arr = np.zeros(shape=(len(accounts), 20))
        nAccounts = len(accounts)
        arr = [['' for i in range(20)] for j in range(nAccounts)]
        rval = 0

        for account in accounts:
            # self.sht.range('A'+str(row)).value = account.get('Id')
            # self.sht.range('B'+str(row)).value = account.get('SyncToken', 0)
            # self.sht.range('C'+str(row)).value = account.get('MetaData').get('CreateTime')
            # self.sht.range('D'+str(row)).value = account.get('MetaData').get('LastUpdatedTime')
            # self.sht.range('E'+str(row)).value = account.get('Name')
            # self.sht.range('F'+str(row)).value = account.get('SubAccount')
            # self.sht.range('G'+str(row)).value = self.get_data(account, 'ParentRef', 'value')
            # self.sht.range('H'+str(row)).value = self.get_data(account, 'ParentRef', 'name')
            # self.sht.range('I'+str(row)).value = account.get('FullyQualifiedName')
            # self.sht.range('J'+str(row)).value = account.get('Description')
            # self.sht.range('K'+str(row)).value = account.get('Active')
            # self.sht.range('L'+str(row)).value = account.get('Classification')
            # self.sht.range('M'+str(row)).value = account.get('AccountType')
            # self.sht.range('N'+str(row)).value = account.get('AccountSubType')
            # self.sht.range('O'+str(row)).value = account.get('AcctNum')
            # self.sht.range('P'+str(row)).value = account.get('CurrentBalance')
            # self.sht.range('Q'+str(row)).value = account.get('CurrentBalanceWithSubAccounts')
            # self.sht.range('R'+str(row)).value = account.get('CurrencyRef').get('value')
            # self.sht.range('S'+str(row)).value = account.get('CurrencyRef').get('name')
            # self.sht.range('T'+str(row)).value = account.get('TaxCodeRef')

            try:
                arr[srow][0] = account.get('Id')
                arr[srow][1] = account.get('SyncToken', 0)
                arr[srow][2] = account.get('MetaData').get('CreateTime')
                arr[srow][3] = account.get('MetaData').get('LastUpdatedTime')
                arr[srow][4] = account.get('Name')
                arr[srow][5] = account.get('SubAccount')
                arr[srow][6] = self.get_data(account, 'ParentRef', 'value')
                arr[srow][7] = self.get_data(account, 'ParentRef', 'name')
                arr[srow][8] = account.get('FullyQualifiedName')
                arr[srow][9] = account.get('Description')
                arr[srow][10] = account.get('Active')
                arr[srow][11] = account.get('Classification')
                arr[srow][12] = account.get('AccountType')
                arr[srow][13] = account.get('AccountSubType')
                arr[srow][14] = account.get('AcctNum')
                arr[srow][15] = account.get('CurrentBalance')
                arr[srow][16] = account.get('CurrentBalanceWithSubAccounts')
                try:
                    arr[srow][17] = account.get('CurrencyRef').get('value')
                    arr[srow][18] = account.get('CurrencyRef').get('name')
                except Exception as error:
                    print('[SPIDER] [SERVICE] [AccountListDetail] [CurreyncyRef] Exception : ' + repr(error))
                arr[srow][19] = account.get('TaxCodeRef')
            except Exception as error:
                print('[SPIDER] [SERVICE] [AccountListDetail] [all] Exception : ' + repr(error))

            row = row + 1
            srow = srow + 1
        print("[SPIDER] [ACCOUNTLIST] 4")
        self.sht.range('A8').options(expend='table').value = arr
        print("[SPIDER] [ACCOUNTLIST] 5")

        return True
