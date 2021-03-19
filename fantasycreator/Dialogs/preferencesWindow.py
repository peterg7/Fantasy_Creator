
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# 3rd Party
from tinydb import where

class PreferencesWindow(qtw.QDialog):

    pref_change = qtc.pyqtSignal(list)

    def __init__(self, database, parent=None):
        super(PreferencesWindow, self).__init__(parent)

        self.setModal(True)

        self.font = qtg.QFont('Baskerville', 14)
        self.font_metric = qtg.QFontMetrics(self.font)

        main_layout = qtw.QVBoxLayout()
        pref_layout = qtw.QHBoxLayout()

        self.listMenu = qtw.QListWidget()
        self.listMenu.insertItem(0, 'General')
        self.listMenu.insertItem(1, 'World Mechanics')
        self.listMenu.insertItem(2, 'Family Tree')
        self.listMenu.insertItem(3, 'Timeline')
        self.listMenu.insertItem(4, 'Map Builder')
        self.listMenu.insertItem(5, 'Character Scroll')

        self.general_stack = GeneralStack(self)
        self.general_stack.setFont(self.font)
        # self.general_stack.setParent(self)
        self.mechanics_stack = MechanicsStack(self)
        self.mechanics_stack.setFont(self.font)
        self.tree_stack = TreeStack(self)
        self.tree_stack.setFont(self.font)
        self.timeline_stack = TimeStack(self)
        self.timeline_stack.setFont(self.font)
        self.map_stack = MapStack(self)
        self.map_stack.setFont(self.font)
        self.scroll_stack = ScrollStack(self)
        self.scroll_stack.setFont(self.font)

        self.stack = qtw.QStackedWidget(self)
        self.stack.addWidget(self.general_stack)
        self.stack.addWidget(self.mechanics_stack)
        self.stack.addWidget(self.tree_stack)
        # self.stack.addWidget(self.timeline_stack)
        # self.stack.addWidget(self.map_stack)
        # self.stack.addWidget(self.scroll_stack)

        pref_layout.addWidget(self.listMenu)
        pref_layout.addWidget(self.stack)

        buttons_layout = qtw.QHBoxLayout()
        self.cancel_button = qtw.QPushButton(
            'Cancel',
            pressed=self.close
        )
        self.cancel_button.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.cancel_button.setFont(self.font)
        self.submit_button = qtw.QPushButton(
            'Submit',
            pressed=self.onSubmit
        )
        self.submit_button.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.submit_button.setFont(self.font)
        self.submit_button.setDefault(True)

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.submit_button)

        main_layout.addLayout(pref_layout)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
        self.listMenu.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.resize(600, 450)
        self.setWindowTitle('Preferences')

        self.preferences_db = database.table('preferences')
        self.distributePreferences()
    

    def distributePreferences(self):
        for panel in self.preferences_db:
            stack = getattr(self, '%s_stack' % panel['tab'], None)
            if stack:
                stack.loadPrefs(panel)
    
    def gatherPreferences(self):
        preferences = []
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            preferences.append(widget.packagePrefs())
            self.preferences_db.update(preferences[-1], where('tab') == widget.objectName())
        return preferences
    
    def onSubmit(self):
        pref_list = self.gatherPreferences()
        self.pref_change.emit(pref_list)
        self.close()



class GeneralStack(qtw.QWidget):

    def __init__(self, parent=None):
        super(GeneralStack, self).__init__(parent)
        self.setObjectName('general')

        stack_layout = qtw.QVBoxLayout()
        
        # Book details
        book_groupbox = qtw.QGroupBox('Book')
        book_groupbox.setFont(qtg.QFont('Baskerville', 15))
        book_layout = qtw.QFormLayout()
        self.book_title = qtw.QLineEdit()
        book_layout.addRow('Book Title', self.book_title)
        book_groupbox.setLayout(book_layout)
        book_groupbox.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)

        # World details
        world_groupbox = qtw.QGroupBox('World Details')
        world_groupbox.setFont(qtg.QFont('Baskerville', 15))
        details_layout = qtw.QFormLayout()
        self.world_name = qtw.QLineEdit()
        details_layout.addRow('World Name', self.world_name)
        world_groupbox.setLayout(details_layout)
        world_groupbox.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        
        stack_layout.addWidget(book_groupbox)
        stack_layout.addWidget(world_groupbox)
        self.setLayout(stack_layout)

        # Connect signals
        # self.book_title.textChanged.connect(lambda x: PreferencesWindow.pref_change.emit('general', 'book_title', x))
        # self.world_name.textChanged.connect(lambda x: PreferencesWindow.pref_change.emit('general', 'world_name', x))

    
    def loadPrefs(self, preferences):
        title = preferences.get('book_title', None)
        if title:
            self.book_title.setText(title)
        world = preferences.get('world_name', None)
        if world:
            self.world_name.setText(world)
    
    @qtc.pyqtSlot()
    def packagePrefs(self):
        return {
            'tab': self.objectName(),
            'book_title': self.book_title.text(),
            'world_name': self.world_name.text()
        }
        


