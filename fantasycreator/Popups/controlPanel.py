
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import sys

# User-defined Modules
import Mechanics.flags as flags

# Create Control widget
class TreeControlPanel(qtw.QDockWidget):

    filtersChanged = qtc.pyqtSignal(int, int)
    selectionChanged = qtc.pyqtSignal(int, str)

    def __init__(self, parent=None):
        super(TreeControlPanel, self).__init__(parent)

        self.setWindowTitle('Control Panel')
        self.setAllowedAreas(qtc.Qt.RightDockWidgetArea | 
                            qtc.Qt.LeftDockWidgetArea)

        control_widget = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        groupbox_font = qtg.QFont('Baskerville', 16)
        
        # Filters Groupbox
        filters_layout = qtw.QVBoxLayout()
        filters_groupbox = qtw.QGroupBox('Filters')
        self.show_rulers = qtw.QCheckBox('Show Rulers')
        self.show_rulers.setChecked(True)
        self.show_fam_names = qtw.QCheckBox('Show Family Names')
        self.show_fam_names.setChecked(True)
        self.show_partners = qtw.QCheckBox('Show Family Heads')
        self.connect_partners = qtw.QCheckBox('Connect Families')
        filter_font = qtg.QFont('Baskerville', 16)
        self.show_rulers.setFont(filter_font)
        self.show_fam_names.setFont(filter_font)
        self.show_partners.setFont(filter_font)
        self.connect_partners.setFont(filter_font)
        filters_layout.addWidget(self.show_rulers)
        filters_layout.addWidget(self.show_fam_names)
        filters_layout.addWidget(self.show_partners)
        filters_layout.addWidget(self.connect_partners)

        filters_groupbox.setLayout(filters_layout)
        filters_groupbox.setFont(groupbox_font)
        
        # Selections Groupbox
        selection_layout = qtw.QVBoxLayout()
        selection_groupbox = qtw.QGroupBox('Selections')
        tree_display_layout = qtw.QVBoxLayout()
        tree_display_layout.setSpacing(0)
        tree_display_layout.setContentsMargins(0, 0, 0, 0)
        display_mode_label = qtw.QLabel('Tree Display Mode:')
        # display_font = display_mode_label.font()
        # display_font.setPointSize(12)
        display_font = qtg.QFont('Baskerville', 16)
        display_mode_label.setFont(display_font)
        self.icon_display = qtw.QComboBox()
        self.icon_display.addItems(['Image', 'Name'])
        self.icon_display.setFont(qtg.QFont('Baskerville', 15))
        tree_display_layout.addWidget(display_mode_label)
        tree_display_layout.addWidget(self.icon_display)

        kingdom_select_layout = qtw.QVBoxLayout()
        kingdom_select_layout.setSpacing(0)
        kingdom_select_layout.setContentsMargins(0, 0, 0, 0)
        kingdom_select_label = qtw.QLabel('Kingdom Selection:')
        # kingdom_font = kingdom_select_label.font()
        # kingdom_font.setPointSize(12)
        kingdom_font = qtg.QFont('Baskerville', 16)
        kingdom_select_label.setFont(kingdom_font)
        self.kingdom_select = MultiSelectComboBox(self, placeholderText='...')
        self.kingdom_select.setFont(qtg.QFont('Baskerville', 15))
        # self.kingdom_select.addItems(['Test_1', 'Test_2'])
        kingdom_select_layout.addWidget(kingdom_select_label)
        kingdom_select_layout.addWidget(self.kingdom_select)

        family_select_layout = qtw.QVBoxLayout()
        family_select_layout.setSpacing(0)
        family_select_layout.setContentsMargins(0, 0, 0, 0)
        family_select_label = qtw.QLabel('Family Selection:')

        family_font = qtg.QFont('Baskerville', 16)
        family_select_label.setFont(family_font)
        self.family_select = MultiSelectComboBox(self, placeholderText='...')
        self.family_select.setFont(qtg.QFont('Baskerville', 15))
        # self.family_select.addItem('...')
        # item = self.family_select.model().item(0)
        # item.setEnabled(False)
        
        family_select_layout.addWidget(family_select_label)
        family_select_layout.addWidget(self.family_select)

        selection_layout.addLayout(tree_display_layout)
        selection_layout.addLayout(kingdom_select_layout)
        selection_layout.addLayout(family_select_layout)
        selection_groupbox.setLayout(selection_layout)
        selection_groupbox.setFont(groupbox_font)
        # View Groupbox

        

        layout.addWidget(filters_groupbox)
        layout.addWidget(selection_groupbox)
        control_widget.setLayout(layout)
        control_widget.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.setWidget(control_widget)

        # Connect signals
        signal_mapper = qtc.QSignalMapper(self)

        self.show_rulers.stateChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.show_rulers, flags.FAMILY_FLAGS.DISPLAY_RULERS)

        self.show_fam_names.stateChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.show_fam_names, flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES)

        self.show_partners.stateChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.show_partners, flags.FAMILY_FLAGS.INCLUDE_PARTNERS)

        self.connect_partners.stateChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.connect_partners, flags.FAMILY_FLAGS.CONNECT_PARTNERS)

        self.icon_display.currentIndexChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.icon_display, flags.TREE_ICON_DISPLAY.BASE)

        self.family_select.currentTextChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.family_select, flags.GROUP_SELECTION_ITEM.FAMILY)

        self.kingdom_select.currentTextChanged.connect(signal_mapper.map)
        signal_mapper.setMapping(self.kingdom_select, flags.GROUP_SELECTION_ITEM.KINGDOM)

        signal_mapper.mapped[int].connect(self.controlSignals)

    @qtc.pyqtSlot(int)
    def controlSignals(self, value):
        if value == flags.TREE_ICON_DISPLAY.BASE:
            selection = value + self.icon_display.currentIndex() + 1
            if selection in flags.TREE_ICON_DISPLAY._value2member_map_:
                self.filtersChanged.emit(flags.TREE_ICON_DISPLAY.BASE, selection)
            return
        if value == flags.GROUP_SELECTION_ITEM.FAMILY:
            selection = self.family_select.currentText()
            self.selectionChanged.emit(flags.GROUP_SELECTION_ITEM.FAMILY, selection)
            return
        
        if value == flags.GROUP_SELECTION_ITEM.KINGDOM:
            selection = self.kingdom_select.currentText()
            self.selectionChanged.emit(flags.GROUP_SELECTION_ITEM.KINGDOM, selection)
            return
        
        self.filtersChanged.emit(flags.FAMILY_FLAGS.BASE, value)

    @qtc.pyqtSlot(int, list)
    def updateSelections(self, flag, value_changes):
        if flag == flags.SELECTIONS_UPDATE.ADDED_FAM:
            model = self.family_select.model()
            index = self.family_select.count()
            self.family_select.blockSignals(True)
            for fam in value_changes:
                # if fam['fam_id'] == NULL_ID:
                #     continue
                self.family_select.addItem(fam['fam_name'])
                item = model.item(index)
                item.setCheckable(True)
                model.setData(model.index(index, 0),
                                qtc.Qt.Checked,
                                qtc.Qt.CheckStateRole)
                index += 1
            self.family_select.blockSignals(False)
        
        elif flag == flags.SELECTIONS_UPDATE.REMOVED_FAM:
            self.family_select.blockSignals(True)
            for fam in value_changes:
                index = self.family_select.findText(fam['fam_name'])
                self.family_select.removeItem(index)
            self.family_select.blockSignals(False)
            
        elif flag == flags.SELECTIONS_UPDATE.ADDED_KINGDOM:
            model = self.kingdom_select.model()
            index = self.kingdom_select.count()
            self.kingdom_select.blockSignals(True)
            for val in value_changes:
                self.kingdom_select.addItem(val['kingdom_name'])
                item = model.item(index)
                item.setCheckable(True)
                model.setData(model.index(index, 0),
                                qtc.Qt.Checked,
                                qtc.Qt.CheckStateRole)
                index += 1
            self.kingdom_select.blockSignals(False)

        elif flag == flags.SELECTIONS_UPDATE.REMOVED_KINGDOM:
            print('Update selection, removed kingdom - in construction')

    @qtc.pyqtSlot(int, int)
    def updateFilters(self, flag, value):
        if flag == flags.FAMILY_FLAGS.BASE:
            if value == flags.FAMILY_FLAGS.DISPLAY_RULERS:
                print('Update filters, display ruler - in construction')
            elif value == flags.FAMILY_FLAGS.DISPLAY_FAM_NAMES:
                print('Update filters, display fam names - in construction')
            elif value == flags.FAMILY_FLAGS.INCLUDE_PARTNERS:
                # self.show_partners.blockSignals(True)
                self.show_partners.setChecked(not self.show_partners.isChecked())
                # self.show_partners.blockSignals(False)


