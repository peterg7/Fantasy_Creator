
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# 3rd Party
from tinydb import where

# Built-in Modules
import uuid

# User-defined Modules
from character import Character, UserLineInput
from database import DataFormatter
from storyTime import DateLineEdit

# create Timeline view
class CharacterScroll(qtw.QWidget):

    CharacterDict = {}
    SCALE_TO_FIT_INCREMENT = 0.95 # 95%

    def __init__(self, parent=None):
        print('Initializing scroll...')
        super(CharacterScroll, self).__init__(parent)

        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 10)

        self.scroll = ScrollList()
        # self.scroll.setSizePolicy(qtw.QSizePolicy.Expanding,
        #                             qtw.QSizePolicy.Preferred)

        layout.addWidget(self.scroll)
        self.setLayout(layout)
        self.entry_formatter = DataFormatter()


    def init_scroll(self):
        print('Building scroll...')
        global_events = set()
        known_locations = set()
        event_types = set()
        for event in self.events_db:
            global_events.add(event['event_name'])
        for loc in self.locations_db:
            known_locations.add(loc['location_name'])
        for char in self.character_db:
            for event in char['events']:
                event_types.add(event['event_type'])
        if '' in global_events:
            global_events.remove('')
        if '' in known_locations:
            known_locations.remove('')
        if '' in event_types:
            event_types.remove('')

        EntrySelectionView.GLOBAL_EVENTS.extend(x for x in global_events)
        EntrySelectionView.GLOBAL_EVENTS.append('New...')
        EntrySelectionView.LOCATIONS.extend(x for x in known_locations)
        # EntrySelectionView.LOCATIONS.append('New...')
        EntrySelectionView.EVENT_TYPES.extend(x for x in event_types)
        EntrySelectionView.EVENT_TYPES.append('New...')

            
    def connect_db(self, database):
        # Create tables
        self.meta_db = database.table('meta')
        self.character_db = database.table('characters')
        self.families_db = database.table('families')
        self.kingdoms_db = database.table('kingdoms')
        self.events_db = database.table('events')
        self.locations_db = database.table('locations')

    @qtc.pyqtSlot(list)
    def addChars(self, char_list):
        for char_id in char_list:
            wrapper_item = qtw.QListWidgetItem(self.scroll)
            formatted_char = self.displayable_char(char_id)
            char_entry = ScrollEntry(formatted_char)
            wrapper_item.setSizeHint(char_entry.sizeHint())
            CharacterScroll.CharacterDict[formatted_char['char_id']] = wrapper_item
            self.scroll.addItem(wrapper_item)
            self.scroll.setItemWidget(wrapper_item, char_entry)

        # self.fitWithBorder()
    
    @qtc.pyqtSlot(list)
    def removeChars(self, char_list):
        for char_id in char_list:
            item = CharacterScroll.CharacterDict[char_id]
            entry = self.scroll.itemWidget(item)
            char = entry.getCharacter()
            print(f"Removed {char['name']} - scroll")
            row = self.scroll.row(item)
            self.scroll.takeItem(row)
            del entry
            del item

    @qtc.pyqtSlot(list)
    def updateChars(self, char_list):
        for char_id in char_list:
            item = CharacterScroll.CharacterDict[char_id]
            entry = self.scroll.itemWidget(item)
            formatted_char = self.displayable_char(char_id)
            entry._char = formatted_char
            entry.updateEntry()


    def displayable_char(self, char_id):
        char_record = self.character_db.get(where('char_id') == char_id)
        family_record = self.families_db.get(where('fam_id') == char_record['fam_id'])
        romance_names = ''
        if char_record['partnerships']:
            for relationship in char_record['partnerships']:
                romance_record = self.families_db.get(where('fam_id') == relationship)
                if romance_record:
                    romance_names += (romance_record['fam_name'] + ', ')
        kingdom_record = self.kingdoms_db.get(where('kingdom_id') == char_record['kingdom_id'])

        char_name = char_record['name']
        parent_0_record = self.character_db.get(where('char_id') == char_record['parent_0'])
        if parent_0_record:
            parent_0 = parent_0_record['name']
        else:
            parent_0 = None
        
        parent_1_record = self.character_db.get(where('char_id') == char_record['parent_1'])
        if parent_1_record:
            parent_1 = parent_1_record['name']
        else:
            parent_1 = None
        
        partner_names = []
        for couple in char_record['partnerships']:
            partner = self.character_db.get(where('char_id') == couple['p_id'])
            if partner:
                partner_names.append(partner['name'])

        sex = char_record['sex']
        birth = str(char_record['birth'])
        death = str(char_record['death'])
        ruler = "Yes" if char_record['ruler'] else "No"
        picture= char_record['__IMG__']
        race = char_record['race']
        events = char_record['events']
        notes = char_record['notes']

        if family_record:
            fam_name = family_record['fam_name']
        else:
            fam_name = 'Unnamed'

        if kingdom_record:
            kingdom_name = kingdom_record['kingdom_name']
        else:
            kingdom_name = 'Unnamed'
        
        formatted_events = []
        if events:
            for event in events:
                formatted_events.append(self.displayable_event(event))

        # outline character format
        return {
            'char_id': char_id,
            'name': char_name,
            'family': fam_name,
            'romance': romance_names[:-2],
            'parent_0': parent_0,
            'parent_1': parent_1,
            'partners': partner_names,
            'sex': sex,
            'birth': birth,
            'death': death,
            'ruler': ruler,
            'picture': picture,
            'kingdom': kingdom_name,
            'race': race,
            'events': formatted_events,
            'notes': notes }


    def displayable_event(self, event_dict):
        event_record = self.events_db.get(where('event_id') == event_dict['event_id'])
        location_record = self.locations_db.get(where('location_id') == event_dict['location_id'])

        if event_record:
            event_name = event_record['event_name']
        else:
            event_name = event_dict.get('event_name', None)
        if not event_name:
            event_name = ''
        
        if location_record:
            loc_name = location_record['location_name']
        else:
            loc_name = ''

        event_id = event_dict.get('event_id', None)  
        event_type = event_dict.get('event_type', '')
        start_date = str(event_dict['start'])
        end_date = str(event_dict['end'])
        event_desc = event_dict.get('event_description', '')

        return {
            'event_id': event_id,
            'event_name': event_name,
            'location_name': loc_name,
            'event_type': event_type,
            'start': start_date,
            'end': end_date,
            'event_description': event_desc }
    

    @qtc.pyqtSlot(dict)
    def handleSaveEntry(self, new_vals):
        char_record = self.character_db.get(where('char_id') == new_vals['char_id'])
        char_record['events'] = []
        for event in new_vals['events']:
            if event:
                event_record = self.events_db.get(where('event_name') == event['event_name'])
                location_record = self.locations_db.get(where('location_name') == event['location_name'])

                if location_record:
                        event['location_id'] = location_record['location_id']
                formatted_event = self.entry_formatter.eventEntry(event)

                char_record['events'].append(formatted_event)    

        if new_vals['notes']:
            char_record['notes'] = new_vals['notes']
        self.character_db.update(char_record, where('char_id') == new_vals['char_id'])
                
    def fitWithBorder(self):
        # Expensive method, only want + need to run once
        max_width = -1
        for i in range(self.scroll.count()):
            item = self.scroll.item(i)
            max_width = max(self.scroll.itemWidget(item).width(), max_width)

        scale_factor = self.scroll.width() / max_width

        for i in range(self.scroll.count()):
            item = self.scroll.item(i)
            entry = self.scroll.itemWidget(item)
            entry.scale(scale_factor)
            item.setSizeHint(entry.sizeHint())

        # while entry.width() > self.scroll.width():
        #     entry.scale(CharacterScroll.SCALE_TO_FIT_INCREMENT)

        #     print(self.scroll.size())
        #     print(entry.width())
            
        # item.setSizeHint(entry.sizeHint())


