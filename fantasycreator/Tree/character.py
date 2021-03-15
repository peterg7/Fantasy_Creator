
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import re
import uuid
import datetime

# User-defined Modules
from Mechanics.flags import TREE_ICON_DISPLAY, EVENT_TYPE
from Mechanics.storyTime import Time, DateLineEdit

# External resources
from resources import resources


# Create Character class
class Character(qtw.QGraphicsWidget):

    ICON_HEIGHT = 180
    ICON_WIDTH = 180

    CROWN_HEIGHT = 50
    RULER_PIC_PATH = ':/dflt-tree-images/crown.png'
    BUTTON_WIDTH = 35

    item_moved = qtc.pyqtSignal(qtc.QPointF)

    def __init__(self, char_dict=None, char_id=None, x_pos=0, y_pos=0, parent=None):
        super(Character, self).__init__(parent)
        self.setX(x_pos)
        self.setY(y_pos)
        self.setFlags(qtw.QGraphicsItem.ItemIsFocusable | 
                        qtw.QGraphicsItem.ItemIsSelectable | 
                        qtw.QGraphicsItem.ItemClipsToShape)
        # self.setFlag(qtw.QGraphicsItem.ItemSendsGeometryChanges)
        # self.setFlag(qtw.QGraphicsItem.ItemIsMovable)
        self.setCacheMode(qtw.QGraphicsItem.ItemCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setCursor(qtc.Qt.PointingHandCursor)
        self.setZValue(2)

        self.add_desc = qtw.QPushButton(
            '+',
            clicked=lambda: self.parent().add_descendant.emit(self.uniq_id)
        )
        # self.add_btn.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.add_desc.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: green;
                            border-style: outset;
                            border-radius: 3px;
                            color: green;
                            font: bold 26px;
                            background-color: rgba(66, 245, 117, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(66, 245, 117, 70);
                            border-style: inset;
                        }""")

        self.del_desc = qtw.QPushButton(
            '-',
            clicked=lambda: self.parent().remove_character.emit(self.uniq_id)
        )
        # self.del_btn.setFixedSize(self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.del_desc.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: red;
                            border-style: outset;
                            border-radius: 3px;
                            color: red;
                            font: bold 32px;
                            background-color: rgba(245, 66, 66, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(245, 66, 66, 70);
                            border-style: inset;
                        }""")
        
        self.add_partner = qtw.QPushButton(
            '+',
            clicked=lambda: self.parent().add_partner.emit(self.uniq_id)
        )
        # self.partner_btn.setFixedSize(self.BUTTON_HEIGHT, self.BUTTON_WIDTH)
        self.add_partner.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: blue;
                            border-style: outset;
                            border-radius: 3px;
                            color: blue;
                            font: bold 26px;
                            background-color: rgba(66, 197, 245, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(66, 197, 245, 70);
                            border-style: inset;
                        }""")
        
        self.del_partner = qtw.QPushButton(
            '-',
            clicked=lambda: self.parent().remove_partnership[uuid.UUID].emit(self.uniq_id)
        )
        # self.partner_btn.setFixedSize(self.BUTTON_HEIGHT, self.BUTTON_WIDTH)
        self.del_partner.setStyleSheet("""
                        QPushButton { 
                            border-width: 3px;
                            border-color: yellow;
                            border-style: outset;
                            border-radius: 3px;
                            color: yellow;
                            font: bold 28px;
                            background-color: rgba(245, 218, 66, 40);
                        }
                        QPushButton:pressed { 
                            background-color: rgba(245, 218, 66, 70);
                            border-style: inset;
                        }""")

        self.add_desc_btn = qtw.QGraphicsProxyWidget(self)
        self.add_desc_btn.setWidget(self.add_desc)
        self.add_desc_btn.setToolTip("Add Descendant")
        self.add_desc_btn.setVisible(False)

        self.del_desc_btn = qtw.QGraphicsProxyWidget(self)
        self.del_desc_btn.setWidget(self.del_desc)
        self.del_desc_btn.setToolTip("Delete Character")
        self.del_desc_btn.setVisible(False)

        self.add_partner_btn = qtw.QGraphicsProxyWidget(self)
        self.add_partner_btn.setWidget(self.add_partner)
        self.add_partner_btn.setToolTip("Add Partner")
        self.add_partner_btn.setVisible(False)

        self.del_partner_btn = qtw.QGraphicsProxyWidget(self)
        self.del_partner_btn.setWidget(self.del_partner)
        self.del_partner_btn.setToolTip("Remove Partner")
        self.del_partner_btn.setVisible(False)

        # Character properties
        self.uniq_id = char_id 
        # self.clone_num = 0       
        self.tree_id = None
        self.name = ''
        self.parent_0 = None
        self.parent_1 = None
        self.tree_pos = None
        self.ruler = False
        self.picture_loc = ''

        self.display_font = qtg.QFont('Cochin')
        self.display_font.setPointSize(40)
        self.display_font.setWeight(qtg.QFont.DemiBold)

        self.ruler_display_flag = True
        self.current_display_mode = TREE_ICON_DISPLAY.IMAGE

        # self.pixmap = qtw.QGraphicsPixmapItem()
        self.pixmap = None
        self.img = None
        self.img_ruler_pixmap = None
        self.name_ruler_pixmap = None
        self.offset = (0, 0)

        if char_dict is not None:
            self.parseDict(char_dict)
    
    ## Auxiliary Methods ##

    # def removeSelf(self):
    #     self.parent().delete_character(self.uniq_id)
    #     self.parent().removed_character.emit(char_id)

    def parseDict(self, dictionary):
        self.uniq_id = dictionary.get('char_id', self.uniq_id)
        if not self.uniq_id:
            self.uniq_id = uuid.uuid4()
        # self.clone_num = dictionary.get('clone', self.clone_num)
        # self.clone_num += 1
        # self.romance_id = dictionary.get('romance_id', self.romance_id)
        self.tree_id = dictionary.get('tree_id', self.tree_id)
        self.name = dictionary.get('name', self.name)
        ruler_input = dictionary.get('ruler', self.ruler)
        self.parent_0 = dictionary.get('parent_0', self.parent_0)
        self.parent_1 = dictionary.get('parent_1', self.parent_1)
        self.tree_pos = dictionary.get('tree_pos', self.tree_pos)
        if img := dictionary.get('__IMG__', None):
            # print('Using img')
            if isinstance(img, qtg.QImage):
                self.pixmap = qtg.QPixmap.fromImage(img)
            else: # Assume instance of QPixmap
                self.pixmap = img

            self.current_pixmap = self.pixmap
            self.updatePixmapImage()
            self.img = img

        # else:
        #     picture_loc_input = dictionary.get('picture_path', self.picture_loc)
        #     if picture_loc_input != self.picture_loc:
        #         self.updatePixmapImage(picture_loc_input)
        if self.ruler != ruler_input:
            self.ruler = ruler_input
            if self.ruler_display_flag:
                self.showRuler(self.ruler)
        self.setToolTip(self.name)
        self.updateButtons()

    def toDict(self):
        char_dict = {}
        char_dict['char_id'] = self.uniq_id
        char_dict['tree_id'] = self.tree_id
        char_dict['name'] = self.name
        char_dict['ruler'] = self.ruler
        char_dict['parent_0'] = self.parent_0
        char_dict['parent_1'] = self.parent_1
        char_dict['picture_path'] = self.picture_loc
        char_dict['__IMG__'] = self.img
        return char_dict
    
    def clone(self):
        char = Character()
        char.parseDict(self.toDict())
        return char

    def setDisplayMode(self, display_mode):
        if display_mode == TREE_ICON_DISPLAY.IMAGE:
            self.current_display_mode = TREE_ICON_DISPLAY.IMAGE
            self.updatePixmapImage(self.picture_loc)

        elif display_mode == TREE_ICON_DISPLAY.NAME:
            self.current_display_mode = TREE_ICON_DISPLAY.NAME
            self.setNameDisplay()
        
        if self.ruler_display_flag:
            self.showRuler(self.ruler)
        self.updateButtons()
    
    def setNameDisplay(self):
        # size = qtc.QSize(self.pixmap.pixmap().width(), self.pixmap.pixmap().height())
        font_metric = qtg.QFontMetrics(self.display_font)
        text_width = font_metric.horizontalAdvance(self.name)

        size = qtc.QSize(text_width, self.ICON_HEIGHT/2)


        result_px = qtg.QPixmap(size)
        result_px.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(result_px)
        bounding_rect = qtc.QRect(0, 0, text_width, self.ICON_HEIGHT/2)
        painter.setFont(self.display_font)
        painter.drawText(bounding_rect, qtc.Qt.AlignCenter, self.name)
        painter.end()
        # self.pixmap.setPixmap(result_px)
        # self.pixmap.setOffset(-text_width / 2, -self.ICON_HEIGHT / 4)
        # self.pixmap.setShapeMode(qtw.QGraphicsPixmapItem.BoundingRectShape)
        self.current_pixmap = result_px
        self.offset = (-text_width / 2, -self.ICON_HEIGHT / 4)
    

    def buildNameRulerPix(self):
        img = qtg.QImage(self.RULER_PIC_PATH)
        img.convertTo(qtg.QImage.Format_ARGB32_Premultiplied)
        crown_px = qtg.QPixmap.fromImage(img)

        crown_px = crown_px.scaledToHeight(self.CROWN_HEIGHT)
        crown_point = qtc.QPoint((self.pixmap.width()-crown_px.width())/2, 0)
        
        size = qtc.QSize(self.current_pixmap.width(), self.current_pixmap.height() + self.CROWN_HEIGHT)
        char_rect = qtc.QRect(0, self.CROWN_HEIGHT, self.current_pixmap.width(), self.current_pixmap.height())
        result_px = qtg.QPixmap(size)
        result_px.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(result_px)
        painter.setRenderHint(qtg.QPainter.TextAntialiasing)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        painter.drawPixmap(char_rect, self.current_pixmap)
        painter.drawPixmap(crown_point, crown_px)
        painter.end()
        self.name_ruler_pixmap = result_px

    def buildImgRulerPix(self):
        img = qtg.QImage(self.RULER_PIC_PATH)
        img.convertTo(qtg.QImage.Format_ARGB32_Premultiplied)
        crown_px = qtg.QPixmap.fromImage(img)

        crown_px = crown_px.scaledToHeight(self.CROWN_HEIGHT)
        crown_point = qtc.QPoint((self.pixmap.width()-crown_px.width())/2, 0)
        
        size = qtc.QSize(self.pixmap.width(), self.pixmap.height() + self.CROWN_HEIGHT)
        char_rect = qtc.QRect(0, self.CROWN_HEIGHT, self.pixmap.width(), self.pixmap.height())
        result_px = qtg.QPixmap(size)
        result_px.fill(qtc.Qt.transparent)
        painter = qtg.QPainter(result_px)
        painter.setRenderHint(qtg.QPainter.TextAntialiasing)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        painter.drawPixmap(char_rect, self.pixmap)
        painter.drawPixmap(crown_point, crown_px)
        painter.end()
        self.img_ruler_pixmap = result_px

    def showRuler(self, ruler_state):
        if ruler_state:
            if self.current_display_mode == TREE_ICON_DISPLAY.IMAGE:
                if not self.img_ruler_pixmap:
                    self.buildImgRulerPix()
                self.prepareGeometryChange()
                self.current_pixmap = self.img_ruler_pixmap
                self.offset = (-self.current_pixmap.width() / 2, -self.current_pixmap.height() / 2 - self.CROWN_HEIGHT/2)

            elif self.current_display_mode == TREE_ICON_DISPLAY.NAME:
                self.setNameDisplay()
                if not self.name_ruler_pixmap:
                    self.buildNameRulerPix()
                self.prepareGeometryChange()
                self.current_pixmap = self.name_ruler_pixmap
                self.offset = (-self.current_pixmap.width() / 2, -self.current_pixmap.height() / 2 - self.CROWN_HEIGHT/2)

        elif self.current_display_mode == TREE_ICON_DISPLAY.IMAGE:
            self.updatePixmapImage()
        elif self.current_display_mode == TREE_ICON_DISPLAY.NAME:
            self.setNameDisplay()
    
    def setRulerDisplay(self, flag):
        self.ruler_display_flag = flag
        if self.ruler_display_flag:
            self.showRuler(self.ruler)
        else:
            self.current_pixmap = self.pixmap
            self.showRuler(False)
        self.updateButtons()
    
    def updatePixmapImage(self, pix=None):
        self.current_pixmap = self.pixmap
        self.offset = (-self.current_pixmap.width() / 2, -self.current_pixmap.height() / 2)
        
        
    def updateButtons(self):
        pix_height = self.current_pixmap.height()
        pix_width = self.current_pixmap.width()

        self.add_desc_btn.resize(pix_width + 70, self.BUTTON_WIDTH)
        self.del_desc_btn.resize(pix_width + 70, self.BUTTON_WIDTH)
        self.add_partner_btn.resize(self.BUTTON_WIDTH, pix_height)
        self.del_partner_btn.resize(self.BUTTON_WIDTH, pix_height)

        if self.ruler and self.ruler_display_flag:
            self.add_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                                        pix_height/2 - self.CROWN_HEIGHT/2)
            self.del_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                        -pix_height/2 - self.CROWN_HEIGHT/2 - self.BUTTON_WIDTH - 9)
            self.add_partner_btn.setPos(pix_width/2, -pix_height/2 - self.CROWN_HEIGHT/2)
            self.del_partner_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                                        -pix_height/2 - self.CROWN_HEIGHT/2)
        else:
            self.add_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, pix_height/2)
            self.del_desc_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, 
                                                -pix_height/2 - self.BUTTON_WIDTH - 9)
            self.add_partner_btn.setPos(pix_width/2, -pix_height/2)
            self.del_partner_btn.setPos(-pix_width/2 - self.BUTTON_WIDTH, -pix_height/2)
        


    ## Accessors and Mutators ##

    def setTreePos(self, pos):
        self.tree_pos = pos
    
    def setParentID(self, char_id, parent_index=0):
        if not parent_index:
            self.parent_0 = char_id
        else:
            self.parent_1 = char_id
    
    def setTreeID(self, tree_id):
        self.tree_id = tree_id

    # def setRomanceID(self, rom_id):
    #     self.romance_id = rom_id

    def getName(self):
        return self.name
    
    def setName(self, new_name):
        self.name = new_name

    def getID(self):
        return self.uniq_id
    
    # def getRomanceID(self):
    #     return self.romance_id
    def getTreeID(self):
        return self.tree_id

    def getWidth(self):
        return self.current_pixmap.width()
    
    def getHeight(self):
        return self.current_pixmap.height()
    
    def addXOffset(self, offset):
        self.setX(self.x() + offset)
    
    def addYOffset(self, offset):
        self.setY(self.y() + offset)
    
    ## Override paint methods ##

    def paint(self, painter, option, widget):
        # self.pixmap.paint(painter, option, widget)
        painter.drawPixmap(self.x() + self.offset[0], self.y() + self.offset[1], self.current_pixmap)

    def boundingRect(self):
        bounding_rect = self.current_pixmap.rect()
        bounding_rect.translate(self.offset[0], self.offset[1])
        bounding_rect.adjust(-35, -35, 35, 35)
        return qtc.QRectF(bounding_rect)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    ## Override Built-In Slots ##


    def contextMenuEvent(self, event):
    # def launchContextMenu(self, event):
        menu = qtw.QMenu("Options")
        edit_act = menu.addAction("Edit...")
        add_part_act = menu.addAction("Add partner")
        rem_part_act = menu.addAction("Remove partner")
        add_parent_act = menu.addAction("Add parent")
        # rem_parent_act = menu.addAction("Add parent")
        add_desc_act = menu.addAction("Add descendant")
        rem_char_act = menu.addAction("Delete character")
        selected_act = menu.exec(event.screenPos())
        if selected_act == edit_act:
            self.parent().edit_char.emit(self.uniq_id)
        elif selected_act == add_part_act:
            self.parent().add_partner.emit(self.uniq_id)
        elif selected_act == rem_part_act:
            self.parent().remove_partnership[uuid.UUID].emit(self.uniq_id)
        elif selected_act == add_parent_act:
            self.parent().add_parent.emit(self.uniq_id)
        # elif selected_act == rem_parent_act:
        #     print('Removing parent- in construction')
        elif selected_act == add_desc_act:
            self.parent().add_descendant.emit(self.uniq_id)
        elif selected_act == rem_char_act:
            self.parent().remove_character.emit(self.uniq_id)
        event.accept()
        # super(Character, self).contextMenuEvent(event)
        self.setCursor(qtc.Qt.PointingHandCursor)
        


    def hoverEnterEvent(self, event):
        self.add_desc_btn.setVisible(True)
        self.del_desc_btn.setVisible(True)
        self.add_partner_btn.setVisible(True)
        self.del_partner_btn.setVisible(True)
        super(Character, self).hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.add_desc_btn.setVisible(False)
        self.del_desc_btn.setVisible(False)
        self.add_partner_btn.setVisible(False)
        self.del_partner_btn.setVisible(False)
        super(Character, self).hoverLeaveEvent(event)


    ## Operator Overloads ##

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.uniq_id
    
    def __hash__(self):
        return hash(self.uniq_id)

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return self.uniq_id == other
        elif isinstance(other, Character):
            return self.uniq_id == other.uniq_id
        else:
            return self is other


