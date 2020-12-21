
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# 3rd party
from tinydb import where

# Built-in Modules
import uuid

# User-defined Modules
from hashList import HashList
from character import CharacterView, CharacterCreator
from timelineEntries import TimelineCharEntry, MainTimelineAxis, TimelineEntry
from timelineEntries import TimelineEventEntry, EntryView, EventCreator
from materializer import Materializer
from storyTime import TimeConstants, Time
from database import DataFormatter
from flags import EVENT_TYPE, DIRECTION

# create Timeline view
class TimelineView(qtw.QGraphicsView):

    updatedChars = qtc.pyqtSignal(list)
    zoomChanged = qtc.pyqtSignal(int)
    setEventDel = qtc.pyqtSignal(bool)

    MIN_YEAR = -1
    MAX_YEAR = -1

    SCENE_WIDTH = 8500
    SCENE_HEIGHT = 3000
    SCENE_BOUNDS = (0, 0, 8500, 3000)

    EVENT_AXIS = 200
    START_ENTRY_AXIS = 250
    ENTRY_SPACING = 35
    TIMELINE_PADDING = 100
    BORDER_X = 50
    BORDER_Y = 60
    DFLT_VIEW = qtc.QRectF(2500, 150, 3500, 1000)
    MAIN_AXIS_MIN = 0
    MAIN_AXIS_MAX = 0
    MAIN_AXIS_PADDING = 25

    MIN_ZOOM = -8
    MAX_ZOOM = 8

    CharacterList = HashList() # Stores all CHARACTER ENTRY objects
    CharacterOrder = {}
    FamilyColors = {}
    EventList = HashList() # Stores all EVENT ENTRY objects

    def __init__(self, parent=None):
        print('Initializing timeline...')
        super(TimelineView, self).__init__(parent)
        self.scene = TimelineScene(self)
        self.setScene(self.scene)
        self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setRenderHints(qtg.QPainter.Antialiasing | qtg.QPainter.SmoothPixmapTransform)
        self.viewport().grabGesture(qtc.Qt.PinchGesture)
        self.viewport().setAttribute(qtc.Qt.WA_AcceptTouchEvents)

        # self.setDragMode(qtw.QGraphicsView.ScrollHandDrag)

        self.entry_formatter = DataFormatter()

        self.zoom_factor = 1
        self.current_factor = 1
        self.zoomStatus = 0
        self.zoom_tracker = 0 

        self.char_views = []
        self.event_views = []
        self._pan = False
        self._pan_act = False
        self.zoomStatus = 0
        self._mousePressed = False
        self.current_color = 0
        self.last_mouse = None
        

    def init_timeline_view(self):
        self.materializer = Materializer()

        min_date = TimeConstants.MIN_TIME[:]
        max_date = TimeConstants.MAX_TIME[:]

        min_date.addYears(self.TIMELINE_PADDING)
        max_date.addYears(-self.TIMELINE_PADDING)

        TimelineEntry.MAIN_AXIS_MAX = self.materializer.mapTime(max_date)
        TimelineEntry.MAIN_AXIS_MIN = self.materializer.mapTime(min_date)

        self.main_axis = MainTimelineAxis(min_date, max_date)

        self.scene.add_axis(self.main_axis)
        self.main_axis.setX(self.materializer.mapTime(min_date))
        self.main_axis.drawIntervals()

        self.build_timeline()

    def build_timeline(self):
        print('Building timeline...')
        y_spacing = TimelineCharEntry.ENTRY_HEIGHT + TimelineView.ENTRY_SPACING
        current_family = None
        rom_id = None
        num_colors = len(TimelineEntry.COLORS)
        known_families = [fam['fam_id'] for fam in self.families_db.all()]
        TimelineView.FamilyColors = dict(zip(known_families, TimelineEntry.COLORS))
        ordered_chars = sorted(self.character_db.all(), key=lambda x: x['timeline_ord'])
        for index, char in enumerate(self.character_db):
            birth = char['birth']
            death = char['death']
            if char['partnerships']:
                rom_id = char['partnerships'][0]['rom_id']
            fam_id = char['fam_id']
            
            if fam_id in known_families:
                self.current_color = known_families.index(fam_id)
            elif rom_id in known_families:
                self.current_color = known_families.index(rom_id)
            else:
                self.current_color = 0
            if self.current_color >= num_colors:
                    self.current_color %= num_colors 
                    TimelineView.FamilyColors[fam_id] = TimelineEntry.COLORS[self.current_color]

            char_entry = TimelineCharEntry(char['char_id'], char['name'], 
                                        TimelineEntry.COLORS[self.current_color], index)
            char_entry.setY(TimelineView.START_ENTRY_AXIS + (index * y_spacing))
            char_entry.stopped_movement.connect(self.handleEntryMovement)
            char_entry.add_edit.connect(self.add_character_edit)
            char_entry.add_view.connect(self.add_character_view)
            char_entry.shift_entry.connect(self.shiftCharEntry)
            self.scene.addEntryToScene(char_entry)
            char_entry.setTimeInterval(birth, death)
            TimelineView.CharacterOrder[index] = char_entry
            TimelineView.CharacterList.add(char_entry)
        
        TimelineView.EVENT_AXIS = TimelineView.START_ENTRY_AXIS - (MainTimelineAxis.AXIS_HEIGHT + (1.35 * y_spacing))
        for index, event in enumerate(self.events_db):
            start = event['start']
            end = event['end']
            event_entry = TimelineEventEntry(event['event_id'], event['event_name'])
            event_entry.setY(TimelineView.EVENT_AXIS)
            event_entry.stopped_movement.connect(self.handleEntryMovement)
            event_entry.add_edit.connect(self.add_event_edit)
            event_entry.add_view.connect(self.add_event_view)
            event_entry.del_entry.connect(self.deleteEvent)
            self.scene.addEntryToScene(event_entry)
            event_entry.setTimeInterval(start, end)
            TimelineView.EventList.add(event_entry)
        

    def connect_db(self, database):
        # Create tables
        self.meta_db = database.table('meta')
        self.character_db = database.table('characters')
        self.families_db = database.table('families')
        self.kingdoms_db = database.table('kingdoms')
        self.events_db = database.table('events')
        self.locations_db = database.table('locations')

    def init_event_dialogs(self):
        locations = set()
        _types = set()
        for loc in self.locations_db:
            locations.add(loc['location_name'])
        for event in self.events_db:
            _types.add(event['event_type'])

        if '' in locations:
            locations.remove('')
        if '' in _types:
            _types.remove('')

        EventCreator.LOC_ITEMS.extend(x for x in locations)
        # EventCreator.LOC_ITEMS.append('Other...')
        EventCreator.TYPE_ITEMS.extend(x for x in _types)
        EventCreator.TYPE_ITEMS.append('Other...')


    
    @qtc.pyqtSlot(bool)
    def toggle_panning(self, state):
        self._pan = state
        self._pan_act = state
        self._mousePressed = False
        if self._pan:
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)
        else:
            self.viewport().unsetCursor()
    
    @qtc.pyqtSlot()
    def check_event_dlt_button(self):
        if not self.event_views:
            self.setEventDel.emit(False)
            EntryView.CURRENT_SPAWN = qtc.QPoint(20, 50) # NOTE: Magic Number
        else:
            self.setEventDel.emit(True)
    

    def calcCharDateSpan(self, char_list):
        sorted_birth = sorted(char_list, key=lambda x: x['birth'].getYear())
        sorted_death = sorted(char_list, key=lambda x: x['death'].getYear(), reverse=True)
        min_date = sorted_birth[0]['birth']
        max_date = sorted_death[0]['death']
        return (min_date, max_date)


    @qtc.pyqtSlot(uuid.UUID, bool)
    def toggleCharViz(self, char_id, state):
        char_entry = TimelineView.CharacterList.search(char_id)[0]
        if char_entry:
            char_entry.setVisible(state)

    @qtc.pyqtSlot(bool)
    def handleTimeChange(self, reorder):
        self.scene.removeItem(self.main_axis)
        del self.main_axis
        
        min_date = TimeConstants.MIN_TIME[:]
        max_date = TimeConstants.MAX_TIME[:]

        min_date.addYears(self.TIMELINE_PADDING)
        max_date.addYears(-self.TIMELINE_PADDING)

        TimelineEntry.MAIN_AXIS_MAX = self.materializer.mapTime(max_date)
        TimelineEntry.MAIN_AXIS_MIN = self.materializer.mapTime(min_date)

        self.main_axis = MainTimelineAxis(min_date, max_date)

        self.scene.add_axis(self.main_axis)
        self.main_axis.setX(self.materializer.mapTime(min_date))
        self.main_axis.drawIntervals()

        for entry in TimelineView.CharacterList:
            entry.shiftClocks(reorder)

        for entry in TimelineView.EventList:
            entry.shiftClocks(reorder)

        self.fitWithBorder()


    @qtc.pyqtSlot()
    def build_event(self):
        self.new_event_dialog = EventCreator(self)
        self.new_event_dialog.submitted.connect(self.processNewEvent)
        self.new_event_dialog.show()

    @qtc.pyqtSlot()
    def character_selected(self):
        if self.last_mouse == 'Single':
            if len(self.scene.selectedItems()) > 0: # at least one character selected
                selected_item = self.scene.selectedItems()[0] # NOTE: only using "first" item
                if isinstance(selected_item, TimelineCharEntry):
                    self.add_character_view(selected_item.getID())
                elif isinstance(selected_item, TimelineEventEntry):
                    self.add_event_view(selected_item.getID())
        elif self.last_mouse == 'Double':
            if len(self.scene.selectedItems()) > 0: # at least one character selected
                selected_item = self.scene.selectedItems()[0] # NOTE: only using "first" item
                if isinstance(selected_item, TimelineCharEntry):
                    self.add_character_edit(selected_item.getID())
                    
    
    @qtc.pyqtSlot(int, uuid.UUID, Time, Time)
    def handleEntryMovement(self, entry_type, entry_id, new_start, new_end):
        if entry_type == EVENT_TYPE.CHAR:
            self.character_db.update({'birth': new_start, 'death': new_end}, 
                                                where('char_id') == entry_id)
            self.updatedChars.emit([entry_id])
        elif entry_type == EVENT_TYPE.EVENT:
            self.events_db.update({'start': new_start, 'end': new_end},
                                                where('event_id') == entry_id)

    @qtc.pyqtSlot(dict)
    def receiveCharacterUpdate(self, char_dict):
        family_name = char_dict.pop('family', None)
        kingdom_name = char_dict.pop('kingdom', None)
        # Merge dicts
        updated_dict = {**self.character_db.get(where('char_id') == char_dict['char_id']), **char_dict}        
        # TODO: Assert the user wants to change the ENTIRE family name (or check to start a new one)
        if not self.families_db.contains(where('fam_name') == family_name):
            self.families_db.update({'fam_name': family_name}, 
                                where('fam_id') == updated_dict['fam_id'])

        # TODO: Assert the user wants to change the ENTIRE kingdom name (or check to start a new one)
        if not self.kingdoms_db.contains(where('kingdom_name') == kingdom_name):
            self.kingdoms_db.update({'kingdom_name': kingdom_name},
                                where('kingdom_id') == updated_dict['kingdom_id'])
        elif not updated_dict['kingdom_id']:
            updated_dict['kingdom_id'] = self.kingdoms_db.get(where('kingdom_name') == kingdom_name)['kingdom_id']

        formatted_dict = self.entry_formatter.char_entry(updated_dict)
        update = self.character_db.update(formatted_dict, where('char_id') == formatted_dict['char_id'])
        if update:
            entry = TimelineView.CharacterList.search(formatted_dict['char_id'])
            if entry:
                entry[0].updateInterval(formatted_dict['birth'], formatted_dict['death'])
            self.updatedChars.emit([formatted_dict['char_id']])
    
    @qtc.pyqtSlot(dict)
    def receiveEventUpdate(self, event_dict):
        location_name = event_dict.pop('location', None)
        merged_dict = {**self.events_db.get(where('event_id') == event_dict['event_id']), ** event_dict}

        if location := self.locations_db.get(where('location_name') == location_name):
            merged_dict['location_id'] = location['location_id']
        else:
            merged_dict['location_id'] = self.meta_db.all()[0]['NULL_ID']
        
        formatted_dict = self.entry_formatter.eventEntry(merged_dict)
        update = self.events_db.update(formatted_dict, where('event_id') == formatted_dict['event_id'])
        if update:
            entry = TimelineView.EventList.search(formatted_dict['event_id'])
            if entry:
                entry[0].updateInterval(formatted_dict['start'], formatted_dict['end'])


    @qtc.pyqtSlot(list)
    def addChars(self, char_list):
        TimelineView.START_ENTRY_AXIS = self.START_ENTRY_AXIS
        spacing = TimelineCharEntry.ENTRY_HEIGHT + self.ENTRY_SPACING
        index = len(TimelineView.CharacterList)
        rom_id = None
        for char_id in char_list:
            if char_id not in TimelineView.CharacterList:
                char = self.character_db.get(where('char_id') == char_id)
                birth = char['birth']
                death = char['death']
                if char['partnerships']:
                    rom_id = char['partnerships'][0]['rom_id']
                fam_id = char['fam_id']
                if fam_id in TimelineView.FamilyColors:
                    color = TimelineView.FamilyColors[fam_id]
                elif rom_id in TimelineView.FamilyColors:
                    color = TimelineView.FamilyColors[rom_id]
                else:
                    self.current_color += 1
                    if self.current_color > len(TimelineEntry.COLORS):
                        self.current_color = 0
                    color = TimelineEntry.COLORS[self.current_color]
                    TimelineView.FamilyColors[fam_id] = color
                char_entry = TimelineCharEntry(char['char_id'], char['name'], color, index)
                char_entry.setY(TimelineView.START_ENTRY_AXIS + (index * spacing))
                char_entry.stopped_movement.connect(self.handleEntryMovement)
                char_entry.add_edit.connect(self.add_character_edit)
                char_entry.add_view.connect(self.add_character_view)
                char_entry.shift_entry.connect(self.shiftCharEntry)
                self.scene.addEntryToScene(char_entry)
                char_entry.setTimeInterval(birth, death)
                TimelineView.CharacterOrder[index] = char_entry
                TimelineView.CharacterList.add(char_entry)
                index += 1


    @qtc.pyqtSlot(list)
    def removeChars(self, char_list):
        for char_id in char_list:
            entry_index = self.scene.current_entries.index(char_id)
            char = self.scene.current_entries[entry_index]
            print(f'Removed {char} - timeline')
            child = self.findChild(EntryView, 'view{}'.format(char_id))
            if child:
                child.close()
            self.scene.removeEntryFromScene(char)
            TimelineView.CharacterList.remove(char)
            del char
            for index in range(entry_index, len(self.scene.current_entries)):
                entry = self.scene.current_entries[index]
                if isinstance(entry, TimelineCharEntry):
                    self.shiftCharEntry(entry, DIRECTION.UP)
        self.scene.update()
    
    @qtc.pyqtSlot(list)
    def updateChars(self, char_list):
        for char_id in char_list:
            char_record = self.character_db.get(where('char_id') == char_id)
            entry = TimelineView.CharacterList.search(char_id)
            if entry:
                entry[0].updateInterval(char_record['birth'], char_record['death'])
                
    
    @qtc.pyqtSlot(int, uuid.UUID)
    def shiftCharEntry(self, direction, entry_id):
        if entry := TimelineView.CharacterList.search(entry_id):
            entry = entry[0]
            spacing = TimelineCharEntry.ENTRY_HEIGHT + self.ENTRY_SPACING
            if direction == DIRECTION.UP:
                if entry._order <= 0:
                    return
                spacing = -spacing
                swapped_entry = TimelineView.CharacterOrder[entry._order - 1]
            elif direction == DIRECTION.DOWN:
                if entry._order >= len(TimelineView.CharacterList) - 1:
                    return
                swapped_entry = TimelineView.CharacterOrder[entry._order + 1]
            
            entry.shiftEntry(spacing)
            swapped_entry.shiftEntry(-spacing)
            TimelineView.CharacterOrder[entry._order], TimelineView.CharacterOrder[swapped_entry._order] = (
                TimelineView.CharacterOrder[swapped_entry._order], TimelineView.CharacterOrder[entry._order])
            entry._order, swapped_entry._order = swapped_entry._order, entry._order

    @qtc.pyqtSlot(dict)
    def processNewEvent(self, event_dict):
        if existing_loc := self.locations_db.get(where('location_name') == event_dict['location']):
            existing_loc = existing_loc['location_id']
        event_dict['location_id'] = existing_loc
        formatted_dict = self.entry_formatter.eventEntry(event_dict)
        self.events_db.insert(formatted_dict)
        start = formatted_dict['start']
        end = formatted_dict['end']
        event_entry = TimelineEventEntry(formatted_dict['event_id'], formatted_dict['event_name'])
        event_entry.setY(TimelineView.EVENT_AXIS)
        event_entry.stopped_movement.connect(self.handleEntryMovement)
        event_entry.add_edit.connect(self.add_event_edit)
        event_entry.add_view.connect(self.add_event_view)
        event_entry.del_entry.connect(self.deleteEvent)
        self.scene.addEntryToScene(event_entry)
        event_entry.setTimeInterval(start, end)
        TimelineView.EventList.add(event_entry)
    
    
    @qtc.pyqtSlot()
    def deleteActiveEvent(self):
        event = None
        for item in self.scene.selectedItems():
            if isinstance(item, TimelineEventEntry):
                event = item
                break
        if not event and self.event_views:
            event = self.event_views[-1]
        if not event:
            return
        self.deleteEvent(event.getID())
    

    @qtc.pyqtSlot(uuid.UUID)
    def deleteEvent(self, event_id):
        if event := TimelineView.EventList.search(event_id):
            if child := self.findChild(EntryView, 'view{}'.format(event_id)):
                child.close()
            self.scene.removeEntryFromScene(event[0])
            TimelineView.EventList.remove(event[0])
            del event
            self.scene.update()


    @qtc.pyqtSlot(uuid.UUID)
    def add_character_view(self, char_id):
        char_view = self.findChild(CharacterView, 'view{}'.format(char_id))
        if not char_view:
            char = self.character_db.get(where('char_id') == char_id)
            fam_record = self.families_db.get(where('fam_id') == char['fam_id'])
            if not fam_record and char['partnerships']:
                fam_record = self.families_db.get(where('fam_id') == char['partnerships'][0]['rom_id'])
            char['family'] = fam_record['fam_name']
            kingdom_record = self.kingdoms_db.get(where('kingdom_id') == char['kingdom_id'])
            if not kingdom_record:
                char['kingdom'] = ''
            else:
                char['kingdom'] = kingdom_record['kingdom_name']

            popup_view = CharacterView(char)
            popup_view.setParent(self)
            self.scene.addItem(popup_view)
            popup_view.setPos(self.mapToScene(EntryView.CURRENT_SPAWN)) # NOTE: Magic numbers!
            popup_view.setZValue(2)
            EntryView.CURRENT_SPAWN += qtc.QPoint(10, 10)
            popup_view.closed.connect(lambda : self.char_views.remove(popup_view))
            popup_view.closed.connect(self.scene.clearSelection)
            self.char_views.append(popup_view)
            self.scene.selectionChanged.connect(popup_view.check_selected)

    

    @qtc.pyqtSlot(uuid.UUID)
    def add_event_view(self, event_id):
        event_view = self.findChild(EntryView, 'view{}'.format(event_id))
        if not event_view:
            event = self.events_db.get(where('event_id') == event_id)
            location = self.locations_db.get(where('location_id') == event['location_id'])
            if location:
                location = location['location_name']
            else:
                location = 'Unknown'
            event['location'] = location
            popup_view = EntryView(event)
            popup_view.setParent(self)
            self.scene.addItem(popup_view)
            popup_view.setPos(self.mapToScene(EntryView.CURRENT_SPAWN)) # NOTE: Magic numbers!
            popup_view.setZValue(2)
            EntryView.CURRENT_SPAWN += qtc.QPoint(10, 10)
            popup_view.closed.connect(lambda : self.event_views.remove(popup_view))
            popup_view.closed.connect(self.check_event_dlt_button)
            popup_view.closed.connect(self.scene.clearSelection)
            self.event_views.append(popup_view)
            self.scene.selectionChanged.connect(popup_view.check_selected)
            self.check_event_dlt_button()
    

    @qtc.pyqtSlot(uuid.UUID)
    def add_character_edit(self, char_id):
        selected_char = self.character_db.get(where('char_id') == char_id)
        if selected_char:
            fam_record = self.families_db.get(where('fam_id') == selected_char['fam_id'])
            if not fam_record:
                fam_record = self.families_db.get(where('fam_id') == selected_char['partnerships'][0]['rom_id'])
            selected_char['family'] = fam_record['fam_name']
            kingdom_record = self.kingdoms_db.get(where('kingdom_id') == selected_char['kingdom_id'])
            if kingdom_record:
                selected_char['kingdom'] = kingdom_record['kingdom_name']
            else:
                selected_char['kingdom'] = ''
            self.edit_window = CharacterCreator(self, selected_char)
            self.edit_window.submitted.connect(self.receiveCharacterUpdate)
            self.edit_window.show()


    @qtc.pyqtSlot(uuid.UUID)
    def add_event_edit(self, event_id):
        if selected_event := self.events_db.get(where('event_id') == event_id):
            if loc_record := self.locations_db.get(where('location_id') == selected_event['location_id']):
                loc_name = loc_record['location_name']
            else:
                loc_name = ''
            selected_event['location'] = loc_name
            self.new_event_dialog = EventCreator(self, selected_event)
            self.new_event_dialog.submitted.connect(self.receiveEventUpdate)
            self.new_event_dialog.show()
    
    

    def fitWithBorder(self):
        items = self.scene.current_entries
        boundingRect = qtc.QRectF()
        if len(items):
            for i in items:
                boundingRect = boundingRect.united(i.sceneBoundingRect())
            boundingRect.adjust(-self.BORDER_X, -self.BORDER_Y, 
                                    self.BORDER_X, self.BORDER_Y)
            if boundingRect.height() < self.DFLT_VIEW.height():
                rect = qtc.QRectF()
                rect.setSize(self.DFLT_VIEW.size())
                rect.moveCenter(boundingRect.center())
                boundingRect = rect
        else:
            boundingRect = self.DFLT_VIEW
        self.fitInView(boundingRect, qtc.Qt.KeepAspectRatio)
        self.zoomStatus = 0
        self.zoom_tracker = 0
        self.zoomChanged.emit(0)


    # def wheelEvent(self, event):                   # Control Zoom
    #     if event.angleDelta().y() > 0:
    #         direction = self.zoomStatus + 1
    #     else:
    #         direction = self.zoomStatus - 1
    #     self.zoomEvent(direction, event.pos())

    def zoomEvent(self, factor, center_pos=None):
        slider_zoom = False
        if not center_pos:
            slider_zoom = True
            center_pos = self.viewport().rect().center()
        zoomInFactor = 1.1
        zoomOutFactor = 1 / zoomInFactor
        self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
        self.setResizeAnchor(qtw.QGraphicsView.NoAnchor)

        if factor > self.zoomStatus:
            zoomFactor = zoomInFactor
            self.zoom_tracker += 1
        else:
            zoomFactor = zoomOutFactor
            self.zoom_tracker -= 1
        self.zoomStatus = factor
        

        if TimelineView.MIN_ZOOM > self.zoom_tracker:
            self.zoom_tracker = TimelineView.MIN_ZOOM
            return
        elif TimelineView.MAX_ZOOM < self.zoom_tracker:
            self.zoom_tracker = TimelineView.MAX_ZOOM
            return

        if not slider_zoom:
            self.zoomChanged.emit(self.zoomStatus)

        oldPos = self.mapToScene(center_pos)
        self.scale(zoomFactor, zoomFactor)
        # self.scale(factor, factor)
        newPos = self.mapToScene(center_pos)
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())
    

    def mousePressEvent(self, event):
        if event.button()  == qtc.Qt.LeftButton: 
            self._mousePressed = True
            self.last_mouse = 'Single'
        
        if self._pan: 
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.viewport().setCursor(qtc.Qt.ClosedHandCursor)
            event.accept()
        super(TimelineView, self).mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.last_mouse = 'Double'
    
    def mouseReleaseEvent(self, event):
        self._mousePressed = False
        
        if self._pan: 
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)
            event.accept()
        
        elif self.last_mouse == "Single":
            qtc.QTimer.singleShot(qtw.QApplication.instance().doubleClickInterval(), 
                            self.character_selected)
        
        # else:
        #     self.character_selected()

        super(TimelineView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._mousePressed:
            self.last_mouse = 'Move'
            if self._pan:
                self.viewport().setCursor(qtc.Qt.ClosedHandCursor)
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - (event.x() - self._panStartX))
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - (event.y() - self._panStartY))
                self._panStartX = event.x()
                self._panStartY = event.y()
                event.accept()
            elif event.pos().x() < 10:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - 15)
            elif event.pos().x() > self.viewport().width() - 10:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() + 15)

        super(TimelineView, self).mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:        # Escape key shortcuts
            if self.scene.selectedItems():
                item = self.scene.selectedItems()[0]
                if isinstance(item, TimelineCharEntry):
                    child = self.findChild(CharacterView, 'view{}'.format(item.getID()))
                    if child is not None:
                        child.close()
                    self.scene.clearSelection()
                elif isinstance(item, (CharacterView, EntryView)):
                    item.close()
            elif self.scene.focusItem():
                item = self.scene.focusItem()
                if isinstance(item, (CharacterView, EntryView)):
                    item.close()
            elif self.char_views:
                view = self.char_views[-1]
                view.close()
            elif self.event_views:
                view = self.event_views[-1]
                view.close()
        super(TimelineView, self).keyPressEvent(event)
    


    ## Gestures

    def viewportEvent(self, event):
        if event.type() == qtc.QEvent.Gesture:
            return self.gestureEvent(event)
        if event.type() == qtc.QEvent.GestureOverride:
            event.accept()
        return super(TimelineView, self).viewportEvent(event)

 
    def gestureEvent(self, event):
        # if swipe := event.gesture(qtc.Qt.PanGesture):
        #     self._pan = True
        #     self.panEvent(swipe)
        #     event.accept()

        if swipe := event.gesture(qtc.Qt.PinchGesture):
            if swipe.totalScaleFactor() != 1:
                # print('Pinching!')
                flags = swipe.changeFlags()
                if flags & qtw.QPinchGesture.ScaleFactorChanged:
                    self.current_factor = swipe.totalScaleFactor()

                if swipe.state() == qtc.Qt.GestureFinished:
                    self.zoom_factor *= self.current_factor
                    self.current_factor = 1
                    return True
                
                scale_factor = self.zoom_factor * self.current_factor
                self.zoomEvent(scale_factor, swipe.centerPoint().toPoint())

        return True

    
    def panEvent(self, event):
        if event.state() == qtc.Qt.GestureStarted:
            pass
        elif event.state() == qtc.Qt.GestureUpdated:
            self.setCursor(qtc.Qt.OpenHandCursor)
        else:
            self.setCursor(qtc.Qt.ArrowCursor)
        delta = event.delta()
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() - (delta.x()))
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() - (delta.y()))
        # self._panStartX = event.x()
        # self._panStartY = event.y()
    
    