class ScrollEntry(qtw.QWidget):

    BASE_NAME_FONT = 48
    BASE_DISPLAY_FONT = 26

    def __init__(self, char_dict, parent=None):
        super(ScrollEntry, self).__init__(parent)
        self._char = char_dict
    
        name_font = qtg.QFont('Baskerville', 48)
        display_font = qtg.QFont('Baskerville', 26)

        self.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)
        self.layout = qtw.QGridLayout(self)
        self.layout.setSizeConstraint(qtw.QLayout.SetFixedSize)
        self.layout.setSpacing(20)

        # Add image label
        self.prof_pic = qtw.QLabel()
        # self.prof_pic.setScaledContents(True)
        # self.prof_pic.setMinimumSize(100, 100)
        # self.prof_pic.setMaximumSize(200, 200)

        self.layout.addWidget(self.prof_pic, 0, 0, 4, 1)

        # Container for all widget for resizing
        self.list_labels = []
        # Add name/family labels
        self.name_label = qtw.QLabel()
        self.name_label.setFont(name_font)
        self.family_label = qtw.QLabel()
        self.family_label.setFont(display_font)
        self.layout.addWidget(self.name_label, 0, 1, 2, 1)
        self.layout.addWidget(self.family_label, 2, 1, 1, 1)
        self.list_labels.append(self.family_label)

        # Add sex/kingdom labels
        self.sex_label = qtw.QLabel()
        self.sex_label.setFont(display_font)
        self.kingdom_label = qtw.QLabel()
        self.kingdom_label.setFont(display_font)
        self.layout.addWidget(self.sex_label, 2, 3, 1, 1)
        self.layout.addWidget(self.kingdom_label, 2, 2, 1, 1)
        self.list_labels.append(self.sex_label)
        self.list_labels.append(self.kingdom_label)

        # Add race/ruler labels
        self.race_label = qtw.QLabel()
        self.race_label.setFont(display_font)
        self.ruler_label = qtw.QLabel()
        self.ruler_label.setFont(display_font)
        self.layout.addWidget(self.race_label, 1, 3, 1, 1)
        self.layout.addWidget(self.ruler_label, 1, 2, 1, 1)
        self.list_labels.append(self.race_label)
        self.list_labels.append(self.ruler_label)
        
        # Add birth/death labels
        self.birth_label = qtw.QLabel()
        self.birth_label.setFont(display_font)
        self.death_label = qtw.QLabel()
        self.death_label.setFont(display_font)
        self.layout.addWidget(self.birth_label, 1, 4, 1, 1)
        self.layout.addWidget(self.death_label, 2, 4, 1, 1)
        self.list_labels.append(self.birth_label)
        self.list_labels.append(self.death_label)

        # Add parent 1/2 labels
        self.parent1_label = qtw.QLabel()
        self.parent1_label.setFont(display_font)
        self.parent2_label = qtw.QLabel()
        self.parent2_label.setFont(display_font)
        self.layout.addWidget(self.parent1_label, 1, 5, 1, 1)
        self.layout.addWidget(self.parent2_label, 2, 5, 1, 1)
        self.list_labels.append(self.parent1_label)
        self.list_labels.append(self.parent2_label)

        # Add partners labels
        self.partners_label = qtw.QLabel()
        self.partners_label.setFont(display_font)
        self.layout.addWidget(self.partners_label, 1, 6, 1, 1)
        self.list_labels.append(self.partners_label)

        self.updateEntry()

    def getCharacter(self):
        return self._char

    def scale(self, factor):
        name_font = self.name_label.font()
        list_font = self.family_label.font()
        old_height = self.prof_pic.pixmap().height()

        name_offset = name_font.pointSize() * (factor - 1)
        display_offset = list_font.pointSize() * (factor - 1)
        height_offset = old_height * (factor - 1)
        # print(f'name offset: {name_offset}')
        # print(f'display offset: {display_offset}')
        # print(f'pix offset: {height_offset}')

        # if factor < 0:
        #     # name_font.setPointSize(36)
        #     # list_font.setPointSize(20)
        #     name_font.setPointSize(name_font.pointSize() - name_offset)
        #     list_font.setPointSize(list_font.pointSize() - display_offset)
            
        # else:
            # name_font.setPointSize(48)
            # list_font.setPointSize(26)
        name_font.setPointSize(name_font.pointSize() + name_offset)
        list_font.setPointSize(list_font.pointSize() + display_offset)

        # print(name_font.pointSize())
        # print(list_font.pointSize())
        self.name_label.setFont(name_font)
        self.name_label.adjustSize()
        for label in self.list_labels:
            label.setFont(list_font)
            label.adjustSize()
        self.prof_pic.setPixmap(self.pix.scaledToHeight(old_height + height_offset,
                                qtc.Qt.SmoothTransformation))      
        self.layout.invalidate()
        self.adjustSize()
        
        

    def updateEntry(self):
        if img := self._char['picture']:
            if not img.isNull():
                self.pix = qtg.QPixmap.fromImage(img)
                self.prof_pic.setPixmap(self.pix)

        if self._char['name']:
            label_string = self._char['name']
        else:
            label_string = 'Name: ...'
        self.name_label.setText(label_string)
        self.name_label.adjustSize()

        if self._char['family']:
            label_string = f"<b>Family</b>: {self._char['family']}"
        else:
            label_string = 'Family: ...'
        self.family_label.setText(label_string)
        self.family_label.adjustSize()
        
        if self._char['sex']:
            label_string = f"<b>Sex</b>: {self._char['sex']}"
        else:
            label_string = 'Sex: ...'
        self.sex_label.setText(label_string)
        self.sex_label.adjustSize()

        if self._char['kingdom']:
            label_string = f"<b>Kingdom</b>: {self._char['kingdom']}"
        else:
            label_string = 'Kingdom: ...'
        self.kingdom_label.setText(label_string)
        self.kingdom_label.adjustSize()

        if self._char['race']:
            label_string = f"<b>Race</b>: {self._char['race']}"
        else:
            label_string = 'Race: ...'
        self.race_label.setText(label_string)
        self.race_label.adjustSize()

        if self._char['ruler']:
            label_string = f"<b>Ruler</b>: {self._char['ruler']}"
        else:
            label_string = 'Ruler: ...'
        self.ruler_label.setText(label_string)
        self.ruler_label.adjustSize()
        
        if self._char['birth']:
            label_string = f"<b>Birth</b>: {self._char['birth']}"
        else:
            label_string = 'Birth: ...'
        self.birth_label.setText(label_string)
        self.birth_label.adjustSize()

        if self._char['death']:
            label_string = f"<b>Death</b>: {self._char['death']}"
        else:
            label_string = 'Death: ...'
        self.death_label.setText(label_string)
        self.death_label.adjustSize()

        if self._char['parent_0']:
            label_string = f"<b>Parent 1</b>: {self._char['parent_0']}"
        else:
            label_string = 'Parent 1: ...'
        self.parent1_label.setText(label_string)
        self.parent1_label.adjustSize()

        if self._char['parent_1']:
            label_string = f"<b>Parent 2</b>: {self._char['parent_1']}"
        else:
            label_string = 'Parent 2: ...'
        self.parent2_label.setText(label_string)
        self.parent2_label.adjustSize()

        if self._char['partners'] != []:
            label_string = (str(self._char['partners'])[1:-1].strip("'"))
            if len(self._char['partners']) == 1:
                label_string = "<b>Partner</b>: " + label_string
            else:
                label_string = "<b>Partners</b>: " + label_string
        else:
            label_string = 'Partner: ...'
        self.partners_label.setText(label_string)
        self.partners_label.adjustSize()
        self.adjustSize()

        


