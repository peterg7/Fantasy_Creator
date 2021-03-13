
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# Built-in Modules
import re
import uuid

# 3rd Party Modules
import numpy as np
from tinydb import where

# User-defined Modules
from character import Character


# Create Look Up table view
class LookUpTableView(qtw.QTableView):

    char_selected = qtc.pyqtSignal(uuid.UUID)
    
    BACKGROUND_COLOR = '#F8ECC2'

    def __init__(self, parent=None):
        super(LookUpTableView, self).__init__(parent)
        self.setSortingEnabled(True)

        palette = self.palette()
        palette.setColor(qtg.QPalette.Base, qtg.QColor(self.BACKGROUND_COLOR))
        self.setPalette(palette)

        self.setFont(qtg.QFont("Baskerville", 15))

        # self.verticalHeader().setVisible(False)
        # self.setColumnHidden(0, True)
        # self.horizontalHeader().setStretchLastSection(True)
        
        # self.setSizeAdjustPolicy(qtw.QAbstractScrollArea.AdjustToContents)

        self.visible_check = False

    def setVisibleCol(self, state):
        self.visible_check = state
        if not self.visible_check:
            self.setColumnHidden(LookUpTableModel.VIS_COL, True)
        else: 
            self.setColumnHidden(LookUpTableModel.VIS_COL, False)
    
    def adjustView(self):
        # self.setModel(model)
        self.setColumnHidden(0, True) # ID

        self.setStyle(CheckBoxProxyStyle(self.style())) # CAUSES SEG FAULT
        self.setColumnWidth(LookUpTableModel.VIS_COL, 50)
        self.horizontalHeader().setSectionResizeMode(LookUpTableModel.VIS_COL, qtw.QHeaderView.Fixed) # Visible
        
        self.horizontalHeader().setSectionResizeMode(2, qtw.QHeaderView.Stretch) # Name
        # self.horizontalHeader().setSectionResizeMode(3, qtw.QHeaderView.ResizeToContents) # Sex
        self.horizontalHeader().setSectionResizeMode(4, qtw.QHeaderView.Stretch) # Race
        self.horizontalHeader().setSectionResizeMode(5, qtw.QHeaderView.Stretch) # Birth
        self.horizontalHeader().setSectionResizeMode(6, qtw.QHeaderView.Stretch) # Death
        # self.horizontalHeader().setSectionResizeMode(7, qtw.QHeaderView.ResizeToContents) # Ruler
        self.horizontalHeader().setSectionResizeMode(8, qtw.QHeaderView.Stretch) # Kingdom
        self.horizontalHeader().setSectionResizeMode(9, qtw.QHeaderView.Stretch) # Family

        self.horizontalHeader().setFont(qtg.QFont('Baskerville', 14))
        
    ## Override Built-In Slots ##
    @qtc.pyqtSlot(qtc.QItemSelection, qtc.QItemSelection)
    def selectionChanged(self, selected, deselected):
        if self.selectionModel().selectedRows():
            index = self.selectionModel().selectedRows()[0] # WARNING Only take first row
            self.char_selected.emit(self.model().data(index, qtc.Qt.DisplayRole))
        super(LookUpTableView, self).selectionChanged(selected, deselected)
    
    def resizeEvent(self, event):
        self.setColumnHidden(0, True)
        if not self.visible_check:
            self.setColumnHidden(LookUpTableModel.VIS_COL, True)
        # self.resizeColumnsToContents()
        super(LookUpTableView, self).resizeEvent(event)


