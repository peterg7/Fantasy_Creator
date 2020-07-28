
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

# User-defined Modules
from scrollGraphics import CharacterScroll, EntrySelectionView


# craete Timeline scene
class ScrollTab(qtw.QMainWindow):

    scroll_loaded = qtc.pyqtSignal()
    status_message = qtc.pyqtSignal(str, int)

    def __init__(self, parent=None):
        super(ScrollTab, self).__init__(parent)
        self.setWindowFlags(qtc.Qt.Widget)
        # Setup and layout
        self.layout = qtw.QHBoxLayout()
        self.splitter = qtw.QSplitter()

        self.selectionview = None
        self.scroll_widget = CharacterScroll(self)
       
        self.splitter.addWidget(self.scroll_widget)
        self.splitter.setOrientation(qtc.Qt.Vertical)
        self.splitter.setContentsMargins(25, 0, 25, 0)


        self.setCentralWidget(self.splitter)
        # self.layout.addWidget(self.splitter)
        # self.setLayout(self.layout)

        self.scroll_loaded.emit()
        # self.parent().moduleLoaded()
 
        self.scroll_widget.scroll.itemSelectionChanged.connect(self.handle_view)
        

    ## Auxiliary Functions ##

    def handle_view(self):
        item = self.scroll_widget.scroll.selectedItems()
        if not item:
            if self.selectionview:
                self.selectionview.setParent(None)
                self.selectionview.deleteLater()
                self.selectionview = None
                self.scroll_widget.scroll.expand()
        else:
            entry = self.scroll_widget.scroll.itemWidget(item[0])
            char = entry.getCharacter()
            char_id = char['char_id']
            if self.selectionview:
                self.selectionview.saveEdits()
                self.selectionview.updateEntry(self.scroll_widget.displayable_char(char_id))
            else:
                self.selectionview = EntrySelectionView(self.scroll_widget.displayable_char(char_id), self)
                self.selectionview.cancel_btn.clicked.connect(self.scroll_widget.scroll.clearSelection)
                self.selectionview.saved_values.connect(self.scroll_widget.handleSaveEntry)
                self.selectionview.status_message.connect(self.status_message.emit)
                self.splitter.insertWidget(0, self.selectionview)
                self.splitter.setCollapsible(0, False)
                self.scroll_widget.scroll.shrink()
                view_size = 0.7 * self.sizeHint().height()
                list_size = 0.3 * self.sizeHint().height()
                sizes = [view_size, list_size]
                self.splitter.setSizes(sizes)
                self.selectionview.updatePics()
                
    


    def build_scroll(self, db):
        # self.resize(size)
        self.scroll_widget.connect_db(db)
        self.scroll_widget.init_scroll()
        self.scroll_loaded.emit()
        # self.scroll_widget.show()
        # self.treeview.init_tree_view(trees, size)
        # self.treeview.init_char_dialogs()
    
    def resizeEvent(self, event):
        self.splitter.update()
        self.scroll_widget.update()
        super(ScrollTab, self).resizeEvent(event)
    
    @qtc.pyqtSlot()
    def saveRequest(self):
        print('Saving scroll...')
        if self.selectionview:
            self.selectionview.saveEdits()

    @qtc.pyqtSlot()
    def preferenceUpdate(self):
        print('Scroll: Received preference notification...')