class ScrollList(qtw.QListWidget):

    def __init__(self, parent=None):
        super(ScrollList, self).__init__(parent)
        # self.setResizeMode(qtw.QListView.Adjust)
        self.setSizeAdjustPolicy(qtw.QListWidget.AdjustToContents)
        # self.setUniformItemSizes(True)
        # self.setFocusPolicy(qtc.Qt.StrongFocus)
        self.setStyleSheet("""
                    QListWidget {
                        background-image: url(:/background-images/scene_bg_1.png);
                        background-position: center;
                    }
                    QListWidget:Item:!selected {
                        border-bottom: 2px solid black;
                    }
        """)

        self.verticalScrollBar().setSingleStep(18)
        self._expandedView = False

    def expand(self):
        self.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        for i in range(self.count()):
            item = self.item(i)
            entry = self.itemWidget(item)
            entry.scale(1.6)
            item.setSizeHint(item.sizeHint() * 1.6)

    def shrink(self):
        self.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Minimum)
        for i in range(self.count()):
            item = self.item(i)
            entry = self.itemWidget(item)
            entry.scale(0.625)
            item.setSizeHint(item.sizeHint() * 0.625)
    
    def scaleEntries(self, factor):
        for i in range(self.count()):
            item = self.item(i)
            entry = self.itemWidget(item)
            entry.scale(factor)
            item.setSizeHint(item.sizeHint() * factor)

    def _updateItemDelegate(self):
        opt = qtw.QStyleOptionViewItem()
        opt.initFrom(self)
        if self.style().styleHint(qtw.QStyle.SH_ListViewExpand_SelectMouseType, opt, self):
            delegate = CharacterScroll.ListItemDelegate(self)
            self.setItemDelegate(delegate)
        # else:
    

    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:
            self.clearSelection()
        super(ScrollList, self).keyPressEvent(event)
    
    # def sizeHint(self):
    #         size = qtc.QSize()
    #         size.setHeight(super(ScrollList, self).sizeHint().height())
    #         size.setWidth(self.sizeHintForColumn(0))
    #         print('asdjf;')
    #         return size

    # class ListItemDelegate(qtw.QAbstractItemDelegate):

    #     def __init__(self, parent=None):
    #         super(ScrollList.ListDelegate, self).__init__(parent)


    # class ListViewDelegate(qtw.QStyledItemDelegate)