# Create Loop Up table model
class LookUpTableModel(qtc.QAbstractTableModel):

    cell_changed = qtc.pyqtSignal(dict)
    visible_change = qtc.pyqtSignal(uuid.UUID, bool)

    ID_COL = 0
    VIS_COL = 1
    INDX = 'char_id'
    DFLT_HEADERS = ['Name', 'Sex', 'Race']

    def __init__(self, parent=None):
        super(LookUpTableModel, self).__init__(parent)
        self.DFLT_HEADERS.insert(0, self.INDX)
        self._cols = len(self.DFLT_HEADERS)
        self._rows = 0
        self._headers = self.DFLT_HEADERS
        self.character_table = np.ndarray((0, self._cols), dtype=object)    

        self.char_keys = [s.lower().split()[0] for s in self.DFLT_HEADERS]
        self.char_keys.insert(0, self.INDX)
        self.checks = {}

    def set_columns(self, columns):
        self.layoutAboutToBeChanged.emit()
        self._headers = columns
        self._headers.insert(self.ID_COL, self.INDX)
        self._headers.insert(self.VIS_COL, 'Visible')
        self.char_keys = [s.lower().split()[0] for s in self._headers]
        self._cols = len(columns)
        self.character_table = np.resize(self.character_table, (self._rows, self._cols))
        self.layoutChanged.emit()

    def connect_db(self, database):
        # Create tables
        self.meta_db = database.table('meta')
        self.character_db = database.table('characters')
        self.families_db = database.table('families')
        self.kingdoms_db = database.table('kingdoms')

    ## Custom Slots ##

    @qtc.pyqtSlot(list)
    def insertNewChars(self, newChars):
        self.beginInsertRows(
            qtc.QModelIndex(),
            self._rows,
            self._rows + len(newChars) - 1
        )
        for char_id in newChars:
            char_record = self.character_db.get(where('char_id') == char_id)

            # Need to access families db
            if 'family' in self.char_keys:
                if self.families_db.contains(where('fam_id') == char_record['fam_id']):
                    char_record['family'] = self.families_db.get(where('fam_id') == char_record['fam_id'])['fam_name']
                elif char_record['partnerships']:
                    # self.families_db.contains(where('fam_id') == char_record['partnerships'][0]['rom_id'])
                    char_record['family'] = self.families_db.get(where('fam_id') == char_record['partnerships'][0]['rom_id'])['fam_name']
            # Need to access kingdoms db
            if 'kingdom' in self.char_keys:
                if self.kingdoms_db.contains(where('kingdom_id') == char_record['kingdom_id']):
                    char_record['kingdom'] = self.kingdoms_db.get(where('kingdom_id') == char_record['kingdom_id'])['kingdom_name']
        
            if 'birth' in self.char_keys:
                char_record['birth'] = str(char_record['birth'])
            
            if 'death' in self.char_keys:
                char_record['death'] = str(char_record['death'])
            
            if 'ruler' in self.char_keys:
                char_record['ruler'] = 'Yes' if char_record['ruler'] else 'No'

            newRow = []
            for key in self.char_keys:
                newRow.append(char_record.get(key, ''))
            self.character_table = np.insert(
                self.character_table, self._rows, newRow, 0)
            self._rows += 1
        self.endInsertRows()
        # for i in range(self._rows):
        #     checkBox = qtw.QTableWidgetItem()
        #     checkBox.setFlags(qtc.Qt.ItemIsUserCheckable | qtc.Qt.ItemIsEnabled)
        #     checkBox.setCheckState(qtc.Qt.Unchecked)
        #     self.setItem(i, len(self._cols))

        # topLeftIndex = self.createIndex(position, 0)
        # bottomRightIndex = self.createIndex(self._rows, self._cols)
        # self.dataChanged.emit(topLeftIndex, bottomRightIndex, [])

    @qtc.pyqtSlot(list)
    def removeChars(self, deletedChars):
        for char_id in deletedChars:
            index = np.where(char_id == self.character_table[:,0])[0][0]
            if index is not None:
                self.beginRemoveRows(
                    qtc.QModelIndex(),
                    index,
                    index
                )
                self.character_table = np.delete(self.character_table, index, axis=0)       
                self.endRemoveRows()
                self._rows -= 1


    @qtc.pyqtSlot(list)
    def updateChars(self, changedChars):
        for char_id in changedChars:
            index = np.where(char_id == self.character_table[:,0])[0][0]
            if index is not None:
                char_record = self.character_db.get(where('char_id') == char_id)

                # Need to access families db
                if 'family' in self.char_keys:
                    if self.families_db.contains(where('fam_id') == char_record['fam_id']):
                        char_record['family'] = self.families_db.get(where('fam_id') == char_record['fam_id'])['fam_name']
                    elif char_record['partnerships']:
                        char_record['family'] = self.families_db.get(where('fam_id') == char_record['partnerships'][0]['rom_id'])['fam_name']
                # Need to access kingdoms db
                if 'kingdom' in self.char_keys:
                    if self.kingdoms_db.contains(where('kingdom_id') == char_record['kingdom_id']):
                        char_record['kingdom'] = self.kingdoms_db.get(where('kingdom_id') == char_record['kingdom_id'])['kingdom_name']
                
                if 'birth' in self.char_keys:
                    char_record['birth'] = str(char_record['birth'])

            
                if 'death' in self.char_keys:
                    char_record['death'] = str(char_record['death'])
                
                if 'ruler' in self.char_keys:
                    char_record['ruler'] = 'Yes' if char_record['ruler'] else 'No'
                
                updatedRow = []
                for key in self.char_keys:
                    updatedRow.append(char_record.get(key, ''))
                self.character_table[index] = updatedRow

                topLeftIndex = self.createIndex(index, 0)
                bottomRightIndex = self.createIndex(index, self._cols)
                self.dataChanged.emit(topLeftIndex, bottomRightIndex, [])    
    

    @qtc.pyqtSlot()
    @qtc.pyqtSlot(bool)
    def preferenceUpdate(self, reorder=False):
        self.updateChars([x['char_id'] for x in self.character_db])
        

    ## Overridde Built-In Slots ##

    # adding write capability
    def flags(self, index):
        if index.column() == self.VIS_COL:
            return super().flags(index) | qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsUserCheckable
        return super().flags(index) | qtc.Qt.ItemIsEditable
    
    def checkState(self, index):
        if index in self.checks:
            return self.checks[index]
        else:
            return qtc.Qt.Checked
    
    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if role == qtc.Qt.CheckStateRole:
            self.checks[qtc.QPersistentModelIndex(index)] = value
            char = self.character_table[index.row()][self.ID_COL]
            self.visible_change.emit(char, bool(value))
            return True
        
        if role == qtc.Qt.EditRole:
            selected_char = self.character_table[index.row()]
            selected_char[index.column()] = value
            #print(f"Changed  {self.character_table[index.row()][0]}'s {self._headers[index.column()]}")
            self.dataChanged.emit(index, index, [role])
            self.cell_changed.emit(dict(zip(self.char_keys, selected_char)))
            return True
        
        return False
            
    

    def sort(self, column, order):
        if self._rows > 0:
            self.layoutAboutToBeChanged.emit() # needs to be emitted before a sort
            self.character_table = np.array(sorted(self.character_table, 
                key=lambda x: natural_keys(x[column])))
            if order == qtc.Qt.DescendingOrder:
                self.character_table = np.flipud(self.character_table)
            self.layoutChanged.emit() # needs to be emitted after a sort
            

    ## Required Virtual Functions ##

    def rowCount(self, parent):
        return self._rows

    def columnCount(self, parent):
        return self._cols

    def data(self, index, role): # return data in a single cell
        if not index.isValid():
            return False
        if role == qtc.Qt.TextAlignmentRole:
            return qtc.Qt.AlignCenter
        if role == qtc.Qt.CheckStateRole and index.column() == self.VIS_COL:
            return self.checkState(qtc.QPersistentModelIndex(index))
        if role in [qtc.Qt.DisplayRole, qtc.Qt.EditRole]:
            return self.character_table[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role):
        if(orientation == qtc.Qt.Horizontal and role == qtc.Qt.DisplayRole):
            return self._headers[section]
        else:
            return super().headerData(section, orientation, role)

## Global Helper Functions ##

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)',text) ]


class CheckBoxProxyStyle(qtw.QProxyStyle):
    def subElementRect(self, element, option=None, widget=None):
        rect = super().subElementRect(element, option, widget)
        if element == qtw.QStyle.SE_ItemViewItemCheckIndicator:
            rect.moveCenter(option.rect.center())
        return rect