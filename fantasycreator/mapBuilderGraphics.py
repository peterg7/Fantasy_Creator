
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# 3rd party
import numpy as np
from tinydb import where

# Built-in Modules
import random
import types
import uuid

# User-defined Modules
from character import PictureLineEdit, PictureEditor, CharacterView, CharacterCreator
from database import DataFormatter
from mapBuilderObjects import GraphicCharacter, GraphicLocation, LocationView, LocationCreator
from mapBuilderObjects import CharacterSelect, TimestampCreator, LocationSelect
from animator import Animator
from storyTime import Time
from flags import ANIMATION_MODE, EVENT_TYPE

class MapView(qtw.QGraphicsView):

    BORDER_X = 20
    BORDER_Y = 20

    CANVAS_WIDTH = 10000
    CANVAS_HEIGHT = 10000
    CANVAS_BOUNDS = (0, 0, 10000, 10000)

    zoomChanged = qtc.pyqtSignal(int)    
    move_minimap = qtc.pyqtSignal(qtg.QPolygonF)

    animation_timestamp = qtc.pyqtSignal(uuid.UUID, Time, qtc.QPointF)
    visual_timestamp = qtc.pyqtSignal(str, Time)
    cut_character_scene = qtc.pyqtSignal(uuid.UUID, Time)
    updatedChars = qtc.pyqtSignal(list)

    MIN_ZOOM = -14
    MAX_ZOOM = 14

    def __init__(self, parent=None):
        print('Initializing map...')
        super(MapView, self).__init__(parent)

        self.scene = MapScene()
        self.setScene(self.scene)
        self.setSceneRect(0, 0, MapView.CANVAS_WIDTH, MapView.CANVAS_HEIGHT)
        self.setSizePolicy(
            qtw.QSizePolicy.Expanding, 
            qtw.QSizePolicy.Expanding
        )
        self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.centerOn(MapView.CANVAS_WIDTH/2, MapView.CANVAS_HEIGHT/2)
        self.setResizeAnchor(qtw.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)

        self.viewport().grabGesture(qtc.Qt.PinchGesture)
        self.viewport().setAttribute(qtc.Qt.WA_AcceptTouchEvents)

        self.data_formatter = DataFormatter()
        self.animator = Animator()

        # Connect signals
        self.scene.canvas.resized.connect(self.fitWithBorder)
        self.scene.canvas.location_placed.connect(self.createLocation)
        self.scene.canvas.timestamp_req.connect(self.createTimestamp)
        self.animation_timestamp.connect(self.animator.addTimestamp)
        self.cut_character_scene.connect(self.animator.deleteTimestamp)
        self.scene.canvas.edit_char.connect(self.addCharacterEdit)
        self.scene.canvas.add_char_view.connect(self.addCharacterView)
        self.scene.canvas.edit_location.connect(self.addLocationEdit)
        self.scene.canvas.add_loc_view.connect(self.addLocationView)
        
        ## MiniMap
        self.minimap = MiniMap(self.scene, self)
        self.scene.canvas.resized.connect(self.minimap.setMap)
        self.move_minimap.connect(self.minimap.controlView)
        # self.minimap.installEventFilter(self)

        layout = qtw.QVBoxLayout()
        app = qtw.QApplication.instance()
        scrollbar_width = app.style().pixelMetric(qtw.QStyle.PM_ScrollBarExtent)
        layout.setAlignment(qtc.Qt.AlignTop | qtc.Qt.AlignRight)
        # layout.setContentsMargins(0, 5, 5, 0)
        layout.addWidget(self.minimap)
        self.setLayout(layout)

        # self.setFixedSize(qtc.QSize(1800, 650))
        

        # Local variables
        self.zoom_factor = 1
        self.current_factor = 1
        self.zoomStatus = 0
        self.zoom_tracker = 0 

        self.loc_views = []
        self.char_views = []
        self._pan = False
        self.pan_act = False
        self._mousePressed = False
        self.last_mouse = None
        self.current_cast = set()
        self.current_map_path = None
    

    def connect_db(self, database):
        self.meta_db = database.table('meta')
        self.character_db = database.table('characters')
        self.families_db = database.table('families')
        self.kingdoms_db = database.table('kingdoms')
        self.locations_db = database.table('locations')
        self.timestamps_db = database.table('timestamps')
        # self.animator.buildTimeline(database)
        if probe := self.meta_db.get(where('map_path').exists()):
            meta_record = self.meta_db.get(doc_id=probe.doc_id)
            if img := meta_record['__IMG__']:
                self.reset(qtg.QPixmap.fromImage(img))
            else:
                self.reset(qtg.QPixmap(meta_record['map_path']))
            self.current_map_path = meta_record.get('map_path', None)
        else:
            self.blank_slate()

    # def eventFilter(self, source, event):
    #     if event.type() in (qtc.QEvent.GraphicsSceneMouseMove, qtc.QEvent.GraphicsSceneHoverEnter,
    #                         qtc.QEvent.GraphicsSceneHoverLeave, qtc.QEvent.GraphicsSceneHoverMove,
    #                         qtc.QEvent.GraphicsSceneMouseDoubleClick, qtc.QEvent.GraphicsSceneMousePress,
    #                         qtc.QEvent.GraphicsSceneMouseRelease, qtc.QEvent.HoverEnter, qtc.QEvent.HoverLeave, 
    #                         qtc.QEvent.HoverMove, qtc.QEvent.MouseTrackingChange, qtc.QEvent.MouseMove,
    #                         qtc.QEvent.GrabMouse, qtc.QEvent.Enter, qtc.QEvent.Leave):
    #         print('trapped event')
    #         return True
    #     print(event.type())
    #     return super(MapView, self).eventFilter(source, event)
    

    def saveMap(self):
        self.scene.clearSelection()
        self.fitWithBorder()

        embedded = set()
        for item in self.scene.canvas.current_items:
            if isinstance(item, (GraphicCharacter, GraphicLocation)):
                item.setVisible(False)
                embedded.add(item)
        map_img = qtg.QImage(self.mapToScene(self.viewport().rect()).boundingRect().toRect().size(), qtg.QImage.Format_ARGB32)
        map_img.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(map_img)
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        self.render(painter)
        painter.end()

        for item in embedded:
            item.setVisible(True)
    
        self.meta_db.update({'__IMG__': map_img})
        self.saveEmbedded()
    
    def saveEmbedded(self):
        for item in self.scene.canvas.current_items:
            if isinstance(item, GraphicCharacter):
                self.character_db.update({'graphical_rect': item.getGraphicalRect()},
                                            where('char_id') == item.getID())
            elif isinstance(item, GraphicLocation):
                self.locations_db.update({'graphical_rect': item.getGraphicalRect()},
                                            where('location_id') == item.getID())

    
    def set_new_image(self, img_path):
        if img_path != self.current_map_path:
            img = qtg.QImage(img_path)
            self.meta_db.update({'map_path': img_path, '__IMG__': img})
            self.reset(qtg.QPixmap.fromImage(img))
            self.current_map_path = img_path
    
    def blank_slate(self):
        self.current_map_path = None
        self.reset()
    
    def sweep_canvas(self):
        sweep_prompt = qtw.QMessageBox(qtw.QMessageBox.Warning, "Sweep Map?", 
                            (f"Are you sure you would like to clear the map?"),
                            qtw.QMessageBox.Abort | qtw.QMessageBox.Yes, self)
        sweep_prompt.setInformativeText('This action can not be undone.')
        prompt_font = qtg.QFont('Didot', 20)
        sweep_prompt.setFont(prompt_font)
        response = sweep_prompt.exec()
        if response != qtw.QMessageBox.Yes:
            return
        for item in self.scene.canvas.current_items:
            self.scene.removeItem(item)
            del item
        self.scene.canvas.current_items = []

    def init_loc_dialogs(self):
        loc_types = set()

        for loc in self.locations_db:
            loc_types.add(loc['location_type'])
            
        if '' in loc_types:
            loc_types.remove('')

        LocationCreator.TYPE_ITEMS.extend(x for x in loc_types)
        LocationCreator.TYPE_ITEMS.append('New...')
    
    def initTimestamps(self):
        for stamp in self.timestamps_db:
            if char_record := self.character_db.get(where('char_id') == stamp['char_id']):
                self.visual_timestamp.emit(char_record['name'], stamp['timestamp'])
                self.animation_timestamp.emit(char_record['char_id'], stamp['timestamp'], stamp['graphical_point'])
                

    def reset(self, img=None):      
        self.scene.canvas.reset(img)
    
    def set_primary_color(self, hex):
        self.scene.canvas.set_primary_color(hex)

    def set_secondary_color(self, hex):
        self.scene.canvas.set_secondary_color(hex)
    
    def set_current_stamp(self, stamp_path=None, stamp=None): # ASSUME TO BE STR PAT
        if stamp:
            self.scene.canvas.set_current_stamp(stamp)
        elif stamp_path:
            self.scene.canvas.set_current_stamp(qtg.QImage(stamp_path))
    
    def set_current_id(self, _id):
        self.scene.canvas.set_current_id(_id)

    def set_mode(self, mode, secondary=None):
        self.scene.canvas.set_mode(mode, secondary)
    
    def decrementViewSpawn(self):
        LocationView.CURRENT_SPAWN -= qtc.QPoint(10, 10)

    def toggle_panning(self, state):
        self._pan = state
        self.pan_act = state
        self._mousePressed = False
        if self.pan_act:
            self.viewport().setCursor(qtc.Qt.OpenHandCursor)
        else:
            self.viewport().unsetCursor()
        
    @qtc.pyqtSlot(list)
    def updateChars(self, char_list):
        for char_id in char_list:
            for item in self.scene.canvas.current_items:
                if char_id == item:
                    char_record = self.character_db.get(where('char_id') == char_id)
                    item.setStamp(char_record['__IMG__'])


    @qtc.pyqtSlot(int)
    @qtc.pyqtSlot(int, int)
    def animationDirector(self, slider_val, slider_mode=ANIMATION_MODE.YEAR):
        if slider_mode == ANIMATION_MODE.YEAR:
            if new_cast := self.animator.getYearStamps(year=slider_val):
                self.current_year = slider_val
                for char in new_cast:
                    if char[0] in self.current_cast:
                        self.scene.canvas.remove_character(char[0])
                    pix = self.character_db.get(where('char_id') == char[0])['__IMG__']
                    self.scene.canvas.place_character(char[0], pix, char[1])
                    self.current_cast.add(char[0])

        elif slider_mode == ANIMATION_MODE.MONTH:
            if new_cast := self.animator.getMonthStamps(month=slider_val, year=self.current_year):
                self.current_month = slider_val
                for char in new_cast:
                    pix = self.character_db.get(where('char_id') == char[0])['__IMG__']
                    self.scene.canvas.place_character(char[0], pix, char[1])
        
        elif slider_mode == ANIMATION_MODE.DAY:
            if new_cast := self.animator.getDayStamps(day=slider_val, 
                                    month=self.current_month, year=self.current_day):
                self.current_day = slider_val
                for char in new_cast:
                    pix = self.character_db.get(where('char_id') == char[0])['__IMG__']
                    self.scene.canvas.place_character(char[0], pix, char[1])


    @qtc.pyqtSlot(int)
    def scene_coordinator(self, show_locs):
        if show_locs:
            for loc in self.locations_db:
                self.scene.canvas.place_location(loc['location_id'], loc['__IMG__'], loc['graphical_rect'])
        else:
            for loc in self.locations_db:
                self.scene.canvas.remove_location(loc['location_id'])



    @qtc.pyqtSlot(str, Time)
    def removeTimestamp(self, name, time):
        if char_record := self.character_db.get(where('name') == name):
            self.cut_character_scene.emit(char_record['char_id'], time)
    
    @qtc.pyqtSlot(dict)
    def receiveLocationUpdate(self, loc_dict):
        loc_id = loc_dict.get('location_id', None)
        if not loc_id:
            return
        if not self.locations_db.contains(where('location_id') == loc_id):
            formatted_dict = self.data_formatter.globalLocationEntry(loc_dict=loc_dict, loc_id=loc_id)
            self.locations_db.insert(formatted_dict)
        else:
            updated_dict = {**self.locations_db.get(where('location_id') == loc_id), **loc_dict}
            formatted_dict = self.data_formatter.globalLocationEntry(loc_dict=updated_dict, loc_id=loc_id)
            update = self.locations_db.update(formatted_dict, where('location_id') == loc_id)
        if img := formatted_dict.get('__IMG__', None):
            self.scene.canvas.updateLocImage(loc_id, img)
        

    @qtc.pyqtSlot(dict)
    def receiveCharacterUpdate(self, char_dict):
        family_name = char_dict.pop('family', None)
        kingdom_name = char_dict.pop('kingdom', None)
        # # Merge dicts
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

        formatted_dict = self.data_formatter.char_entry(updated_dict)
        update = self.character_db.update(formatted_dict, where('char_id') == formatted_dict['char_id'])
        if update:
            self.updateChars([formatted_dict['char_id']])
            self.updatedChars.emit([formatted_dict['char_id']])


    @qtc.pyqtSlot()
    def itemSelected(self):
        if self.last_mouse == 'Single':
            if len(self.scene.selectedItems()) > 0: # at least one character selected
                selected_item = self.scene.selectedItems()[0] # NOTE: only using "first" item
                if isinstance(selected_item, GraphicLocation):
                    self.addLocationView(selected_item.getID())
                elif isinstance(selected_item, GraphicCharacter):
                    self.addCharacterView(selected_item.getID())

        if self.last_mouse == 'Double':
            if len(self.scene.selectedItems()) > 0: # at least one character selected
                selected_item = self.scene.selectedItems()[0] # NOTE: only using "first" item
                if isinstance(selected_item, GraphicLocation):
                    self.addLocationEdit(selected_item.getID())
                elif isinstance(selected_item, GraphicCharacter):
                    self.addCharacterEdit(selected_item.getID())
    

    @qtc.pyqtSlot()
    def launchCharacterSelect(self):
        current_chars = []
        for char in self.character_db:
            current_chars.append(char['name'])
        self.select_window = CharacterSelect(current_chars, self)
        self.select_window.submitted.connect(self.interpretCharSelection)
        self.select_window.cancel_btn.pressed.connect(self.scene.canvas.reset_mode)
        self.select_window.show()
    
    @qtc.pyqtSlot()
    def launchLocationSelect(self):
        current_locs = []
        for loc in self.locations_db:
            current_locs.append(loc['location_name'])
        self.select_window = LocationSelect(current_locs, self)
        self.select_window.submitted.connect(self.interpretLocSelection)
        self.select_window.cancel_btn.pressed.connect(self.scene.canvas.reset_mode)
        self.select_window.show()
    

    @qtc.pyqtSlot(str)
    def interpretCharSelection(self, char_name):
        selected_char = self.character_db.get(where('name') == char_name)
        if selected_char:
            self.set_current_id(selected_char['char_id'])
            self.set_current_stamp(selected_char['__IMG__'])
    
    @qtc.pyqtSlot(str)
    def interpretLocSelection(self, loc_name):
        selected_loc = self.locations_db.get(where('location_name') == loc_name)
        if selected_loc:
            self.set_current_id(selected_loc['location_id'])
            self.set_current_stamp(selected_loc['__IMG__'])
        

    @qtc.pyqtSlot(uuid.UUID, qtc.QPointF)
    def createTimestamp(self, char_id, loc):
        self.timestamp_window = TimestampCreator(self)
        self.timestamp_window.submitted.connect(lambda t: self.processTimestamp(char_id, loc, t))
        self.timestamp_window.show()

    @qtc.pyqtSlot(uuid.UUID, qtc.QPointF, Time)
    def processTimestamp(self, char_id, loc, time):
        char_record = self.character_db.get(where('char_id') == char_id)
        if char_record:
            formatted_dict = self.data_formatter.timestampEntry(loc, time, char_id)
            if existing_stamp := self.timestamps_db.get((where('time') == time) & (where('char_id') == char_id)):
                self.timestamps_db.update(formatted_dict, doc_ids=[existing_stamp.doc_id])
            else:
                self.timestamps_db.insert(formatted_dict)
            self.visual_timestamp.emit(char_record['name'], time)
            self.animation_timestamp.emit(char_id, time, loc)


    @qtc.pyqtSlot(uuid.UUID)
    def addLocationView(self, loc_id):
        if loc_id:
            location_view = self.findChild(LocationView, 'view{}'.format(loc_id))
            if location_view is None:
                location = self.locations_db.get(where('location_id') == loc_id)
                if location:
                    popup_view = LocationView(location)
                    popup_view.setParent(self)
                    self.scene.addItem(popup_view)
                    popup_view.setPos(self.mapToScene(LocationView.CURRENT_SPAWN)) # NOTE: Magic numbers!
                    popup_view.setZValue(1)
                    LocationView.CURRENT_SPAWN += qtc.QPoint(10, 10)
                    popup_view.closed.connect(lambda : self.loc_views.remove(popup_view))
                    popup_view.closed.connect(self.decrementViewSpawn)
                    popup_view.closed.connect(self.scene.clearSelection)
                    self.loc_views.append(popup_view)
                    self.scene.selectionChanged.connect(popup_view.check_selected)

    @qtc.pyqtSlot(uuid.UUID)
    def addLocationEdit(self, loc_id):
        selected_loc = self.locations_db.get(where('location_id') == loc_id)
        if selected_loc:
            self.edit_window = LocationCreator(self, selected_loc)
            self.edit_window.submitted.connect(self.receiveLocationUpdate)
            # self.edit_window.submitted.connect(lambda d: self.updatedChars.emit([d['char_id']]))
            self.edit_window.show()
    
    @qtc.pyqtSlot(str, qtg.QPolygonF)
    @qtc.pyqtSlot(str, qtg.QPolygonF, qtg.QImage)
    def createLocation(self, _type, graph_rect, stamp=None):
        rect = graph_rect.boundingRect()
        new_loc = {'location_type': _type, 'graphical_rect': rect}
        formatted_loc = self.data_formatter.globalLocationEntry(loc_dict=new_loc)
        loc_id = formatted_loc['location_id']

        if stamp:
            formatted_loc['__IMG__'] = stamp

        self.scene.canvas.current_graphic.setID(loc_id)
        self.new_loc_dialog = LocationCreator(self, formatted_loc, 'Create a new location')
        self.new_loc_dialog.submitted.connect(self.receiveLocationUpdate)
        self.new_loc_dialog.submitted.connect(self.scene.canvas.reset_mode)
        self.new_loc_dialog.cancel_btn.pressed.connect(lambda: self.scene.canvas.remove_location(loc_id))
        self.new_loc_dialog.cancel_btn.pressed.connect(self.scene.canvas.reset_mode)
        self.new_loc_dialog.show()


    @qtc.pyqtSlot(uuid.UUID)
    def addCharacterView(self, char_id):
        if char_id:
            char_view = self.findChild(CharacterView, 'view{}'.format(char_id))
            if char_view is None:
                char = self.character_db.get(where('char_id') == char_id)
                fam_record = self.families_db.get(where('fam_id') == char['fam_id'])

                if not fam_record:
                    if char['partnerships']:
                        fam_record = self.families_db.get(where('fam_id') == char['partnerships'][0]['rom_id'])
                    else:
                        fam_record = {'fam_name': ''} # NOTE: Temporary 
                char['family'] = fam_record['fam_name']
                kingdom_record = self.kingdoms_db.get(where('kingdom_id') == char['kingdom_id'])
                if not kingdom_record:
                    char['kingdom'] = ''
                else:
                    char['kingdom'] = kingdom_record['kingdom_name']

                popup_view = CharacterView(char)
                popup_view.setParent(self)
                self.scene.addItem(popup_view)
                popup_view.setPos(self.mapToScene(LocationView.CURRENT_SPAWN)) # NOTE: Magic numbers!
                popup_view.setZValue(1)
                LocationView.CURRENT_SPAWN += qtc.QPoint(10, 10)
                popup_view.closed.connect(lambda : self.char_views.remove(popup_view))
                popup_view.closed.connect(self.decrementViewSpawn)
                popup_view.closed.connect(self.scene.clearSelection)
                self.char_views.append(popup_view)
                self.scene.selectionChanged.connect(popup_view.check_selected)

    @qtc.pyqtSlot(uuid.UUID)
    def addCharacterEdit(self, char_id):
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
            # self.edit_window.submitted.connect(lambda d: self.updatedChars.emit([d['char_id']]))
            self.edit_window.show()


    def fitWithBorder(self):
        boundingRect = self.scene.canvas.center_view.adjusted(-self.BORDER_X, -self.BORDER_Y, 
                                self.BORDER_X, self.BORDER_Y)
        for i in self.scene.canvas.current_items:
                boundingRect = boundingRect.united(i.sceneBoundingRect())
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
        

        if MapView.MIN_ZOOM > self.zoom_tracker:
            self.zoom_tracker = MapView.MIN_ZOOM
            return
        elif MapView.MAX_ZOOM < self.zoom_tracker:
            self.zoom_tracker = MapView.MAX_ZOOM
            return

        if slider_zoom:
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
        
        if self.pan_act: 
            # self._pan = True
            # self._mousePressed = True
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.viewport().setCursor(qtc.Qt.ClosedHandCursor)
            event.accept()
        # else:
        #     event.ignore()
        super(MapView, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._mousePressed = False
        if self.pan_act: 
            pass

        # if self.last_mouse == "Single":
        #     qtc.QTimer.singleShot(qtw.QApplication.instance().doubleClickInterval(), 
        #                     self.itemSelected)
        super(MapView, self).mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        self.last_mouse = 'Double'
        # event.ignore()
        super(MapView, self).mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._mousePressed:
            self.last_mouse = 'Move'
            if self.pan_act:
                # self.viewport().setCursor(qtc.Qt.ClosedHandCursor)
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - (event.x() - self._panStartX))
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - (event.y() - self._panStartY))
                self._panStartX = event.x()
                self._panStartY = event.y()
                event.accept()
            # else:
            #     event.ignore()
        super(MapView, self).mouseMoveEvent(event)
    
    ## Gestures

    def viewportEvent(self, event):
        if event.type() == qtc.QEvent.Gesture:
            return self.gestureEvent(event)
        if event.type() == qtc.QEvent.GestureOverride:
            event.accept()
        return super(MapView, self).viewportEvent(event)
 
    def gestureEvent(self, event):
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

    
    def paintEvent(self, event):
        rect = self.mapToScene(self.rect())
        self.move_minimap.emit(rect)
        # print('MapView', rect.boundingRect())
        super(MapView, self).paintEvent(event)