class EntrySelectionView(qtw.QWidget):

    GLOBAL_EVENTS = ['Event Name...']
    LOCATIONS = ['Select Location...']
    EVENT_TYPES = ['Select Category...']

    saved_values = qtc.pyqtSignal(dict)
    status_message = qtc.pyqtSignal(str, int)

    def __init__(self, char_dict, parent=None):
        super(EntrySelectionView, self).__init__(parent)
        # self._char = char_dict
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.name_font = qtg.QFont('Baskerville', 62, italic=True)
        self.display_font = qtg.QFont('Baskerville', 22)
        self.header_font = qtg.QFont('Baskerville', 28)
        self.RULER_PIC = qtg.QPixmap(Character.RULER_PIC_PATH)
        self.current_events = [] # keep track of events
        self.edited_events = []
        self.current_notes = ''
        self.profile_pixmap = None
        self.ruler_pixmap = None

        layout = qtw.QHBoxLayout()
        widget_groupbox = qtw.QGroupBox()

        # layout for basic info
        info_layout = qtw.QGridLayout()
        # info_layout.setHorizontalSpacing(20)
        # info_layout.setVerticalSpacing(10)
        # info_layout.setSpacing(20)
        # info_layout.setContentsMargins(10, 0, 0, 10)
        # info_layout.setSizeConstraint(qtw.QLayout.SetMinimumSize)

        self.name_label = qtw.QLabel()
        self.name_label.setFont(self.name_font)

        image_layout = qtw.QVBoxLayout()
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)
        image_layout.setAlignment(qtc.Qt.AlignHCenter)
        self.profile_pic = qtw.QLabel()
        self.profile_pic.setSizePolicy(qtw.QSizePolicy.Expanding,
                                        qtw.QSizePolicy.Expanding)
        self.profile_pic.setMinimumSize(100, 100)
        self.profile_pic.setMaximumSize(200, 200)

        self.ruler_picture = qtw.QLabel()
        self.ruler_picture.setSizePolicy(qtw.QSizePolicy.Expanding,
                                        qtw.QSizePolicy.Expanding)
        # self.ruler_picture.setContentsMargins(0, 0, 0, 15)
        self.ruler_picture.setAlignment(qtc.Qt.AlignHCenter)
        self.ruler_picture.setMinimumSize(69, 40)
        self.ruler_picture.setMaximumSize(150, 87)

        image_layout.addWidget(self.ruler_picture)
        image_layout.addWidget(self.profile_pic)
        
        self.birth_label = qtw.QLabel()
        self.birth_label.setFont(self.display_font)
        # self.birth_label.setWordWrap(True)
        self.death_label = qtw.QLabel()
        self.death_label.setFont(self.display_font)
        # self.death_label.setWordWrap(True)
        # info_layout.setRowMinimumHeight(1, self.RULER_PIC.height())
        info_layout.addWidget(self.name_label, 0, 1, 1, 2, qtc.Qt.AlignHCenter)
        # info_layout.addWidget(self.ruler_picture, 1, 1, 2, 1)#, qtc.Qt.AlignHCenter)
        # info_layout.addWidget(self.profile_pic, 2, 1, 5, 1)#, qtc.Qt.AlignHCenter)
        info_layout.addLayout(image_layout, 1, 1, 6, 2, qtc.Qt.AlignHCenter)
        info_layout.addWidget(self.birth_label, 8, 0, 1, 2)
        info_layout.addWidget(self.death_label, 8, 2, 1, 2, qtc.Qt.AlignRight)

        right_col_layout = qtw.QVBoxLayout()
        self.sex_label = qtw.QLabel()
        self.sex_label.setFont(self.display_font)
        self.sex_label.setSizePolicy(
            qtw.QSizePolicy.Preferred, 
            qtw.QSizePolicy.Minimum)
        self.sex_label.setWordWrap(True)
        self.race_label = qtw.QLabel()
        self.race_label.setFont(self.display_font)
        self.race_label.setSizePolicy(
            qtw.QSizePolicy.Preferred, 
            qtw.QSizePolicy.Minimum)
        self.race_label.setWordWrap(True)
        # self.family_label = qtw.QLabel()
        # self.family_label.setFont(self.display_font)
        # self.family_label.setSizePolicy(
        #     qtw.QSizePolicy.Preferred, 
        #     qtw.QSizePolicy.Minimum)
        # self.family_label.setWordWrap(True)
        # self.parent1_label = qtw.QLabel()
        # self.parent1_label.setFont(self.display_font)
        # self.parent1_label.setSizePolicy(
        #     qtw.QSizePolicy.Preferred, 
        #     qtw.QSizePolicy.Minimum)
        # self.parent1_label.setWordWrap(True)
        # self.parent2_label = qtw.QLabel()
        # self.parent2_label.setFont(self.display_font)
        # self.parent2_label.setSizePolicy(
        #     qtw.QSizePolicy.Preferred, 
        #     qtw.QSizePolicy.Minimum)
        # self.parent2_label.setWordWrap(True)
        # self.kingdom_label = qtw.QLabel()
        # self.kingdom_label.setFont(self.display_font)
        # self.kingdom_label.setSizePolicy(
        #     qtw.QSizePolicy.Preferred, 
        #     qtw.QSizePolicy.Minimum)
        # self.kingdom_label.setWordWrap(True)
        # self.partners_label = qtw.QLabel()
        # self.partners_label.setFont(self.display_font)
        # self.partners_label.setSizePolicy(
        #     qtw.QSizePolicy.Preferred, 
        #     qtw.QSizePolicy.Minimum)
        # self.partners_label.setWordWrap(True)
        info_layout.addWidget(self.sex_label, 7, 0, 1, 2)
        info_layout.addWidget(self.race_label, 7, 2, 1, 2, qtc.Qt.AlignRight)
        # info_layout.addWidget(self.family_label, 4, 2, 1, 1)
        # info_layout.addWidget(self.parent1_label, 5, 2, 1, 1)
        # info_layout.addWidget(self.parent2_label, 6, 2, 1, 1)
        # info_layout.addWidget(self.kingdom_label, 7, 2, 1, 1)
        # info_layout.addWidget(self.partners_label, 8, 2, 1, 1)

        main_spacer1 = qtw.QSpacerItem(15, 50, 
                qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)

        # Events layout
        event_layout = qtw.QVBoxLayout()
        events_header = qtw.QLabel('Notable Events')
        events_header.setFont(self.header_font)
        event_layout.addWidget(events_header)

        self.events_list = EventsList()
        # self.events_list.setSizePolicy(
        #     qtw.QSizePolicy.Preferred,
        #     qtw.QSizePolicy.MinimumExpanding
        # )
        # self.events_list.setFont(qtg.QFont('Baskerville', 20))
        event_layout.addWidget(self.events_list)

        list_manager_spacer = qtw.QSpacerItem(10, 10, qtw.QSizePolicy.Minimum,
                                                qtw.QSizePolicy.Minimum)
        event_layout.addItem(list_manager_spacer)

        # Add location groupbox
        event_entry_group = qtw.QGroupBox('Manage Events')
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Preferred)
        sizePolicy.setVerticalStretch(1)
        event_entry_group.setSizePolicy(sizePolicy)
        event_entry_group.setFont(qtg.QFont('Baskerville', 16))
        add_event_layout = qtw.QGridLayout()

        self.location_name = qtw.QComboBox()
        self.event_name = qtw.QComboBox()
        self.event_category = qtw.QComboBox()
        self.event_start = DateLineEdit()
        self.event_end = DateLineEdit()
        self.event_details = qtw.QTextEdit()
        self.add_event_btn = qtw.QPushButton('Add/Update')
        self.del_event_btn = qtw.QPushButton('Delete')

        # Manage widgets
        self.event_name.addItems(EntrySelectionView.GLOBAL_EVENTS)
        self.event_name.model().item(0).setEnabled(False)

        self.location_name.addItems(EntrySelectionView.LOCATIONS)
        self.location_name.model().item(0).setEnabled(False)

        self.event_category.addItems(EntrySelectionView.EVENT_TYPES)
        self.event_category.model().item(0).setEnabled(False)

        self.event_details.setMinimumSize(0, 60)
        self.event_details.setMaximumSize(2000, 250)
        self.event_details.setPlaceholderText('Description...')

        start_time_layout = qtw.QHBoxLayout()
        end_time_layout = qtw.QHBoxLayout()
        start_time_label = qtw.QLabel('From')
        start_time_label.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        start_time_label.setFont(qtg.QFont('Baskerville', 16))
        # start_time_layout.addWidget(start_time_label)

        end_time_layout = qtw.QHBoxLayout()
        end_time_label = qtw.QLabel('To')
        end_time_label.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        end_time_label.setFont(qtg.QFont('Baskerville', 16))
        # end_time_layout.addWidget(end_time_label)
        
        self.event_start.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )
        self.event_end.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred
        )

        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.event_start)
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(self.event_end)

        self.add_event_btn.setFont(qtg.QFont('Baskerville', 16))
        self.del_event_btn.setFont(qtg.QFont('Baskerville', 16))
        
        add_event_layout.addWidget(self.event_name, 1, 1, 1, 2)
        add_event_layout.addLayout(start_time_layout, 1, 3)
        add_event_layout.addLayout(end_time_layout, 2, 3)
        add_event_layout.addWidget(self.location_name, 2, 1, 1, 2)
        add_event_layout.addWidget(self.event_category, 3, 1, 1, 2)
        add_event_layout.addWidget(self.event_details, 4, 1, 1, 3)
        add_event_layout.addWidget(self.del_event_btn, 5, 2)
        add_event_layout.addWidget(self.add_event_btn, 5, 3)
        # add_event_layout.setColumnMinimumWidth(1, 50)
        # add_event_layout.setColumnStretch(0, 1)
        # add_event_layout.setColumnStretch(0, 1.2)

        event_entry_group.setLayout(add_event_layout)
        event_layout.addWidget(event_entry_group)

        main_spacer2 = qtw.QSpacerItem(15, 50, 
                qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)
        
        # Character notes 
        notes_layout = qtw.QVBoxLayout()
        notes_header_layout = qtw.QHBoxLayout()
        notes_header = qtw.QLabel('Character Notes')
        notes_header.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Minimum
        )
        notes_header.setFont(self.header_font)
        self.cancel_btn = qtw.QPushButton('X')
        self.cancel_btn.setStyleSheet(""" 
                    QPushButton {
                        border-color: rgb(150, 150, 150);
                        border-width: 2px;        
                        border-style: inset;
                        border-radius: 12px;
                        /*padding: 5px;*/
                        color: rgb(150, 150, 150);
                        background-color: rgba(185, 185, 185, 50);
                    }
                    QPushButton:pressed { 
                        background-color: rgba(185, 185, 185, 75);
                    }
        """)
        self.cancel_btn.setFixedSize(24, 24)
        notes_header_layout.addWidget(notes_header)
        notes_header_layout.addWidget(self.cancel_btn)

        self.cancel_btn.pressed.connect(self.saveEdits)

        format_layout = qtw.QHBoxLayout()
        self.font_family = qtw.QFontComboBox(self)
        self.font_family.setCurrentText('Baskerville')
        self.font_family.currentFontChanged.connect(self.updateFontFamily)
 
        self.font_size = qtw.QComboBox(self)
        self.font_size.setEditable(True)
        self.font_size.setMinimumContentsLength(3)
        # self.font_size.activated.connect(self.updateFontSize)
        
        font_sizes = [6,7,8,9,10,11,12,13,14,15,16,18,20,22,24,26,28,32,36,40,44,48,
                 54,60,66,72,80,88,96]
         
        for size in font_sizes:
            self.font_size.addItem(str(size))
        self.font_size.setCurrentText(str(16))
        self.font_size.setFont(qtg.QFont('Baskerville', 16))
        # font_color_act = qtg.QAction(QIcon("icons/color.png"),"Change font color",self)
        # fontColor.triggered.connect(self.FontColor)
        format_btn_list = []

        self.bold_btn = qtw.QToolButton(self)
        self.bold_btn.setIcon(qtg.QIcon(":/map-icons/edit-bold.png"))
        self.bold_btn.setText("Bold")
        self.bold_btn.setCheckable(True)
        self.bold_btn.clicked.connect(self.Bold)
        format_btn_list.append(self.bold_btn)
         
        self.italic_btn = qtw.QToolButton(self)
        self.italic_btn.setIcon(qtg.QIcon(":/map-icons/edit-italic.png"))
        self.italic_btn.setText("Italic")
        self.italic_btn.setCheckable(True)
        self.italic_btn.clicked.connect(self.Italic)
        format_btn_list.append(self.italic_btn)
         
        self.underline_btn = qtw.QToolButton(self)
        self.underline_btn.setIcon(qtg.QIcon(":/map-icons/edit-underline.png"))
        self.underline_btn.setText("Underline")
        self.underline_btn.setCheckable(True)
        self.underline_btn.clicked.connect(self.Underline)
        format_btn_list.append(self.underline_btn)
 
        self.align_left_btn = qtw.QToolButton(self)
        self.align_left_btn.setIcon(qtg.QIcon(":/map-icons/align-left.png"))
        self.align_left_btn.setText("Align left")
        self.align_left_btn.clicked.connect(self.alignLeft)
        format_btn_list.append(self.align_left_btn)
 
        self.align_center_btn = qtw.QToolButton(self)
        self.align_center_btn.setIcon(qtg.QIcon(":/map-icons/align-center.png"))
        self.align_center_btn.setText("Align center")
        self.align_center_btn.clicked.connect(self.alignCenter)
        format_btn_list.append(self.align_center_btn)
 
        self.align_right_btn = qtw.QToolButton(self)
        self.align_right_btn.setIcon(qtg.QIcon(":/map-icons/align-right.png"))
        self.align_right_btn.setText("Align right")
        self.align_right_btn.clicked.connect(self.alignRight)
        format_btn_list.append(self.align_right_btn)
 
        # alignJustify = QAction(QIcon(":/icons/map/alignJustify.png"),"Align justify",self)
        # alignJustify.triggered.connect(self.alignJustify)

        # indent_btn = qtw.QToolButton(self)
        # indent_btn.setIcon(qtg.QIcon(":/map-icons/indent.png"))
        # indent_btn.setText("Indent Area")
        # indent_btn.setShortcut("Ctrl+Tab")
        # indent_btn.clicked.connect(self.Indent)
        # format_btn_list.append(indent_btn)
 
        # dedent_btn = qtw.QToolButton(self)
        # dedent_btn.setIcon(qtg.QIcon(":/map-icons/dedent.png"))
        # dedent_btn.setText("Dedent Area")
        # dedent_btn.setShortcut("Shift+Tab")
        # dedent_btn.clicked.connect(self.Dedent)
        # format_btn_list.append(dedent_btn)
 
        # backColor = QAction(QIcon("icons/backcolor.png"),"Change background color",self)
        # backColor.triggered.connect(self.FontBackColor)
 
        # self.bullet_btn = qtw.QToolButton(self)
        # self.bullet_btn.setIcon(qtg.QIcon(":/map-icons/bullet-list.png"))
        # self.bullet_btn.setText("Insert Bullet List")
        # self.bullet_btn.clicked.connect(self.BulletList)
        # format_btn_list.append(self.bullet_btn)
 
        # self.numbered_btn = qtw.QToolButton(self)
        # self.numbered_btn.setIcon(qtg.QIcon(":/map-icons/numbered-list.png"))
        # self.numbered_btn.setText("Insert Numbered List")
        # self.numbered_btn.clicked.connect(self.NumberedList)
        # format_btn_list.append(self.numbered_btn)

        for btn in format_btn_list:
            btn.setToolButtonStyle(qtc.Qt.ToolButtonIconOnly)
            # if btn not in [indent_btn, dedent_btn, self.bullet_btn, self.numbered_btn]:
            #     btn.setCheckable(True)
        # space1 = qtw.QLabel("  ",self)
        # space2 = qtw.QLabel(" ",self)
        # space3 = qtw.QLabel(" ",self)
        format_spacer1 = qtw.QSpacerItem(10, 10, 
                qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        format_spacer2 = qtw.QSpacerItem(10, 10, 
                qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
         
 
        # self.formatbar = self.addToolBar("Format")
        format_layout.addWidget(self.font_family)
        format_layout.addWidget(self.font_size)

        format_layout.addStretch(1)
        # self.formatbar.addWidget(fontColor)
        # self.formatbar.addAction(backColor)
         
        format_layout.addWidget(self.bold_btn)
        format_layout.addWidget(self.italic_btn)
        format_layout.addWidget(self.underline_btn)
         
        format_layout.addItem(format_spacer1)
 
        format_layout.addWidget(self.align_left_btn)
        format_layout.addWidget(self.align_center_btn)
        format_layout.addWidget(self.align_right_btn)
        # self.formatbar.addAction(alignJustify)
 
        # format_layout.addItem(format_spacer2)
 
        # format_layout.addWidget(indent_btn)
        # format_layout.addWidget(dedent_btn)
        # format_layout.addWidget(self.bullet_btn)
        # format_layout.addWidget(self.numbered_btn)

        notes_layout.addLayout(notes_header_layout)
        notes_groupbox = qtw.QGroupBox()
        notes_groupbox_layout = qtw.QVBoxLayout()
        self.character_notes = qtw.QTextEdit()
        self.character_notes.setTabStopWidth(12)
        # self.character_notes.setFontPointSize(12)

        self.character_notes.document().setDefaultFont(qtg.QFont('Baskerville', 16))
        self.character_notes.setCurrentFont(qtg.QFont('Baskerville', 16))

        self.font_size.currentTextChanged.connect(self.updateFontSize)
        self.character_notes.cursorPositionChanged.connect(self.checkCursor)
        self.character_notes.textChanged.connect(notes_groupbox.repaint)

        # notes_groupbox.setSizePolicy(
        #     qtw.QSizePolicy.Preferred,
        #     qtw.QSizePolicy.MinimumExpanding
        # )
        notes_groupbox_layout.addLayout(format_layout)
        notes_groupbox_layout.addWidget(self.character_notes)
        # notes_groupbox_layout.addWidget(self.save_btn)
        notes_groupbox.setLayout(notes_groupbox_layout)
        notes_layout.addWidget(notes_groupbox)

        self.cancel_btn.clicked.connect(self.close)

        layout.addLayout(info_layout)
        layout.addItem(main_spacer1)
        layout.addLayout(event_layout)
        layout.addItem(main_spacer2)
        layout.addLayout(notes_layout)
        layout.setStretch(0, 1)
        layout.setStretch(2, 1.35)
        layout.setStretch(4, 2)
        widget_groupbox.setLayout(layout)
        widget_groupbox.setSizePolicy(
            qtw.QSizePolicy.Expanding,
            qtw.QSizePolicy.Preferred
        )
        master_layout = qtw.QHBoxLayout()
        master_layout.addWidget(widget_groupbox)
        self.setLayout(master_layout)
        self.updateEntry(char_dict)

        self.events_list.itemSelectionChanged.connect(self.populateForm)
        self.events_list.itemSelectionChanged.connect(self.checkDeleteBtn)
        self.event_name.currentTextChanged.connect(self.onNameChange)
        # self.location_name.currentTextChanged.connect(self.onLocationChange)
        self.event_category.currentTextChanged.connect(self.onCategoryChange)
        self.add_event_btn.clicked.connect(self.commitEvent)
        self.del_event_btn.clicked.connect(self.dropEvent)



    def updateEntry(self, char_dict):
        self._char = char_dict
        self._id = self._char['char_id']
        if img := self._char['picture']:
            if not img.isNull():
                self.profile_pixmap = qtg.QPixmap.fromImage(img)
            else:
                self.profile_pixmap = None
        else:
            self.profile_pixmap = None

        if self._char['name']:
            label_string = self._char['name']
        else:
            label_string = 'Name: ...'
        self.name_label.setText(label_string)
        self.name_label.adjustSize()

        # if self._char['family']:
        #     label_string = f"<b>Family</b>: {self._char['family']}"
        # else:
        #     label_string = 'Family: ...'
        # self.family_label.setText(label_string)
        # self.family_label.adjustSize()
        
        if self._char['sex']:
            label_string = f"<b>Sex</b>: {self._char['sex']}"
        else:
            label_string = 'Sex: ...'
        self.sex_label.setText(label_string)
        self.sex_label.adjustSize()

        # if self._char['kingdom']:
        #     label_string = f"<b>Kingdom</b>: {self._char['kingdom']}"
        # else:
        #     label_string = 'Kingdom: ...'
        # self.kingdom_label.setText(label_string)
        # self.kingdom_label.adjustSize()

        if self._char['race']:
            label_string = f"<b>Race</b>: {self._char['race']}"
        else:
            label_string = 'Race: ...'
        self.race_label.setText(label_string)
        self.race_label.adjustSize()

        if self._char['ruler']:
            label_string = self._char['ruler'].casefold()
            if label_string == 'yes':
                self.ruler_pixmap = self.RULER_PIC
            else:    
                self.ruler_picture.clear()
                self.ruler_pixmap = None
        else:    
            self.ruler_picture.clear()
            self.ruler_pixmap = None
        
        if self._char['birth']:
            label_string = f"<b>Birth</b>:<br>{self._char['birth']}"
        else:
            label_string = 'Birth: ...'
        self.birth_label.setText(label_string)

        if self._char['death']:
            label_string = f"<b>Death</b>:<br>{self._char['death']}"
        else:
            label_string = 'Death: ...'
        self.death_label.setText(label_string)

        # if self._char['parent_0']:
        #     label_string = f"<b>Parent 1</b>: {self._char['parent_0']}"
        # else:
        #     label_string = 'Parent 1: ...'
        # self.parent1_label.setText(label_string)
        # self.parent1_label.adjustSize()

        # if self._char['parent_1']:
        #     label_string = f"<b>Parent 2</b>: {self._char['parent_1']}"
        # else:
        #     label_string = 'Parent 2: ...'
        # self.parent2_label.setText(label_string)
        # self.parent2_label.adjustSize()

        # if self._char['partners'] != []:
        #     label_string = (str(self._char['partners'])[1:-1].strip("'"))
        #     if len(self._char['partners']) == 1:
        #         label_string = "<b>Partner</b>: " + label_string
        #     else:
        #         label_string = "<b>Partners</b>: " + label_string
        # else:
        #     label_string = 'Partner: ...'
        # self.partners_label.setText(label_string)
        # self.partners_label.adjustSize()

        self.edited_events = []
        self.current_events.clear()
        if self._char['events']:
            for event_dict in self._char['events']:
                self.current_events.append(event_dict)

        self.current_notes = ''
        if self._char['notes']:
            self.current_notes = self._char['notes']
        self.populateList()
        self.populateNotes()
        self.updatePics()
        self.update()

    def updatePics(self):
        if self.profile_pixmap:
            self.profile_pic.setPixmap(self.profile_pixmap.scaled(
                                        self.profile_pic.width(),
                                        self.profile_pic.height(),
                                        qtc.Qt.KeepAspectRatio))
        if self.ruler_pixmap:
            self.ruler_picture.setPixmap(self.ruler_pixmap.scaled(
                                        self.ruler_picture.width(),
                                        self.ruler_picture.height(),
                                        qtc.Qt.KeepAspectRatio))


    @qtc.pyqtSlot()
    def saveEdits(self):
        self.saved_values.emit({
            'char_id': self._id,
            'events': self.current_events,
            'notes': self.character_notes.toHtml()
        })
        self.edited_events = []


    def populateNotes(self):
        self.character_notes.blockSignals(True)
        self.character_notes.clear()
        self.character_notes.blockSignals(False)
        self.character_notes.insertHtml(self.current_notes)

    def checkDeleteBtn(self):
        self.del_event_btn.setDisabled(self.events_list.currentRow() == -1)

    def onNameChange(self, text):
        if text == 'New...':
            # text, ok = qtw.QInputDialog.getText(self, 'Create new event', 'Enter name:')
            text, ok = UserLineInput.requestInput("Create new event", "Enter name:", self)
            if ok and text:
                self.event_name.addItem(text)
                EntrySelectionView.GLOBAL_EVENTS.insert(len(EntrySelectionView.GLOBAL_EVENTS)-2, text)
                self.event_name.setCurrentText(text)
            else:
                self.event_name.setCurrentIndex(0)

    # def onLocationChange(self, text):
    #     if text == 'New...':
    #         # text, ok = qtw.QInputDialog.getText(self, 'Define new location', 'Enter location:')
    #         text, ok = UserLineInput.requestInput("Define new location", "Enter location:", self)
    #         if ok:
    #             self.location_name.addItem(text)
    #             EntrySelectionView.LOCATIONS.insert(len(EntrySelectionView.LOCATIONS)-1, text)
    #             self.location_name.setCurrentText(text)
    #         else:
    #             self.location_name.setCurrentIndex(0)

    def onCategoryChange(self, text):
        if text == 'New...':
            # text, ok = qtw.QInputDialog.getText(self, 'Define other event type', 'Enter category:')
            text, ok = UserLineInput.requestInput("Define other event type", "Enter category:", self)
            if ok and text:
                self.event_category.addItem(text)
                EntrySelectionView.EVENT_TYPES.insert(len(EntrySelectionView.EVENT_TYPES)-2, text)
                self.event_category.setCurrentText(text)
            else:
                self.event_category.setCurrentIndex(0)

    def dropEvent(self):
        index = self.events_list.currentRow()
        if index != -1:
            # value = list(self.current_events.values())[index]
            del self.current_events[index]
            self.events_list.setCurrentRow(-1)
            self.clearForm()
            self.populateList()

    def commitEvent(self):
        if self.event_name.currentText() == "Event Name...":
            self.status_message.emit("Event must have a name", 4000)
            return

        event = {
            'event_id': None,
            'event_name': self.event_name.currentText(),
            'location_name': self.location_name.currentText(),
            'event_type': self.event_category.currentText(),
            'start': self.event_start.getDate()[0],
            'end': self.event_end.getDate()[0],
            'event_description': self.event_details.toPlainText()
        }
        # event_index = self.events_list.currentRow()
        event_index = -1
        for index, seeker in enumerate(self.current_events):
            if event['event_name'] == seeker['event_name']:
                # print([x for x in self.current_events])
                event_index = index
                break

        if event_index == -1 or event_index >= len(self.current_events):
            self.current_events.append(event)

        if event_index < len(self.current_events):
            event['event_id'] = self.current_events[event_index].get('event_id', None)
            self.current_events[event_index] = event
        self.populateList()
    

    def populateList(self):
        self.events_list.blockSignals(True)
        self.events_list.clear()
        self.events_list.blockSignals(False)
        self.clearForm()
        for event in self.current_events:
            name = event['event_name']
            location = event['location_name']
            start = event['start']
            end = event['end']
            wrapper = qtw.QListWidgetItem(self.events_list)
            event_entry = EventListEntry()
            event_entry.populateEntry(name, location, start, end)
            wrapper.setSizeHint(event_entry.sizeHint())
            self.events_list.addItem(wrapper)
            self.events_list.setItemWidget(wrapper, event_entry)
    
    def populateForm(self):
        self.clearForm()
        event_index = self.events_list.currentRow()
        if event_index == -1:
            return
        data = self.current_events[event_index]

        self.event_name.setCurrentText(data['event_name'])
        self.location_name.setCurrentText(data['location_name'])
        self.event_category.setCurrentText(data['event_type'])
        self.event_start.setText(str(data['start']))
        self.event_end.setText(str(data['end']))
        self.event_details.setPlainText(data['event_description'])


    def clearForm(self):
        self.event_name.setCurrentIndex(0)
        self.location_name.setCurrentIndex(0)
        self.event_category.setCurrentIndex(0)
        self.event_start.clear()
        self.event_end.clear()
        self.event_details.setPlainText('')
        self.update()
    
    def Undo(self):
        self.character_notes.undo()
    
    def Redo(self):
        self.character_notes.redo()
    
    def Cut(self):
        self.character_notes.cut()
    
    def Copy(self):
        self.character_notes.copy()
    
    def Paste(self):
        self.character_notes.paste()
    
    def updateFontFamily(self, font):
        font = qtg.QFont(self.font_family.currentFont())
        self.character_notes.setCurrentFont(font)
    
    def updateFontSize(self, font_size):
        try:
            size = int(font_size)
            if size > 0:
                self.character_notes.setFontPointSize(size)
        except ValueError:
            return
    
    def Bold(self):
        current_weight = self.character_notes.fontWeight()
        if current_weight == qtg.QFont.Normal:
            self.character_notes.setFontWeight(qtg.QFont.Bold)
        elif current_weight == qtg.QFont.Bold:
            self.character_notes.setFontWeight(qtg.QFont.Normal)

    def Italic(self):
        self.character_notes.setFontItalic(not self.character_notes.fontItalic())
    
    def Underline(self):
        self.character_notes.setFontUnderline(not self.character_notes.fontUnderline())

    def alignLeft(self):
        if not self.align_left_btn.isDown():
            self.align_left_btn.setDown(True)
            self.align_center_btn.setDown(False)
            self.align_right_btn.setDown(False)
            self.character_notes.setAlignment(qtc.Qt.AlignLeft)
            
    
    def alignCenter(self):
        if not self.align_center_btn.isDown():
            self.align_left_btn.setDown(False)
            self.align_center_btn.setDown(True)
            self.align_right_btn.setDown(False)
            self.character_notes.setAlignment(qtc.Qt.AlignCenter)
            
    
    def alignRight(self):
        if not self.align_right_btn.isDown():
            self.align_left_btn.setDown(False)
            self.align_center_btn.setDown(False)
            self.align_right_btn.setDown(True)
            self.character_notes.setAlignment(qtc.Qt.AlignRight)
            
 
    def BulletList(self):
        self.character_notes.insertHtml("<ul><li>...</li></ul>")
 
    def NumberedList(self):
        self.character_notes.insertHtml("<ol><li>...</li></ol>")
    
    def checkCursor(self):
        cursor = self.character_notes.textCursor()

        # start = cursor.selectionStart()
        # end = cursor.selectionEnd()
        current_format = cursor.charFormat()
        self.font_family.blockSignals(True)
        self.font_size.blockSignals(True)
        self.font_family.setCurrentFont(current_format.font())
        
        self.font_size.setCurrentText(str(int(current_format.fontPointSize())))
        self.font_family.blockSignals(False)
        self.font_size.blockSignals(False)

        self.bold_btn.setDown(current_format.fontWeight() == qtg.QFont.Bold)
        self.italic_btn.setDown(current_format.fontItalic())
        self.underline_btn.setDown(current_format.fontUnderline())

        alignment = self.character_notes.alignment()
        if alignment == qtc.Qt.AlignLeft:
            self.align_left_btn.setDown(True)
            self.align_center_btn.setDown(False)
            self.align_right_btn.setDown(False)
        
        elif alignment == qtc.Qt.AlignCenter:
            self.align_left_btn.setDown(False)
            self.align_center_btn.setDown(True)
            self.align_right_btn.setDown(False)
        
        elif alignment == qtc.Qt.AlignRight:
            self.align_left_btn.setDown(False)
            self.align_center_btn.setDown(False)
            self.align_right_btn.setDown(True)


class EventListEntry(qtw.QWidget):

    def __init__(self, parent=None):
        super(EventListEntry, self).__init__(parent)
        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Minimum
        )
        self.setContentsMargins(10, 5, 10, 5)
        display_style = """
            QLabel { 
                font-family: Baskerville;
                font-size: 16px; 
            }"""
        self.empty_display = """
            QLabel { 
                font-family: Baskerville;
                font-size: 16px;
                font-style: italic; 
                color: gray; 
            }"""

        self.name_label = qtw.QLabel()
        self.name_label.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        self.name_label.setStyleSheet("""
            QLabel { 
                font-family: Baskerville;
                font-size: 18px; 
            }""")
        self.name_label.setContentsMargins(0, 0, 0, 0)

        self.loc_label = qtw.QLabel()
        self.loc_label.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        self.loc_label.setStyleSheet("""
            QLabel { 
                font-family: Baskerville;
                font-size: 16px;
                font-style: italic; 
            }""")
        self.loc_label.setContentsMargins(0, 0, 0, 0)

        self.start_label = qtw.QLabel()
        self.start_label.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        self.start_label.setStyleSheet(display_style)
        self.start_label.setContentsMargins(0, 0, 0, 0)

        self.end_label = qtw.QLabel()
        self.end_label.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        self.end_label.setStyleSheet(display_style)
        self.end_label.setContentsMargins(0, 0, 0, 0)

        layout = qtw.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setVerticalSpacing(0)
        
        layout.addWidget(self.name_label, 0, 0, 1, 1, qtc.Qt.AlignLeft)
        layout.addWidget(self.start_label, 0, 1, 1, 1, qtc.Qt.AlignRight)
        layout.addWidget(self.loc_label, 1, 0, 1, 1, qtc.Qt.AlignLeft)
        layout.addWidget(self.end_label, 1, 1, 1, 1, qtc.Qt.AlignRight)
        self.setLayout(layout)
        
    def populateEntry(self, name, loc, start, end):
        if not name or name == '':
            self.name_label.setText('Name...')
            self.name_label.setStyleSheet(self.empty_display)
        else: 
            self.name_label.setText(name)
        if not loc or loc == '':
            self.loc_label.setText('Location...')
            self.loc_label.setStyleSheet(self.empty_display)
        else:
            self.loc_label.setText(loc)
        if not start:
            self.start_label.setText('Dates...')
            self.start_label.setStyleSheet(self.empty_display)
            self.end_label.setText('')
        else:
            self.start_label.setText(f'{start} -')
            self.end_label.setText(f'{end}')

class EventsList(qtw.QListWidget):

    class EventsListDelegate(qtw.QStyledItemDelegate):

        def __init__(self, parent=None):
            super(EventsList.EventsListDelegate, self).__init__(parent)
        
        # def sizeHint(self, option, index):
        #     return qtc.QSize(150, 65)

    
    def __init__(self, parent=None):
        super(EventsList, self).__init__(parent)
        delegate = self.EventsListDelegate(self)
        self.setItemDelegate(delegate)
    
    def mousePressEvent(self, event):
        self.clearSelection()
        self.setCurrentRow(-1)
        self.itemSelectionChanged.emit()
        super(EventsList, self).mousePressEvent(event)
    