# Create Timeline scene
class TimelineScene(qtw.QGraphicsScene):
    
    def __init__(self, parent=None):
        super(TimelineScene, self).__init__(parent)
        bg_pix = qtg.QPixmap(':/background-images/scene_bg_2.png')
        bg_pix = bg_pix.scaled(TimelineView.SCENE_WIDTH, TimelineView.SCENE_HEIGHT, 
                                        qtc.Qt.KeepAspectRatioByExpanding)
        
        self.setSceneRect(0, 0, TimelineView.SCENE_WIDTH, TimelineView.SCENE_HEIGHT)
        self.setItemIndexMethod(qtw.QGraphicsScene.NoIndex)
        self.current_entries = []
        self.linePen = qtg.QPen(qtg.QColor('black'))
        self.linePen.setWidth(10)
        bg_y = (bg_pix.height() - TimelineView.SCENE_HEIGHT) / 2
        self.bg = qtw.QGraphicsPixmapItem(bg_pix)
        self.bg.setPos(-20, -bg_y)
        self.addItem(self.bg)


    def add_axis(self, axis):
        self.addItem(axis)

    def addEntryToScene(self, entry):
        if entry not in self.current_entries:
            entry.setZValue(1)
            entry.setParent(self)
            self.addItem(entry)
            self.current_entries.append(entry)
    
    def removeEntryFromScene(self, entry):
        if entry in self.current_entries:
            self.removeItem(entry)
            self.current_entries.remove(entry)