class MiniMap(qtw.QGraphicsView):

    WIDTH = 100
    HEIGHT = 100

    def __init__(self, scene, parent=None):
        super(MiniMap, self).__init__(parent)

        self.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.setFixedSize(MiniMap.WIDTH, MiniMap.HEIGHT)
        self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.brush = qtg.QBrush(qtg.QColor(252, 221, 160, 128))


        # self.scene = MapScene()
        self.setScene(scene)
        self.centerOn(MapView.CANVAS_WIDTH/2, MapView.CANVAS_HEIGHT/2)
        # self.setResizeAnchor(qtw.QGraphicsView.AnchorViewCenter)
        # self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
        self.boundingRect = qtc.QRectF(0, 0, MapView.CANVAS_WIDTH, MapView.CANVAS_HEIGHT)
        self.setSceneRect(self.boundingRect)
        self.rect_view = qtc.QRectF(0, 0, 0, 0)
        
    @qtc.pyqtSlot()
    def setMap(self):
        self.viewport().update()
        self.fitInView(self.boundingRect, qtc.Qt.KeepAspectRatio)
    
    @qtc.pyqtSlot(qtg.QPolygonF)
    def controlView(self, poly):
        rect = self.mapFromScene(poly).boundingRect()
        self.rect_view = rect
        # print('MiniMap', rect)
    

    def paintEvent(self, event):
        # print('PAINTING')
        super(MiniMap, self).paintEvent(event)
        painter = qtg.QPainter(self.viewport())
        painter.setBrush(self.brush)
        painter.drawRect(self.rect_view)
        painter.end()

    