#TODO: make items selectable by default & SIMPLIFY
# Create Multi-selection ComboBox
class MultiSelectComboBox(qtw.QComboBox):

    class ComboItemDelegate(qtw.QStyledItemDelegate):

        def isSeparator(self, index):
            return str(index.data(qtc.Qt.AccessibleDescriptionRole)) == "separator"

        def paint(self, painter, option, index):
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = qtw.QApplication.style()

            option = qtw.QStyleOptionViewItem(option)
            option.showDecorationSelected = True

            # option.state &= ~QStyle.State_HasFocus & ~QStyle.State_MouseOver
            if self.isSeparator(index):
                opt = qtw.QStyleOption()
                opt.rect = qtc.QRect(option.rect)
                if isinstance(option.widget, qtw.QAbstractItemView):
                    opt.rect.setWidth(option.widget.viewport().width())
                style.drawPrimitive(qtw.QStyle.PE_IndicatorToolBarSeparator,
                                    opt, painter, option.widget)
            else:
                super(MultiSelectComboBox.ComboItemDelegate, self).paint(painter, option, index)


    class ComboMenuDelegate(qtw.QAbstractItemDelegate):

        def isSeparator(self, index):
            return str(index.data(qtc.Qt.AccessibleDescriptionRole)) == "separator"

        def paint(self, painter, option, index):
            menuopt = self._getMenuStyleOption(option, index)
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = qtw.QApplication.style()
            style.drawControl(qtw.QStyle.CE_MenuItem, menuopt, painter,
                                option.widget)

        def sizeHint(self, option, index):
            menuopt = self._getMenuStyleOption(option, index)
            if option.widget is not None:
                style = option.widget.style()
            else:
                style = qtw.QApplication.style()
            return style.sizeFromContents(
                qtw.QStyle.CT_MenuItem, menuopt, menuopt.rect.size(),
                option.widget
            )

        def _getMenuStyleOption(self, option, index):
            menuoption = qtw.QStyleOptionMenuItem()
            palette = option.palette.resolve(qtw.QApplication.palette("QMenu"))
            foreground = index.data(qtc.Qt.ForegroundRole)
            if isinstance(foreground, (qtg.QBrush, qtg.QColor, qtg.QPixmap)):
                foreground = qtg.QBrush(foreground)
                palette.setBrush(qtg.QPalette.Text, foreground)
                palette.setBrush(qtg.QPalette.ButtonText, foreground)
                palette.setBrush(qtg.QPalette.WindowText, foreground)

            background = index.data(qtc.Qt.BackgroundRole)
            if isinstance(background, (qtg.QBrush, qtg.QColor, qtg.QPixmap)):
                background = qtg.QBrush(background)
                palette.setBrush(qtg.QPalette.Background, background)

            menuoption.palette = palette

            decoration = index.data(qtc.Qt.DecorationRole)
            if isinstance(decoration, qtg.QIcon):
                menuoption.icon = decoration

            if self.isSeparator(index):
                menuoption.menuItemType = qtw.QStyleOptionMenuItem.Separator
            else:
                menuoption.menuItemType = qtw.QStyleOptionMenuItem.Normal

            if index.flags() & qtc.Qt.ItemIsUserCheckable:
                menuoption.checkType = qtw.QStyleOptionMenuItem.NonExclusive
            else:
                menuoption.checkType = qtw.QStyleOptionMenuItem.NotCheckable

            check = index.data(qtc.Qt.CheckStateRole)
            menuoption.checked = check == qtc.Qt.Checked

            if option.widget is not None:
                menuoption.font = option.widget.font()
            else:
                menuoption.font = qtw.QApplication.font("QMenu")

            menuoption.maxIconWidth = option.decorationSize.width() + 4
            menuoption.rect = option.rect
            menuoption.menuRect = option.rect

            menuoption.menuHasCheckableItems = True
            menuoption.tabWidth = 0
            # TODO: self.displayText(QVariant, QLocale)
            # TODO: Why is this not a QStyledItemDelegate?
            display = index.data(qtc.Qt.DisplayRole)
            if isinstance(display, str):
                menuoption.text = display
            else:
                menuoption.text = str(display)

            menuoption.fontMetrics = qtg.QFontMetrics(menuoption.font)
            state = option.state & (qtw.QStyle.State_MouseOver |
                                    qtw.QStyle.State_Selected |
                                    qtw.QStyle.State_Active)

            if index.flags() & qtc.Qt.ItemIsEnabled:
                state = state | qtw.QStyle.State_Enabled
                menuoption.palette.setCurrentColorGroup(qtg.QPalette.Active)
            else:
                state = state & ~qtw.QStyle.State_Enabled
                menuoption.palette.setCurrentColorGroup(qtg.QPalette.Disabled)

            if menuoption.checked:
                state = state | qtw.QStyle.State_On
            else:
                state = state | qtw.QStyle.State_Off

            menuoption.state = state
            return menuoption

    def __init__(self, parent=None, placeholderText="", separator=", ",
                    **kwargs):
        super(MultiSelectComboBox, self).__init__(parent, **kwargs)
        self.setFocusPolicy(qtc.Qt.StrongFocus)

        self.__popupIsShown = False
        self.__supressPopupHide = False
        self.__blockMouseReleaseTimer = qtc.QTimer(self, singleShot=True)
        self.__initialMousePos = None
        self.__separator = separator
        self.__placeholderText = placeholderText
        self.__updateItemDelegate()

    def mousePressEvent(self, event):
        """Reimplemented."""
        self.__popupIsShown = False
        super(MultiSelectComboBox, self).mousePressEvent(event)
        if self.__popupIsShown:
            self.__initialMousePos = self.mapToGlobal(event.pos())
            self.__blockMouseReleaseTimer.start(
                qtw.QApplication.doubleClickInterval())

    def changeEvent(self, event):
        if event.type() == qtc.QEvent.StyleChange:
            self.__updateItemDelegate()
        super(MultiSelectComboBox, self).changeEvent(event)

    def showPopup(self):
        super(MultiSelectComboBox, self).showPopup()
        view = self.view()
        view.installEventFilter(self)
        view.viewport().installEventFilter(self)
        self.__popupIsShown = True

    def hidePopup(self):
        self.view().removeEventFilter(self)
        self.view().viewport().removeEventFilter(self)
        self.__popupIsShown = False
        self.__initialMousePos = None
        super(MultiSelectComboBox, self).hidePopup()
        self.view().clearFocus()

    def eventFilter(self, obj, event):
        if self.__popupIsShown and \
                event.type() == qtc.QEvent.MouseMove and \
                self.view().isVisible() and self.__initialMousePos is not None:
            diff = obj.mapToGlobal(event.pos()) - self.__initialMousePos
            if diff.manhattanLength() > 9 and \
                    self.__blockMouseReleaseTimer.isActive():
                self.__blockMouseReleaseTimer.stop()
            # pass through

        if self.__popupIsShown and \
                event.type() == qtc.QEvent.MouseButtonRelease and \
                self.view().isVisible() and \
                self.view().rect().contains(event.pos()) and \
                self.view().currentIndex().isValid() and \
                self.view().currentIndex().flags() & qtc.Qt.ItemIsSelectable and \
                self.view().currentIndex().flags() & qtc.Qt.ItemIsEnabled and \
                self.view().currentIndex().flags() & qtc.Qt.ItemIsUserCheckable and \
                self.view().visualRect(self.view().currentIndex()).contains(event.pos()) and \
                not self.__blockMouseReleaseTimer.isActive():
            model = self.model()
            index = self.view().currentIndex()
            state = model.data(index, qtc.Qt.CheckStateRole)
            model.setData(index,
                            qtc.Qt.Checked if state == qtc.Qt.Unchecked else qtc.Qt.Unchecked,
                            qtc.Qt.CheckStateRole)
            self.setCurrentText(model.itemData(index)[0])
            self.view().update(index)
            self.update()
            return True

        if self.__popupIsShown and event.type() == qtc.QEvent.KeyPress:
            if event.key() == qtc.Qt.Key_Space:
                # toogle the current items check state
                model = self.model()
                index = self.view().currentIndex()
                flags = model.flags(index)
                state = model.data(index, qtc.Qt.CheckStateRole)
                if flags & qtc.Qt.ItemIsUserCheckable and \
                        flags & qtc.Qt.ItemIsTristate:
                    state = qtc.Qt.CheckState((int(state) + 1) % 3)
                elif flags & qtc.Qt.ItemIsUserCheckable:
                    state = qtc.Qt.Checked if state != qtc.Qt.Checked else qtc.Qt.Unchecked
                model.setData(index, state, qtc.Qt.CheckStateRole)
                return True
            # TODO: handle Qt.Key_Enter, Key_Return?

        return super(MultiSelectComboBox, self).eventFilter(obj, event)

    # def paintEvent(self, event):
    #     painter = qtw.QStylePainter(self)
    #     option = qtw.QStyleOptionComboBox()
    #     self.initStyleOption(option)
    #     painter.drawComplexControl(qtw.QStyle.CC_ComboBox, option)
    #     # draw the icon and text
    #     checked = self.checkedIndices()
    #     if checked:
    #         items = [self.itemText(i) for i in checked]
    #         option.currentText = self.__separator.join(items)
    #         self.update()
    #     else:
    #         option.currentText = self.__placeholderText
    #         option.palette.setCurrentColorGroup(qtg.QPalette.Disabled)

    # #     option.currentIcon = qtg.QIcon()
    #     # painter.drawControl(qtw.QStyle.CE_ComboBoxLabel, option)

    def itemCheckState(self, index):
        state = self.itemData(index, role=qtc.Qt.CheckStateRole)
        if isinstance(state, int):
            return qtc.Qt.CheckState(state)
        else:
            return qtc.Qt.Unchecked

    def setItemCheckState(self, index, state):
        self.setItemData(index, state, qtc.Qt.CheckStateRole)

    def checkedIndices(self):
        return [i for i in range(self.count())
                if self.itemCheckState(i) == qtc.Qt.Checked]

    def setPlaceholderText(self, text):
        if self.__placeholderText != text:
            self.__placeholderText = text
            self.update()

    def placeholderText(self):
        return self.__placeholderText

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        # Override the default QComboBox behavior
        if event.key() == qtc.Qt.Key_Down and event.modifiers() & qtc.Qt.AltModifier:
            self.showPopup()
            return

        ignored = {qtc.Qt.Key_Up, qtc.Qt.Key_Down,
                    qtc.Qt.Key_PageDown, qtc.Qt.Key_PageUp,
                    qtc.Qt.Key_Home, qtc.Qt.Key_End}

        if event.key() in ignored:
            event.ignore()
            return

        super(MultiSelectComboBox, self).keyPressEvent(event)

    def __updateItemDelegate(self):
        opt = qtw.QStyleOptionComboBox()
        opt.initFrom(self)
        if self.style().styleHint(qtw.QStyle.SH_ComboBox_Popup, opt, self):
            delegate = MultiSelectComboBox.ComboMenuDelegate(self)
        else:
            delegate = MultiSelectComboBox.ComboItemDelegate(self)
        self.setItemDelegate(delegate)