class MechanicsStack(qtw.QWidget):

    def __init__(self, parent=None):
        super(MechanicsStack, self).__init__(parent)
        self.setObjectName('mechanics')

        stack_layout = qtw.QVBoxLayout()
        
        # Date Formatting
        time_groupbox = qtw.QGroupBox('Time')
        time_groupbox.setFont(qtg.QFont('Baskerville', 15))
        
        top_layout = qtw.QHBoxLayout()
        time_layout = qtw.QVBoxLayout()

        time_format_layout = qtw.QFormLayout()
        time_format_layout.setVerticalSpacing(45)
        time_format_layout.setContentsMargins(5, 22, 5, 5)
        self.day_format = qtw.QLineEdit()
        time_format_layout.addRow('Day\nFormat', self.day_format)
        self.month_format = qtw.QLineEdit()
        time_format_layout.addRow('Month\nFormat', self.month_format)
        self.year_format = qtw.QLineEdit()
        time_format_layout.addRow('Year\nFormat', self.year_format)
        
        
        time_values = ['Day', 'Month', 'Year']
        time_order_layout = qtw.QHBoxLayout()
        self.first_time = qtw.QComboBox()
        self.first_time.addItems(time_values)
        self.first_time.setCurrentIndex(2)
        self.first_time.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        time_order_layout.addWidget(self.first_time)

        spacer_1 = qtw.QLabel('•')
        spacer_1.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Minimum
        )
        time_order_layout.addWidget(spacer_1)

        self.second_time = qtw.QComboBox()
        self.second_time.addItems(time_values)
        self.second_time.setCurrentIndex(1)
        self.second_time.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        time_order_layout.addWidget(self.second_time)

        spacer_2 = qtw.QLabel('•')
        spacer_2.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Minimum
        )
        time_order_layout.addWidget(spacer_2)

        self.third_time = qtw.QComboBox()
        self.third_time.addItems(time_values)
        self.third_time.setCurrentIndex(0)
        self.third_time.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        time_order_layout.addWidget(self.third_time)
        top_layout.addLayout(time_format_layout)

        self.first_time.currentIndexChanged.connect(lambda x: self.propogate_selection(1, x))
        self.second_time.currentIndexChanged.connect(lambda x: self.propogate_selection(2, x))
        self.third_time.currentIndexChanged.connect(lambda x: self.propogate_selection(3, x))


        time_range_layout = qtw.QFormLayout()
        # time_range_layout.setSpacing(20)
        time_range_layout.setVerticalSpacing(28)
        time_range_layout.setContentsMargins(5, 5, 5, 5)
        year_range_layout = qtw.QVBoxLayout()

        day_range_layout = qtw.QVBoxLayout()
        self.day_min = qtw.QLineEdit()
        self.day_min.setValidator(qtg.QIntValidator(2, 200, self))
        day_range_layout.addWidget(self.day_min)
        self.day_max = qtw.QLineEdit()
        self.day_max.setValidator(qtg.QIntValidator(2, 500, self))
        day_range_layout.addWidget(self.day_max)
        time_range_layout.addRow('Day\nRange', day_range_layout)

        month_range_layout = qtw.QVBoxLayout()
        self.month_min = qtw.QLineEdit()
        self.month_min.setValidator(qtg.QIntValidator(1, 200, self))
        month_range_layout.addWidget(self.month_min)
        self.month_max = qtw.QLineEdit()
        self.month_max.setValidator(qtg.QIntValidator(1, 500, self))
        month_range_layout.addWidget(self.month_max)
        time_range_layout.addRow('Month\nRange', month_range_layout)

        self.year_min = qtw.QLineEdit()
        self.year_min.setValidator(qtg.QIntValidator(1, 10000, self))
        year_range_layout.addWidget(self.year_min)
        self.year_max = qtw.QLineEdit()
        self.year_max.setValidator(qtg.QIntValidator(1, 100000, self))
        year_range_layout.addWidget(self.year_max)
        time_range_layout.addRow('Year\nRange', year_range_layout)

        top_layout.addLayout(time_range_layout)

        time_layout.addLayout(top_layout)
        time_layout.addLayout(time_order_layout)
        time_groupbox.setLayout(time_layout)
        
        stack_layout.addWidget(time_groupbox)
        self.setLayout(stack_layout)
    

    def propogate_selection(self, combobox, index):
        indicies = [0, 1, 2]
        indicies.remove(index)
        if combobox == 1:
            second_index = self.second_time.currentIndex()
            third_index = self.third_time.currentIndex()
            if second_index == index:
                indicies.remove(third_index)
                self.second_time.setCurrentIndex(indicies[0])
            elif third_index == index:
                indicies.remove(second_index)
                self.third_time.setCurrentIndex(indicies[0])

        elif combobox == 2:
            third_index = self.third_time.currentIndex()
            first_index = self.first_time.currentIndex()
            if third_index == index:
                indicies.remove(first_index)
                self.third_time.setCurrentIndex(indicies[0])
            elif first_index == index:
                indicies.remove(third_index)
                self.first_time.setCurrentIndex(indicies[0])

        elif combobox == 3:
            first_index = self.first_time.currentIndex()
            second_index = self.second_time.currentIndex()
            if first_index == index:
                indicies.remove(second_index)
                self.first_time.setCurrentIndex(indicies[0])
            elif second_index == index:
                indicies.remove(first_index)
                self.second_time.setCurrentIndex(indicies[0])


    def loadPrefs(self, preferences):
        year_form = preferences.get('year_format', None)
        if year_form:
            self.year_format.setText('#' * year_form)
        month_form = preferences.get('month_format', None)
        if month_form:
            self.month_format.setText('#' * month_form)
        day_form = preferences.get('day_format', None)
        if day_form:
            self.day_format.setText('#' * day_form)
        year_rng = preferences.get('year_range', None)
        if year_rng:
            self.year_min.setText(str(year_rng[0]))
            self.year_max.setText(str(year_rng[1]))
        month_rng = preferences.get('month_range', None)
        if month_rng:
            self.month_min.setText(str(month_rng[0]))
            self.month_max.setText(str(month_rng[1]))
        day_rng = preferences.get('day_range', None)
        if day_rng:
            self.day_min.setText(str(day_rng[0]))
            self.day_max.setText(str(day_rng[1]))
        time_ord = preferences.get('time_order', None)
        if time_ord:
            order = dict((val, key) for key, val in time_ord.items())
            self.first_time.setCurrentText(order['ONE'].title())
            self.second_time.setCurrentText(order['TWO'].title())
            self.third_time.setCurrentText(order['THREE'].title())
    
    @qtc.pyqtSlot()
    def packagePrefs(self):
        return {
            'tab': self.objectName(),
            'year_format': len(self.year_format.text()),
            'month_format': len(self.month_format.text()),
            'day_format': len(self.day_format.text()),
            'year_range': (int(self.year_min.text()), 
                            int(self.year_max.text())),
            'month_range': (int(self.month_min.text()), 
                            int(self.month_max.text())),
            'day_range': (int(self.day_min.text()), 
                            int(self.day_max.text())),
            'time_order': {
                self.first_time.currentText().lower(): 'ONE',
                self.second_time.currentText().lower(): 'TWO',
                self.third_time.currentText().lower(): 'THREE'
            }
        }