class MapScene(qtw.QGraphicsScene):

    CANVAS_BORDER = 200

    def __init__(self, parent=None):
        super(MapScene, self).__init__(parent)

        self.canvas = Canvas()
        # self.canvas.setFocusPolicy(qtc.Qt.StrongFocus)
        # self.canvas.setPos(self.CANVAS_WIDTH/2, self.CANVAS_HEIGHT/2)
        self.canvas.setPos(self.CANVAS_BORDER/2, self.CANVAS_BORDER/2)
        # self.setSceneRect(0, 0, MapView.CANVAS_WIDTH, MapView.CANVAS_HEIGHT)
        self.background_color = qtg.QColor('#fcdda0')
        self.setBackgroundBrush(self.background_color)

        self.addItem(self.canvas)

    # Reimplement built-in slots
    # def mousePressEvent(self, event):
    #     print('Scene was pressed')
    #     super(MapScene, self).mousePressEvent(event)
    def remove_current_graphic(self):
        self.removeItem(self.canvas.current_graphic)
        self.canvas.current_items.remove(self.canvas.current_graphic)
        self.canvas.current_graphic.deleteLater()
        self.canvas.current_graphic = None
        # self.canvas.reset_mode()
    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Backspace:
            if self.selectedItems():
                # if items[0] is self.canvas.current_graphic:
                #     self.remove_current_graphic()
                # else:
                # print(items[0])
                item = self.selectedItems()[0]
                self.canvas.current_items.remove(item)
                self.removeItem(item)
                # # items[0].deleteLater()
                del item
            event.accept()

        elif event.key() == qtc.Qt.Key_Escape:
            self.clearSelection()
            event.accept()
        
        super(MapScene, self).keyPressEvent(event)
    

class Canvas(qtw.QGraphicsWidget):

    DFLT_VIEW = qtc.QRectF(4000, 4000, 2000, 2000)

    SELECTION_PEN = qtg.QPen(qtg.QColor(0xff, 0xff, 0xff), 1, qtc.Qt.DashLine)
    PREVIEW_PEN = qtg.QPen(qtg.QColor(qtc.Qt.black), 1, qtc.Qt.DashLine)
    BRUSH_MULT = 3
    SPRAY_PAINT_MULT = 5
    SPRAY_PAINT_N = 100

    mode = 'select'
    secondary_mode = None

    primary_color = qtg.QColor(qtc.Qt.black)
    secondary_color = None

    primary_color_updated = qtc.pyqtSignal(str)
    secondary_color_updated = qtc.pyqtSignal(str)
    resized = qtc.pyqtSignal()
    clear_mode = qtc.pyqtSignal(str, str)
    location_placed = qtc.pyqtSignal(str, qtg.QPolygonF, qtg.QImage)
    character_placed = qtc.pyqtSignal(uuid.UUID, qtg.QPolygonF)

    edit_char = qtc.pyqtSignal(uuid.UUID)
    edit_location = qtc.pyqtSignal(uuid.UUID)
    add_char_view = qtc.pyqtSignal(uuid.UUID)
    add_loc_view = qtc.pyqtSignal(uuid.UUID)
    timestamp_req = qtc.pyqtSignal(uuid.UUID, qtc.QPointF)

    # Store configuration settings
    config = {
        # Drawing options.
        'size': 1,
        'fill': True,
        # Font options.
        'font': qtg.QFont('Baskerville'),
        'fontsize': 36,
        'bold': False,
        'italic': False,
        'underline': False,
    }

    active_color = None
    preview_pen = None
    timer_event = None
    current_graphic = None
    current_stamp = None
    current_id = None

    

    def __init__(self, img=None, parent=None):
        super(Canvas, self).__init__(parent)
        self.setFlags(qtw.QGraphicsItem.ItemIsFocusable |
                    qtw.QGraphicsItem.ItemSendsGeometryChanges)
        self.setFocusPolicy(qtc.Qt.ClickFocus)
        self.current_items = []

        self.center_view = qtc.QRectF(MapView.CANVAS_WIDTH/3, MapView.CANVAS_HEIGHT/3, 
                                        MapView.CANVAS_WIDTH/3, MapView.CANVAS_HEIGHT/3)
        self.background_color = qtg.QColor(qtc.Qt.white)
        self.eraser_color = qtg.QColor(qtc.Qt.white)
        self.eraser_color.setAlpha(127)
        self.reset(img)
    

    def reset(self, img=None):
        blank_pixmap = qtg.QPixmap(MapView.CANVAS_WIDTH - MapScene.CANVAS_BORDER, 
                                        MapView.CANVAS_HEIGHT - MapScene.CANVAS_BORDER)
        blank_pixmap.fill(self.background_color)
        if img:
            self.custom_background = img
            p = qtg.QPainter(blank_pixmap)
            p.setCompositionMode(qtg.QPainter.CompositionMode_SourceOver)
            # p.drawPixmap(blank_pixmap.width()/2 - img.width()/2, 
            #             blank_pixmap.height()/2 - img.height()/2, img)
            p.drawPixmap(blank_pixmap.width()/2 - img.width()/2, 
                        blank_pixmap.height()/2 - img.height()/2, img)
            p.end()
            self.center_view = qtc.QRectF(blank_pixmap.width()/2 - img.width()/2 + MapScene.CANVAS_BORDER/2, 
                        blank_pixmap.height()/2 - img.height()/2 + MapScene.CANVAS_BORDER/2, img.width(), img.height())
        else:
            self.center_view = Canvas.DFLT_VIEW
        self.pixmap_bg = blank_pixmap
        self.bounding_rect = qtc.QRectF(self.pixmap_bg.rect())        
        # print(f'Resized: {}')
        self.resized.emit()
    
    def set_primary_color(self, hex):
        self.primary_color = qtg.QColor(hex)

    def set_secondary_color(self, hex):
        self.secondary_color = qtg.QColor(hex)

    def set_current_stamp(self, stamp_path):
        self.current_stamp = stamp_path
    
    def set_current_id(self, _id):
        self.current_id = _id
        
    def set_config(self, key, value):
        self.config[key] = value
    
    def set_mode(self, mode, secondary=None):
        self.timer_cleanup()
        if mode == 'select': 
            for item in self.current_items:
                item.toggleEditing(False)
        else:
            for item in self.current_items:
                item.toggleEditing(True)
        self.current_graphic = None
        self.current_stamp = None
        self.current_id = None
        self.active_shape_fn = None
        self.active_shape_args = ()

        self.origin_pos = None
        self.current_pos = None
        self.last_pos = None
        self.history_pos = None
        self.last_history = []

        self.current_text = ''
        self.last_text = ''
        self.last_config = {}

        self.dash_offset = 0
        self.locked = False
        self.mode = mode
        self.secondary_mode = secondary
    
    def reset_mode(self):
        self.scene().clearSelection()
        # for item in self.current_items:
        #         item.toggleEditing(False)
        # if self.current_graphic:
        #     self.current_graphic.toggleEditing(False)
        # self.current_graphic = None
        self.clear_mode.emit('select', 'reset')
        # self.set_mode(self.mode, None)
        self.update()
    
    def on_timer(self):
        if self.timer_event:
            self.timer_event()
    
    def timer_cleanup(self):
        if self.timer_event:
            timer_event = self.timer_event
            self.timer_event = None
            timer_event(final=True)    



    def mousePressEvent(self, event):
        fn = getattr(self, "%s_mousePressEvent" % self.mode, None)
        if fn:
            return fn(event)
        super(Canvas, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        fn = getattr(self, "%s_mouseMoveEvent" % self.mode, None)
        if fn:
            return fn(event)
        super(Canvas, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        fn = getattr(self, "%s_mouseReleaseEvent" % self.mode, None)
        if fn:
            return fn(event)
        super(Canvas, self).mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        fn = getattr(self, "%s_mouseDoubleClickEvent" % self.mode, None)
        if fn:
            return fn(event)
        super(Canvas, self).mouseDoubleClickEvent(event)
    
    def generic_mousePressEvent(self, e):
        self.last_pos = e.pos().toPoint()
        if e.button() == qtc.Qt.LeftButton:
            self.active_color = self.primary_color
        # else:
        #     self.active_color = self.secondary_color

    def generic_mouseReleaseEvent(self, e):
        self.last_pos = None
        self.current_graphic = None
        # if self.current_graphic:
        #     self.current_graphic.toggleEditing(False)


    ## Mode-specific events.

    # Eraser events
    def eraser_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)
        self.current_graphic = GraphicBrushStroke(
                            e.pos(), 
                            qtg.QPen(self.eraser_color, 30, qtc.Qt.SolidLine, qtc.Qt.RoundCap, qtc.Qt.RoundJoin),
                            selectable=False,
                            parent=self)
        self.current_items.append(self.current_graphic)
        
    def eraser_mouseMoveEvent(self, e):
        if self.last_pos:
            self.current_graphic.brush_moved(e.pos())
            self.last_pos = e.pos().toPoint()
            self.update()

    def eraser_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)


    # Pen events
    def pen_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)
        self.current_graphic = GraphicBrushStroke(
                            e.pos(), 
                            qtg.QPen(self.active_color, self.config['size'], qtc.Qt.SolidLine, qtc.Qt.SquareCap, qtc.Qt.RoundJoin),
                            parent=self)
        self.current_items.append(self.current_graphic)

    def pen_mouseMoveEvent(self, e):
        if self.last_pos:
            self.current_graphic.brush_moved(e.pos())
            self.last_pos = e.pos().toPoint()
            self.update()

    def pen_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)


    # Brush events
    def brush_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)
        self.current_graphic = GraphicBrushStroke(
                            e.pos(), 
                            qtg.QPen(self.active_color, self.config['size'] * self.BRUSH_MULT, qtc.Qt.SolidLine, qtc.Qt.RoundCap, qtc.Qt.RoundJoin),
                            parent=self)
        self.current_items.append(self.current_graphic)
        
    def brush_mouseMoveEvent(self, e):
        if self.last_pos:
            self.current_graphic.brush_moved(e.pos())
            self.last_pos = e.pos().toPoint()
            self.update()

    def brush_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)


    # Spray events
    def spray_mousePressEvent(self, e):
        self.generic_mousePressEvent(e)
        self.current_graphic = GraphicPaintSpray(e.pos(),
                                                qtg.QPen(self.active_color, 1),
                                                self.config['size'],
                                                parent=self)
        self.current_items.append(self.current_graphic)

    def spray_mouseMoveEvent(self, e):
        if self.last_pos:
            self.current_graphic.sprayPoints(e)
            self.last_pos = e.pos().toPoint()
            self.update()

    def spray_mouseReleaseEvent(self, e):
        self.generic_mouseReleaseEvent(e)


    # Text events
    def keyPressEvent(self, e):
        if self.mode == 'text':
            if e.key() == qtc.Qt.Key_Backspace:
                self.current_text = self.current_text[:-1]
            elif e.key() == qtc.Qt.Key_Return:
                self.timer_cleanup()
                self.reset_mode()
            elif e.key() == qtc.Qt.Key_Escape:
                self.timer_cleanup()
                self.current_items.remove(self.current_graphic)
                self.scene().removeItem(self.current_graphic)
                self.current_graphic.deleteLater()
                self.reset_mode()
            else:
                self.current_text = self.current_text + e.text()
        super(Canvas, self).keyPressEvent(e)

    def text_mousePressEvent(self, e):
        if e.button() == qtc.Qt.LeftButton and self.current_pos is None:
            self.current_pos = e.pos().toPoint()
            self.current_text = ""
            self.current_graphic = GraphicTextBox(self.current_pos, parent=self)
            self.current_items.append(self.current_graphic)
            self.timer_event = self.text_timerEvent

    def text_timerEvent(self, final=False):
        if self.last_text:
            font = build_font(self.last_config)
            self.current_graphic.setFont(font)
            self.current_graphic.setPlainText(self.last_text)

        if not final:
            font = build_font(self.config)
            self.current_graphic.setFont(font)
            self.current_graphic.setPlainText(self.current_text)

        self.last_text = self.current_text
        self.last_config = self.config.copy()
        self.update()


    # Dropper events
    def dropper_mousePressEvent(self, e):
        c = self.pixmap_bg.toImage().pixel(e.pos().toPoint())
        hex = qtg.QColor(c).name()

        if e.button() == qtc.Qt.LeftButton:
            self.set_primary_color(hex)
            self.primary_color_updated.emit(hex)  # Update UI.

        # elif e.button() == qtc.Qt.RightButton:
        #     self.set_secondary_color(hex)
        #     self.secondary_color_updated.emit(hex)  # Update UI.


    # Line events
    def line_mousePressEvent(self, e):
        self.origin_pos = e.pos().toPoint()
        self.current_pos = e.pos().toPoint()
        self.timer_event = self.line_timerEvent
        self.current_graphic = GraphicLine(e.pos(),
                            qtg.QPen(self.primary_color, self.config['size'], qtc.Qt.SolidLine, qtc.Qt.RoundCap, qtc.Qt.RoundJoin),
                            parent=self)
        self.current_items.append(self.current_graphic)

    def line_timerEvent(self, final=False):
        if self.last_pos:
            self.current_graphic.previewLine(self.last_pos)

        if not final:
            self.current_graphic.previewLine(self.current_pos)

        self.last_pos = self.current_pos

    def line_mouseMoveEvent(self, e):
        self.current_pos = e.pos().toPoint()

    def line_mouseReleaseEvent(self, e):
        if self.last_pos:
            self.timer_cleanup()
            self.current_graphic.previewLine(e.pos())


    # Generic shape events: Rectangle, Ellipse, Rounded-rect
    def generic_shape_mousePressEvent(self, e):
        self.origin_pos = e.pos()
        self.current_pos = e.pos()
        self.timer_event = self.generic_shape_timerEvent
        self.current_graphic = GraphicShape(
                        start_pos=self.origin_pos,
                        mode=self.mode,
                        args=self.active_shape_args,
                        pen=qtg.QPen(self.primary_color, self.config['size'], qtc.Qt.SolidLine, qtc.Qt.SquareCap, qtc.Qt.MiterJoin),
                        parent=self)
        self.current_items.append(self.current_graphic)

    def generic_shape_timerEvent(self, final=False):
        if self.last_pos:
            self.current_graphic.previewShape(self.last_pos)
        if not final:
            self.dash_offset -= 1
            self.current_graphic.adjustPenOffset(self.dash_offset)
            self.current_graphic.previewShape(self.current_pos)

        self.last_pos = self.current_pos

    def generic_shape_mouseMoveEvent(self, e):
        self.current_pos = e.pos()

    def generic_shape_mouseReleaseEvent(self, e):
        if self.last_pos:
            # Clear up indicator.
            self.timer_cleanup()
            if self.config['fill']:
                self.current_graphic.addBrush(qtg.QBrush(self.secondary_color))
            self.current_graphic.commitShape(e.pos())


    # Generic poly events
    def generic_poly_mousePressEvent(self, e):
        if e.button() == qtc.Qt.LeftButton:
            if self.last_pos:
                self.last_pos = e.pos()
                self.current_graphic.commitPoint(self.last_pos)
            else:
                self.current_pos = e.pos()
                self.timer_event = self.generic_poly_timerEvent
                self.current_graphic = GraphicPoly(
                        start_pos=self.current_pos,
                        mode=self.mode,
                        pen=qtg.QPen(self.primary_color, self.config['size'], qtc.Qt.SolidLine, qtc.Qt.RoundCap, qtc.Qt.RoundJoin),
                        parent=self)
                self.current_items.append(self.current_graphic)

        elif e.button() == qtc.Qt.RightButton and self.last_pos:
            self.timer_cleanup()
            self.reset_mode()

    def generic_poly_timerEvent(self, final=False):
        if self.last_pos:
            # getattr(self.current_graphic, self.active_shape_fn)(self.last_pos)
            self.current_graphic.previewPoly(self.last_pos)

        if not final:
            self.dash_offset -= 1
            self.current_graphic.adjustPenOffset(self.dash_offset)
            # getattr(self.current_graphic, self.active_shape_fn)(self.current_pos)
            self.current_graphic.previewPoly(self.current_pos)

        self.last_pos = self.current_pos

    def generic_poly_mouseMoveEvent(self, e):
        self.current_pos = e.pos()

    def generic_poly_mouseDoubleClickEvent(self, e):
        self.timer_cleanup()

        if self.secondary_color:
            self.current_graphic.addBrush(qtg.QBrush(self.secondary_color))

        # getattr(self.current_graphic, self.active_shape_fn)(e.pos())
        self.current_graphic.commitPoly(e.pos())

        # self.reset_mode()


    # Polyline events
    def polyline_mousePressEvent(self, e):
        self.active_shape_fn = 'previewPolyline'
        self.generic_poly_mousePressEvent(e)

    def polyline_timerEvent(self, final=False):
        self.generic_poly_timerEvent(final)

    def polyline_mouseMoveEvent(self, e):
        self.generic_poly_mouseMoveEvent(e)

    def polyline_mouseDoubleClickEvent(self, e):
        self.generic_poly_mouseDoubleClickEvent(e)


    # Rectangle events
    def rect_mousePressEvent(self, e):
        self.active_shape_args = ()
        self.generic_shape_mousePressEvent(e)

    def rect_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def rect_mouseMoveEvent(self, e):
        self.generic_shape_mouseMoveEvent(e)

    def rect_mouseReleaseEvent(self, e):
        self.generic_shape_mouseReleaseEvent(e)


    # Polygon events
    def polygon_mousePressEvent(self, e):
        self.active_shape_fn = 'previewPolygon'
        self.generic_poly_mousePressEvent(e)

    def polygon_timerEvent(self, final=False):
        self.generic_poly_timerEvent(final)

    def polygon_mouseMoveEvent(self, e):
        self.generic_poly_mouseMoveEvent(e)

    def polygon_mouseDoubleClickEvent(self, e):
        self.generic_poly_mouseDoubleClickEvent(e)


    # Ellipse events
    def ellipse_mousePressEvent(self, e):
        self.active_shape_args = ()
        self.generic_shape_mousePressEvent(e)

    def ellipse_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def ellipse_mouseMoveEvent(self, e):
        self.generic_shape_mouseMoveEvent(e)

    def ellipse_mouseReleaseEvent(self, e):
        self.generic_shape_mouseReleaseEvent(e)


    # Roundedrect events
    def roundrect_mousePressEvent(self, e):
        self.active_shape_args = (25, 25)
        self.generic_shape_mousePressEvent(e)

    def roundrect_timerEvent(self, final=False):
        self.generic_shape_timerEvent(final)

    def roundrect_mouseMoveEvent(self, e):
        self.generic_shape_mouseMoveEvent(e)

    def roundrect_mouseReleaseEvent(self, e):
        self.generic_shape_mouseReleaseEvent(e)


    # Embedded events
    def location_mousePressEvent(self, e):
        self.current_graphic = GraphicLocation(
                        e.pos(),
                        mode=self.mode,
                        stamp=self.current_stamp,
                        parent=self)
        self.current_items.append(self.current_graphic)
        self.current_graphic.setParent(self)
        if self.secondary_mode != 'existingLoc':
            self.location_placed.emit(self.mode, self.mapToScene(self.current_graphic.boundingRect()), self.current_stamp)
        else:
            self.current_graphic.setID(self.current_id)
            self.reset_mode()

    def character_mousePressEvent(self, e):
        self.current_graphic = GraphicCharacter(
                        e.pos(),
                        char_id=self.current_id,
                        stamp=self.current_stamp,
                        parent=self)
        self.current_items.append(self.current_graphic)
        self.current_graphic.setParent(self)
        self.character_placed.emit(self.current_id, self.mapToScene(self.current_graphic.boundingRect()))
        self.reset_mode()

    def place_character(self, char_id, char_pix, loc):
        new_graphic = GraphicCharacter(
                        loc,
                        char_id=char_id,
                        stamp=char_pix,
                        timestamp=True,
                        parent=self )
        self.current_items.append(new_graphic)
        new_graphic.toggleEditing(False)
        new_graphic.setParent(self)
    
    def place_location(self, loc_id, loc_pix, graph_loc):
        new_graphic = GraphicLocation(
                        graph_loc,
                        mode='custom',
                        stamp=loc_pix,
                        loc_id=loc_id,
                        parent=self )
        self.current_items.append(new_graphic)
        new_graphic.toggleEditing(False)
        new_graphic.setParent(self)
    
    def remove_character(self, char_id):
        child = self.findChild(GraphicCharacter, "graphicChar{}".format(char_id))
        if child:
            self.scene().removeItem(child)
            child.setParent(None)
            self.current_items.remove(child)
            del child
    
    def remove_location(self, loc_id):
        child = self.findChild(GraphicLocation, "graphicLoc{}".format(loc_id))
        if child:
            self.scene().removeItem(child)
            child.setParent(None)
            self.current_items.remove(child)
            del child

    def updateLocImage(self, loc_id, img):
        if child := self.findChild(GraphicLocation, "graphicLoc{}".format(loc_id)):
            child.setStamp(img)



    def paint(self, painter, options, widget):
        painter.drawPixmap(0, 0, self.pixmap_bg)
        painter.setPen(qtg.QPen(qtc.Qt.black, 3))
        painter.drawRect(self.bounding_rect)

    def boundingRect(self):
        return self.bounding_rect

    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.bounding_rect)
        return path


    def itemChange(self, change, value):
        if change == qtw.QGraphicsItem.ItemSceneHasChanged and self.scene():
            rect = self.scene().sceneRect()
            self.resize(rect.width(), rect.height())
        return super(Canvas, self).itemChange(change, value)