class TreeStack(qtw.QWidget):
    
    def __init__(self, parent=None):
        super(TreeStack, self).__init__(parent)
        self.setObjectName('tree')

        main_layout = qtw.QVBoxLayout()

        spacing_group = qtw.QGroupBox('Spacing')
        spacing_group.setFont(qtg.QFont('Baskerville', 15))

        spacing_layout = qtw.QHBoxLayout()
        column1_layout = qtw.QFormLayout()
        self.gen_spacing = qtw.QSpinBox()
        self.gen_spacing.setMinimum(200)
        self.gen_spacing.setMaximum(500)
        self.gen_spacing.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.gen_spacing.setMinimumSize(qtc.QSize(55, 20))
        self.gen_spacing.setMaximumSize(qtc.QSize(55, 20))
        column1_layout.addRow('Generation\nSpacing', self.gen_spacing)
        self.desc_drop = qtw.QSpinBox()
        self.desc_drop.setMinimum(0)
        self.desc_drop.setMaximum(250)
        self.desc_drop.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.desc_drop.setMinimumSize(qtc.QSize(55, 20))
        self.desc_drop.setMaximumSize(qtc.QSize(55, 20))
        column1_layout.addRow('Descendant\nDropdown', self.desc_drop)
        self.expand_fact = qtw.QSpinBox()
        self.expand_fact.setMinimum(5)
        self.expand_fact.setMaximum(35)
        self.expand_fact.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.expand_fact.setMinimumSize(qtc.QSize(55, 20))
        self.expand_fact.setMaximumSize(qtc.QSize(55, 20))
        column1_layout.addRow('Expansion\nFactor', self.expand_fact)
        expand_label = column1_layout.labelForField(self.expand_fact)
        expand_label.setToolTip('This is used to stretch the tree horizontally')
        # expand_desc.setWordWrap(True)
        # expand_desc.setFont(qtg.QFont('Baskerville', 12))
        # column1_layout.addRow('', expand_desc)

        column2_layout = qtw.QFormLayout()
        self.sibling_spacing = qtw.QSpinBox()
        self.sibling_spacing.setMinimum(25)
        self.sibling_spacing.setMaximum(200)
        self.sibling_spacing.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.sibling_spacing.setMinimumSize(qtc.QSize(55, 20))
        self.sibling_spacing.setMaximumSize(qtc.QSize(55, 20))
        column2_layout.addRow('Sibling\nSpacing', self.sibling_spacing)
        self.part_spacing = qtw.QSpinBox()
        self.part_spacing.setMinimum(100)
        self.part_spacing.setMaximum(350)
        self.part_spacing.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.part_spacing.setMinimumSize(qtc.QSize(55, 20))
        self.part_spacing.setMaximumSize(qtc.QSize(55, 20))
        column2_layout.addRow('Partner\nSpacing', self.part_spacing)
        self.offset_fact = qtw.QSpinBox()
        self.offset_fact.setMinimum(1)
        self.offset_fact.setMaximum(25)
        self.offset_fact.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.offset_fact.setMinimumSize(qtc.QSize(55, 20))
        self.offset_fact.setMaximumSize(qtc.QSize(55, 20))
        column2_layout.addRow('Offset\nFactor', self.offset_fact)
        offset_label = column2_layout.labelForField(self.offset_fact)
        offset_label.setToolTip('This is used to stretch each level proportional to the height and number of siblings')
        # offset_desc.setFont(qtg.QFont('Baskerville', 12))
        # column2_layout.addRow('', offset_desc)

        spacing_layout.addLayout(column1_layout, qtc.Qt.AlignLeft)
        spacing_layout.addLayout(column2_layout, qtc.Qt.AlignRight)
        spacing_group.setLayout(spacing_layout)

        sizing_layout = qtw.QHBoxLayout()

        char_group = qtw.QGroupBox('Characters')
        char_group.setFont(qtg.QFont('Baskerville', 15))
        char_layout = qtw.QHBoxLayout()
        left_char_layout = qtw.QFormLayout()
        self.char_width = qtw.QSpinBox()
        self.char_width.setMinimum(50)
        self.char_width.setMaximum(300)
        self.char_width.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.char_width.setMinimumSize(qtc.QSize(55, 20))
        self.char_width.setMaximumSize(qtc.QSize(55, 20))
        left_char_layout.addRow('Character\nImage W.', self.char_width)
        self.char_height = qtw.QSpinBox()
        self.char_height.setMinimum(50)
        self.char_height.setMaximum(300)
        self.char_height.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.char_height.setMinimumSize(qtc.QSize(55, 20))
        self.char_height.setMaximumSize(qtc.QSize(55, 20))
        left_char_layout.addRow('Character\nImage H.', self.char_height)

        char_layout.addLayout(left_char_layout)
        char_group.setLayout(char_layout)

        crown_group = qtw.QGroupBox('Crown')
        crown_group.setFont(qtg.QFont('Baskerville', 15))

        crown_layout = qtw.QHBoxLayout()
        #TODO LineEdit + Display label for crown image
        left_crown_layout = qtw.QFormLayout()
        self.crown_height = qtw.QSpinBox()
        self.crown_height.setMinimum(10)
        self.crown_height.setMaximum(100)
        self.crown_height.setSizePolicy(
            qtw.QSizePolicy.Fixed,
            qtw.QSizePolicy.Fixed )
        self.crown_height.setMinimumSize(qtc.QSize(55, 20))
        self.crown_height.setMaximumSize(qtc.QSize(55, 20))
        left_crown_layout.addRow('Crown\nHeight', self.crown_height)

        crown_layout.addLayout(left_crown_layout, qtc.Qt.AlignLeft)
        crown_group.setLayout(crown_layout)

        sizing_layout.addWidget(char_group)
        sizing_layout.addWidget(crown_group)

        main_layout.addWidget(spacing_group)
        main_layout.addLayout(sizing_layout)
        self.setLayout(main_layout)




    def loadPrefs(self, preferences):
        if gen_spacing := preferences.get('generation_spacing', None):
            self.gen_spacing.setValue(gen_spacing)
        if sib_spacing := preferences.get('sibling_spacing', None):
            self.sibling_spacing.setValue(sib_spacing)
        if desc_dropdown := preferences.get('desc_dropdown', None):
            self.desc_drop.setValue(desc_dropdown)
        if expand_fact := preferences.get('expand_factor', None):
            self.expand_fact.setValue(expand_fact)
        if offset_fact := preferences.get('offset_factor', None):
            self.offset_fact.setValue(offset_fact)
        if crown_size := preferences.get('ruler_crown_size', None):
            self.crown_height.setValue(crown_size)
        # crown_img = preferences.get('ruler_crown_img', None):
        if char_width := preferences.get('char_img_width', None):
            self.char_width.setValue(char_width)
        if char_height := preferences.get('char_img_height', None):
            self.char_height.setValue(char_height)
        

    @qtc.pyqtSlot()
    def packagePrefs(self):
        return {
            'tab': self.objectName(),
            'generation_spacing': self.gen_spacing.value(),
            'sibling_spacing': self.sibling_spacing.value(),
            'desc_dropdown': self.desc_drop.value(),
            'expand_factor': self.expand_fact.value(),
            'offset_factor': self.offset_fact.value(),
            'ruler_crown_size': self.crown_height.value(),
            'char_img_width': self.char_width.value(),
            'char_img_height': self.char_height.value()
        }


class TimeStack(qtw.QWidget):

    def __init__(self, parent=None):
        super(TimeStack, self).__init__(parent)
        self.setObjectName('timeline')

    def loadPrefs(self, preferences):
        min_year = preferences.get('min_year', None)
        max_year = preferences.get('max_year', None)
        time_periods = preferences.get('time_periods', None)
    
    @qtc.pyqtSlot()
    def packagePrefs(self):
        return {
            'tab': self.objectName()
        }


class MapStack(qtw.QWidget):

    def __init__(self, parent=None):
        super(MapStack, self).__init__(parent)
        self.setObjectName('map')
    
    def loadPrefs(self, preferences):
        pass

    @qtc.pyqtSlot()
    def packagePrefs(self):
        return {
            'tab': self.objectName()
        }


class ScrollStack(qtw.QWidget):

    def __init__(self, parent=None):
        super(ScrollStack, self).__init__(parent)
        self.setObjectName('scroll')

    def loadPrefs(self, preferences):
        pass

    @qtc.pyqtSlot()
    def packagePrefs(self):
        return {
            'tab': self.objectName()
        }