def build_font(config):
    font = config['font']
    font.setPointSize(config['fontsize'])
    font.setBold(config['bold'])
    font.setItalic(config['italic'])
    font.setUnderline(config['underline'])
    return font


# Custom paint/drawing objects

class GraphicTextBox(qtw.QGraphicsTextItem):

    # editing = qtc.pyqtSignal(GraphicTextBox)

    class rotationHandle(qtw.QGraphicsObject):
        
        position_changed = qtc.pyqtSignal(qtc.QPointF, qtc.QPointF)
        update_origin_point = qtc.pyqtSignal()

        def __init__(self, parent=None):
            super(GraphicTextBox.rotationHandle, self).__init__(parent)
            # self.setFlags(qtw.QGraphicsItem.ItemIsMovable |
            self.setFlags(
                        # qtw.QGraphicsItem.ItemIsMovable |
                        qtw.QGraphicsItem.ItemIsSelectable |
                        qtw.QGraphicsItem.ItemSendsScenePositionChanges)
            self.knob = qtw.QGraphicsEllipseItem(0, 0, 12, 12)
            self.knob.setBrush(qtg.QBrush(qtg.QColor('red'), qtc.Qt.SolidPattern))
            self.setting_pos = True

        def setAnchor(self, anchor):
            self.anchor = anchor
            self.radius = np.sqrt(np.square(self.anchor.x() - self.x()) 
                                + np.square(self.anchor.y() - self.y()))
            self.offset = qtc.QPointF(self.radius, self.radius)
            # print(self.radius)
        
        def setPosition(self, pos):
            self.setting_pos = True
            self.setPos(pos)
            self.setting_pos = False

        
        # def itemChange(self, change, value):
        #     if change == qtw.QGraphicsItem.ItemSelectedHasChanged:
        #         self.parent().setSelected(value)
        #     super(GraphicTextBox.rotationHandle, self).itemChange(change, value)


        def mousePressEvent(self, event):
            if event.button() == qtc.Qt.LeftButton:
                self._mouse_pressed = True
                self.initial_pos = event.pos()
                self.initial_center = self.boundingRect()
            super(GraphicTextBox.rotationHandle, self).mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if self._mouse_pressed:
                self.position_changed.emit(event.pos(), self.offset)
            super(GraphicTextBox.rotationHandle, self).mouseMoveEvent(event)
        
        def mouseReleaseEvent(self, event):
            self._mouse_pressed = False
            self.update_origin_point.emit()
            super(GraphicTextBox.rotationHandle, self).mouseReleaseEvent(event)

        def shape(self):
            return self.knob.shape()

        def boundingRect(self):
            return self.knob.boundingRect()

        def paint(self, painter, options, widget):
            self.knob.paint(painter, options, widget)
        

    def __init__(self, start_pos, parent=None):
        super(GraphicTextBox, self).__init__(parent)
        self.creating = True
        self.setPos(start_pos)
        self.handle = GraphicTextBox.rotationHandle(self)
        self.handle.setParent(self)
        self.handle.setParentItem(self)
        self.handle.setVisible(False)
        self.handle.position_changed.connect(self.rotateTextBox)
        self.handle.update_origin_point.connect(self.updateTransformOrigin)
    
    def toggleEditing(self, state):
        self.editing = state
        # print(f'Toggled: {state}')
        if self.editing:
            self.unsetCursor()
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
        else:
            if self.creating:
                self.creating = False
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
            self.setCursor(qtc.Qt.OpenHandCursor)
            center_pt = self.boundingRect().center()
            self.setTransformOriginPoint(center_pt)
            self.handle.setPosition(qtc.QPointF(center_pt.x(), center_pt.y() - self.boundingRect().height()))
            self.handle.setAnchor(center_pt)
    
    @qtc.pyqtSlot(qtc.QPointF, qtc.QPointF)
    def rotateTextBox(self, moved, offset):
        line = qtc.QLineF(self.boundingRect().center(), moved)
        rotations = line.angle()
        if line.dx() <= 0:
          rotations = (180) - rotations
        else:
          rotations = rotations - (180)

        m_Angle = rotations
        self.setRotation(self.rotation() + m_Angle)
        self.prepareGeometryChange()
        self.update()


    @qtc.pyqtSlot()
    def updateTransformOrigin(self):
        old_origin = self.scenePos()
        self.setTransformOriginPoint(self.boundingRect().center())
        new_origin = self.scenePos()
        old_pos = self.pos()
        self.setPos(old_pos.x() + (old_origin.x() - new_origin.x()), old_pos.y() + (old_origin.y() - new_origin.y()))

    # Override built-in slots

    # def itemChange(self, change, value):
    #     if change == qtw.QGraphicsItem.ItemSelectedHasChanged:
    #         self.handle.setSelected(value)
    #     super(GraphicTextBox, self).itemChange(change, value)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.boundingRect())
        path.addPath(self.handle.shape())
        return path
    
    def boundingRect(self):
        return super(GraphicTextBox, self).boundingRect().united(self.childrenBoundingRect())


    def paint(self, painter, options, widget):
        if self.creating:
            painter.drawRect(self.boundingRect())
        if self.isSelected() or self.handle.isSelected():
            self.handle.setVisible(True)
        else:
            self.handle.setVisible(False)
        super(GraphicTextBox, self).paint(painter, options, widget)


class GraphicBrushStroke(qtw.QGraphicsPathItem):

    def __init__(self, start_pos, brush, selectable=True, parent=None):
        super(GraphicBrushStroke, self).__init__(parent)
        self.selectable = selectable
        
        self.stroke = qtg.QPainterPath()
        self.stroke.moveTo(start_pos)
        self.setPath(self.stroke)
        self.setPen(brush)
    
    
    def brush_moved(self, pos):
        self.prepareGeometryChange()
        self.stroke.lineTo(pos)
        self.setPath(self.stroke)

    def toggleEditing(self, state):
        self.editing = state
        if state and self.selectable:
                self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False)
                self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
                self.unsetCursor()
        if not self.editing and self.selectable:
                self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True)
                self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
                self.setCursor(qtc.Qt.OpenHandCursor)


class GraphicPaintSpray(qtw.QGraphicsItem):
    
    def __init__(self, start_pos, brush, size, parent=None):
        super(GraphicPaintSpray, self).__init__(parent)

        self.pix = qtg.QPixmap(MapView.CANVAS_WIDTH - MapScene.CANVAS_BORDER, 
                                        MapView.CANVAS_HEIGHT - MapScene.CANVAS_BORDER)
        self.pix.fill(qtg.QColor(qtc.Qt.transparent))
        self.brush = brush
        self.size = size
        self.setPos(0, 0)
        self.max_x = 0
        self.max_y = 0
        self.min_x = self.pix.width()
        self.min_y = self.pix.height()
        self.radius = self.size * Canvas.SPRAY_PAINT_MULT
        self.creating = True

    
    def toggleEditing(self, state):
        self.editing = state
        if state:
            self.unsetCursor()
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
        else:
            if self.creating:
                self.consolidatePix()
                self.creating = False
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
            self.setCursor(qtc.Qt.OpenHandCursor)
    
    def sprayPoints(self, e):
        p = qtg.QPainter(self.pix)
        p.setPen(self.brush)

        x = e.pos().x()
        y = e.pos().y()
        for n in range(self.size * Canvas.SPRAY_PAINT_N):
            x_0 = random.gauss(0, self.radius)
            y_0 = random.gauss(0, self.radius)
            p.drawPoint(x + x_0, y + y_0)
        
        if x < self.min_x:
            self.min_x = x
        if x > self.max_x:
            self.max_x = x
        if y < self.min_y:
            self.min_y = y
        if y > self.max_y:
            self.max_y = y

        p.end()
        self.update()

    def consolidatePix(self):
        self.prepareGeometryChange()
        pt_1 = qtc.QPoint(self.min_x, self.min_y)
        pt_2 = qtc.QPoint(self.max_x, self.max_y)
        rect = qtc.QRect(pt_1, pt_2).adjusted(- 2.5 * self.radius, - 2.5 * self.radius, 
                                            2.5 * self.radius, 2.5 * self.radius)
        self.pix = self.pix.copy(rect)
        self.setPos(self.min_x - (2.5 * self.radius), self.min_y - (2.5 * self.radius))
        # self.update()
    
    # def shape(self):
    #     return self.boundingRect()

    def boundingRect(self):
        return qtc.QRectF(self.pix.rect())
    
    def paint(self, painter, options, widget):
        painter.drawPixmap(0, 0, self.pix)


class GraphicLine(qtw.QGraphicsItem):

    def __init__(self, start_pos, pen, parent=None):
        super(GraphicLine, self).__init__(parent)
        self.commit_pen = pen
        self.pen = Canvas.PREVIEW_PEN
        self.line = qtc.QLineF()
        self.line.setP1(start_pos)
        self.line.setP2(start_pos)
    
    def previewLine(self, end_pos):
        self.pen = Canvas.PREVIEW_PEN
        self.prepareGeometryChange()
        self.line.setP2(end_pos)
        self.update()
    
    # def commitLine(self, end_pos):
    #     self.pen = self.commit_pen
    #     self.line.setP2(end_pos)
    #     self.update()
    
    def toggleEditing(self, state):
        self.editing = state
        if state:
            self.unsetCursor()
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
        if not self.editing:
            self.pen = self.commit_pen
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
            self.setCursor(qtc.Qt.OpenHandCursor)

    def boundingRect(self):
        return qtc.QRectF(self.line.p1(), self.line.p2()).normalized()

    def paint(self, painter, options, widget):
        painter.setPen(self.pen)
        painter.drawLine(self.line)


class GraphicPoly(qtw.QGraphicsItem):

    def __init__(self, start_pos, mode, pen, parent=None):
        super(GraphicPoly, self).__init__(parent)
        self.mode = mode.title()
        self.commit_pen = pen
        self.pen = Canvas.PREVIEW_PEN
        self.brush = None
        # self.vertices = [start_pos]
        if mode == 'polygon':
            self.poly = qtg.QPolygonF()
            self.poly.append(start_pos)

        elif mode == 'polyline':
            self.mode = 'Path'
            self.poly = qtg.QPainterPath()
            self.poly.moveTo(start_pos)
        # self.tmp_point = start_pos
        # self.vertices.append(self.tmp_point)

        # self.index = 1
        # print(self.mode)

    def addBrush(self, brush):
        self.brush = brush

    def adjustPenOffset(self, offset):
        self.pen.setDashOffset(offset)
    
    def toggleEditing(self, state):
        self.editing = state
        if state:
            self.unsetCursor()
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
        if not self.editing:
            self.pen = self.commit_pen
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
            self.setCursor(qtc.Qt.OpenHandCursor)
    
    # def previewPolyline(self, added_pt):
    #     # print('ADDING POINT')
    #     self.pen = Canvas.PREVIEW_PEN
    #     # self.vertices.append(added_pt)
    #     self.poly.lineTo(added_pt)
    #     self.update()

    def previewPoly(self, added_pt):
        # self.pen = Canvas.PREVIEW_PEN
        # self.prepareGeometryChange()
        # # print('PREVIEWING')
        # # self.poly.replace(self.index, added_pt)
        # self.vertices[-1] = added_pt
        # # self.poly.append(added_pt)
        # self.tmp_point = added_pt
        # self.update()
        pass
    
    def commitPoint(self, added_pt):
        # self.prepareGeometryChange()
        # # self.poly.replace(self.index, added_pt)
        # self.vertices[-1] = added_pt
        # # self.poly.append(added_pt)
        # self.vertices.append(self.tmp_point)
        if self.mode == "Polygon":
            self.poly.append(added_pt)
        else:
            self.poly.lineTo(added_pt)
        self.update()
    
    def commitPoly(self, final_pt):
        # self.prepareGeometryChange()
        # self.poly.replace(self.index, final_pt)
        # self.vertices[-1] = final_pt
        self.pen = self.commit_pen
        self.toggleEditing(False)
        self.update()

    def boundingRect(self):
        return self.poly.boundingRect()

    def paint(self, painter, options, widget):
        painter.setPen(self.pen)
        if self.brush:
            painter.setBrush(self.brush)
        getattr(painter, "draw%s" % self.mode)(self.poly)


class GraphicShape(qtw.QGraphicsItem):

    def __init__(self, start_pos, mode, args, pen,parent=None):
        super(GraphicShape, self).__init__(parent)

        self.commit_pen = pen
        self.pen = Canvas.PREVIEW_PEN
        self.brush = None
        self.shape = qtc.QRectF(start_pos, start_pos)
        self.mode = mode.title()
        if mode == 'roundrect':
            self.mode = 'RoundedRect'
        self.paint_args = args 

    def addBrush(self, brush):
        self.brush = brush

    def adjustPenOffset(self, offset):
        self.pen.setDashOffset(offset)


    def toggleEditing(self, state):
        self.editing = state
        if state:
            self.unsetCursor()
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, False) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
        if not self.editing:
            self.pen = self.commit_pen
            self.setFlag(qtw.QGraphicsItem.ItemIsMovable, True) 
            self.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
            self.setCursor(qtc.Qt.OpenHandCursor)
    
    def previewShape(self, corner_pt):
        self.prepareGeometryChange()
        self.shape.setBottomRight(corner_pt)
        self.update()
    
    def commitShape(self, final_pt):
        self.shape.setBottomRight(final_pt)
        self.pen = self.commit_pen
        self.toggleEditing(False)
    

    def boundingRect(self):
        return self.shape
    

    def paint(self, painter, options, widget):
        painter.setPen(self.pen)
        if self.brush:
            painter.setBrush(self.brush)
        getattr(painter, "draw%s" % self.mode)(self.shape, *self.paint_args)


