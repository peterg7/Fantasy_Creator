
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# Built-in Modules
import uuid

# User-defined Modules
from materializer import Materializer
from storyTime import TimeConstants, Time, DateLineEdit
from flags import EVENT_TYPE, DIRECTION

class TimelineEntry(qtw.QGraphicsWidget):

    # Green
    DFLT_COLOR = '#376e43'

    # Green, blue, magenta, burnt orange, yellow, brown
    COLORS = ['#267382', '#376e43', '#822654', '#824626', 
                '#bfa11d', '#6b2e07']

    ENTRY_HEIGHT = 33

    MAIN_AXIS_MAX = 8000
    MAIN_AXIS_MIN = 500

    stopped_movement = qtc.pyqtSignal(int, uuid.UUID, Time, Time)
    shift_entry = qtc.pyqtSignal(int, uuid.UUID)
    add_view = qtc.pyqtSignal(uuid.UUID)
    add_edit = qtc.pyqtSignal(uuid.UUID)
    del_entry = qtc.pyqtSignal(uuid.UUID)

    def __init__(self, entry_id, name, color=None, order=-1, parent=None):
        super(TimelineEntry, self).__init__(parent)
        self.materializer = Materializer()
        self._id = entry_id
        self._name = name
        self._order = order
        self.display_rect = qtc.QRectF()
        self.start = 0
        self.end = 0
        # self.interval  MUST BE IMPLEMENTED BY DERIVED CLASSES
        self.color = qtg.QColor(color if color else self.DFLT_COLOR) 
        self.pen = qtg.QPen(qtg.QColor('white'), 2)
        self.font = qtg.QFont('Cochin', 26)
        self.font_metric = qtg.QFontMetrics(self.font)
        self.year_labels = []
        self.setting_pos = False

        self.setCursor(qtc.Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        self.setFlags(qtw.QGraphicsItem.ItemIsMovable | 
                    qtw.QGraphicsItem.ItemIsSelectable |
                    qtw.QGraphicsItem.ItemSendsGeometryChanges)


    def getID(self):
        return self._id

    def shiftClocks(self, reorder=False):
        if reorder:
            self.start.reOrder()
            self.end.reOrder()
            # self.interval.reOrder()
        self.start.validateTime(True)
        self.end.validateTime(True)
        self.updateInterval(self.start, self.end)
        self.update()
    
    def setTime(self, start_date):
        self.start = start_date
        # self.end = self.materializer.getTimeSummation(start_date, self.interval)
        self.end = start_date + self.interval

        start_label = self.year_labels[0].widget()
        # start_label.setText('{0} • {1} • {2}'.format(*self.start))
        start_label.setText(str(self.start))
        start_label.adjustSize()

        if self.year_labels[1]:
            end_label = self.year_labels[1].widget()
            # end_label.setText('{0} • {1} • {2}'.format(*self.end))
            end_label.setText(str(self.end))
            end_label.adjustSize()
    
    def shiftEntry(self, shift_amt):
        self.setting_pos = True
        self.setY(self.y() + shift_amt)
        self.setting_pos = False

    def itemChange(self, change, value):
        if change == qtw.QGraphicsItem.ItemPositionChange and self.scene():
            # dx = value.x() - self.x()
            if value.x() < TimelineEntry.MAIN_AXIS_MIN :
                return qtc.QPointF(TimelineEntry.MAIN_AXIS_MIN, self.y()) 

            if value.x() > (TimelineEntry.MAIN_AXIS_MAX - self.display_rect.width()):
                return qtc.QPointF(TimelineEntry.MAIN_AXIS_MAX - self.display_rect.width(), self.y())
            
            # self.ensureVisible() # PROBLEM PROBLEM PROBLEM!!!

            if not self.setting_pos:
                self.setTime(self.materializer.mapToTime(value.x()))
                return qtc.QPointF(value.x(), self.y()) 
        return super(TimelineEntry, self).itemChange(change, value)
    

    def hoverEnterEvent(self, event):
        self.year_labels[0].setVisible(True)
        if self.year_labels[1]:
            self.year_labels[1].setVisible(True)
        super(TimelineEntry, self).hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.year_labels[0].setVisible(False)
        if self.year_labels[1]:
            self.year_labels[1].setVisible(False)
        super(TimelineEntry, self).hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        self.setCursor(qtc.Qt.ClosedHandCursor)
        super(TimelineEntry, self).mousePressEvent(event)


    def __str__(self):
        return self._name
    
    def __repr__(self):
        return self._id
    
    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if isinstance(other, uuid.UUID):
            return self._id == other
        elif isinstance(other, TimelineCharEntry):
            return self._id == other._id
        else:
            return self is other
    



class TimelineCharEntry(TimelineEntry):

    def setTimeInterval(self, start_date, end_date):
        self.start = start_date
        self.end = end_date
        self.prepareGeometryChange()
        # self.interval = self.materializer.getTimeDifference(end_date, start_date)
        self.interval = end_date - start_date
        width = self.materializer.mapTimeRange(end_date, start_date)
        self.display_rect = qtc.QRectF(0, 0, width, self.ENTRY_HEIGHT)

        start_proxy = qtw.QGraphicsProxyWidget(self)
        start_label = qtw.QLabel()
        start_label.setAttribute(qtc.Qt.WA_TranslucentBackground)
        start_label.setFont(self.font)
        # start_label.setText('{0} • {1} • {2}'.format(*start_date))
        start_label.setText(str(start_date))
        start_label.adjustSize()
        start_proxy.setWidget(start_label)
        start_proxy.setPos(self.display_rect.bottomLeft().x() - start_label.width()/2, self.display_rect.bottomLeft().y())
        start_proxy.setVisible(False)
        self.year_labels.append(start_proxy)

        if self.start != self.end:
            end_proxy = qtw.QGraphicsProxyWidget(self)
            end_label = qtw.QLabel()
            end_label.setAttribute(qtc.Qt.WA_TranslucentBackground)
            end_label.setFont(self.font)
            # end_label.setText('{0} • {1} • {2}'.format(*end_date))
            end_label.setText(str(end_date))
            end_label.adjustSize()
            end_proxy.setWidget(end_label)
            end_proxy.setPos(self.display_rect.bottomRight().x() - end_label.width()/2, self.display_rect.bottomRight().y())
            end_proxy.setVisible(False)
            self.year_labels.append(end_proxy)

            if start_proxy.collidesWithItem(end_proxy):
                midline = self.display_rect.center().x()
                min_spacer = 10
                max_spacer = 10
                start_proxy.setPos(midline - min_spacer - start_label.width(), start_proxy.y())
                end_proxy.setPos(midline + max_spacer, end_proxy.y())
        else:
            self.year_labels.append(None)
        
        if self.font_metric.boundingRect(self._name).width() > self.display_rect.width():
            self.pen = qtg.QPen(qtg.QColor('black'), 2)
            self.offset = (self.font_metric.boundingRect(self._name).width() - self.display_rect.width()) / 2
        else:
            self.pen = qtg.QPen(qtg.QColor('white'), 2)
            self.offset = 0

        self.setX(self.materializer.mapTime(start_date))
        # self.setTime(start_date)

    def contextMenuEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        menu = qtw.QMenu("Options")
        # edit_act = menu.addAction("Edit...")
        edit_char_act = menu.addAction("Edit...")
        view_act = menu.addAction("Character view")
        shift_up_act = menu.addAction("Shift character up")
        shift_down_act = menu.addAction("Shift character down")
        selected_act = menu.exec(event.screenPos())

        # if selected_act == edit_act:
        #     self.parent().edit_char.emit(self._id)
        if selected_act == edit_char_act:
            self.add_edit.emit(self._id)
        elif selected_act == view_act:
            self.add_view.emit(self._id)
        elif selected_act == shift_up_act:
            self.shift_entry.emit(DIRECTION.UP, self._id)
        elif selected_act == shift_down_act:
            self.shift_entry.emit(DIRECTION.DOWN, self._id)

        event.accept()
        self.unsetCursor()

    def updateInterval(self, start_date=None, end_date=None):
        if start_date:
            self.start = start_date
        if end_date:
            self.end = end_date
        self.prepareGeometryChange()
        # self.interval = self.materializer.getTimeDifference(end_date, start_date)
        self.interval = self.end - self.start
        width = self.materializer.mapTimeRange(self.end, self.start)
        self.display_rect = qtc.QRectF(0, 0, width, self.ENTRY_HEIGHT)

        self.year_labels[0].setPos(self.display_rect.bottomLeft().x() - self.year_labels[0].widget().width()/2, 
                                    self.display_rect.bottomLeft().y())
        if self.year_labels[1]:
            self.year_labels[1].setPos(self.display_rect.bottomRight().x() - self.year_labels[1].widget().width()/2, 
                                        self.display_rect.bottomRight().y())
            if self.year_labels[0].collidesWithItem(self.year_labels[1]):
                midline = self.display_rect.center().x()
                min_spacer = 10
                max_spacer = 10
                self.year_labels[0].setPos(midline - min_spacer - self.year_labels[0].widget().width(), 
                                    self.year_labels[0].y())
                self.year_labels[1].setPos(midline + max_spacer, 
                                    self.year_labels[1].y())
        if self.font_metric.boundingRect(self._name).width() > self.display_rect.width():
            self.pen = qtg.QPen(qtg.QColor('black'), 2)
            self.offset = (self.font_metric.boundingRect(self._name).width() - self.display_rect.width()) / 2
        else:
            self.pen = qtg.QPen(qtg.QColor('white'), 2)
            self.offset = 0

        self.setTime(self.start)
        self.setX(self.materializer.mapTime(self.start))
        self.setCursor(qtc.Qt.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        self.stopped_movement.emit(EVENT_TYPE.CHAR, self._id, self.start, self.end)
        super(TimelineCharEntry, self).mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        painter.setFont(self.font)
        painter.setBrush(self.color)
        painter.drawRoundedRect(self.display_rect, 5, 5)
        painter.setPen(self.pen)
        rect = qtc.QRectF(self.font_metric.boundingRect(self._name))
        rect.moveCenter(self.display_rect.center())
        painter.drawText(rect, self._name)

    def boundingRect(self):
        return self.display_rect.adjusted(-self.offset, 0, self.offset, 0)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.display_rect.adjusted(-self.offset, 0, self.offset, 0))
        return path


class TimelineEventEntry(TimelineEntry):

    DFLT_COLOR = '#822626'

    def __init__(self, entry_id, name, color=None, parent=None):
        TimelineEntry.__init__(self, entry_id, name, color, parent)
        self.name_font = qtg.QFont('Baskerville', 30)
        self.brush = qtg.QBrush(qtg.QColor(self.DFLT_COLOR))
        self.outline_pen = qtg.QPen(qtg.QColor('black'), 0)

    def buildShape(self):
        self._shape = qtg.QPainterPath()
        self._shape.moveTo(self.display_rect.bottomLeft())
        self._shape.lineTo(self.display_rect.topLeft().x() - 10, self.display_rect.topLeft().y())
        self._shape.lineTo(self.display_rect.topRight().x() + 10, self.display_rect.topRight().y())
        self._shape.lineTo(self.display_rect.bottomRight())
        self._shape.lineTo(self.display_rect.bottomLeft())
       

    def setTimeInterval(self, start_date, end_date):
        self.start = start_date
        self.end = end_date

        # self.interval = self.materializer.getTimeDifference(end_date, start_date)
        self.interval = self.end - self.start
        width = self.materializer.mapTimeRange(self.end, self.start)
        self.display_rect = qtc.QRectF(0, 0, width, self.ENTRY_HEIGHT)

        start_proxy = qtw.QGraphicsProxyWidget(self)
        self.name_proxy = qtw.QGraphicsProxyWidget(self)

        start_label = qtw.QLabel()
        name_label = qtw.QLabel()

        start_label.setAttribute(qtc.Qt.WA_TranslucentBackground)
        name_label.setAttribute(qtc.Qt.WA_TranslucentBackground)

        start_label.setFont(self.font)
        name_label.setFont(self.name_font)

        # start_label.setText('{0} • {1} • {2}'.format(*start_date))
        start_label.setText(str(start_date))
        name_label.setText(self._name)

        start_label.adjustSize()
        name_label.adjustSize()

        start_proxy.setWidget(start_label)
        self.name_proxy.setWidget(name_label)

        start_proxy.setPos(self.display_rect.topLeft().x() - start_label.width()/2, 
                            self.display_rect.topLeft().y() - start_label.height())
        self.name_proxy.setPos(self.display_rect.center().x() - name_label.width()/2, 
                                self.display_rect.top() - name_label.height())
        
        start_proxy.setVisible(False)
        self.year_labels.append(start_proxy)

        if self.start != self.end:
            end_proxy = qtw.QGraphicsProxyWidget(self)
            end_label = qtw.QLabel()
            end_label.setAttribute(qtc.Qt.WA_TranslucentBackground)
            end_label.setFont(self.font)
            # end_label.setText('{0} • {1} • {2}'.format(*end_date))
            end_label.setText(str(end_date))
            end_label.adjustSize()
            end_proxy.setWidget(end_label)
            end_proxy.setPos(self.display_rect.topRight().x() - end_label.width()/2, 
                            self.display_rect.topRight().y() - end_label.height())
            self.year_labels.append(end_proxy)
            end_proxy.setVisible(False)

            if start_proxy.collidesWithItem(end_proxy):
                del end_proxy

        else:
            self.year_labels.append(None)

        if start_proxy.collidesWithItem(self.name_proxy):
            start_proxy.setPos(start_proxy.x(), start_proxy.y() - self.name_proxy.preferredHeight())
        
        self.buildShape()
        self.setX(self.materializer.mapTime(start_date))
        # self.setTime(start_date)

    def updateInterval(self, start_date=None, end_date=None):
        if start_date:
            self.start = start_date
        if end_date:
            self.end = end_date
        self.prepareGeometryChange()
        # self.interval = self.materializer.getTimeDifference(end_date, start_date)
        self.interval = self.end - self.start
        width = self.materializer.mapTimeRange(self.end, self.start)
        self.display_rect = qtc.QRectF(0, 0, width, self.ENTRY_HEIGHT)

        self.name_proxy.setPos(self.display_rect.center().x() - self.name_proxy.widget().width()/2, 
                                self.display_rect.top() - self.name_proxy.widget().height())

        self.year_labels[0].setPos(self.display_rect.topLeft().x() - self.year_labels[0].widget().width()/2, 
                                self.display_rect.topLeft().y() - self.year_labels[0].widget().height())        
        if self.year_labels[0].collidesWithItem(self.name_proxy):
            self.year_labels[0].setPos(self.year_labels[0].x(), self.year_labels[0].y() - self.name_proxy.preferredHeight())

        if self.year_labels[1]:
            self.year_labels[1].setPos(self.display_rect.topRight().x() - self.year_labels[1].widget().width()/2, 
                                        self.display_rect.topRight().y() - self.year_labels[1].widget().height())
            if self.year_labels[1].collidesWithItem(self.name_proxy):
                self.year_labels[1].setPos(self.year_labels[1].x(), self.year_labels[1].y() - self.name_proxy.preferredHeight())
            
            if self.year_labels[0].collidesWithItem(self.year_labels[1]):
                midline = self.display_rect.center().x()
                min_spacer = 10
                max_spacer = 10
                self.year_labels[0].setPos(midline - min_spacer - self.year_labels[0].widget().width(), 
                                    self.year_labels[0].y())
                self.year_labels[1].setPos(midline + max_spacer, 
                                    self.year_labels[1].y())
        
        self.buildShape()
        self.setTime(self.start)
        self.setX(self.materializer.mapTime(self.start))
        self.setCursor(qtc.Qt.PointingHandCursor)


    def contextMenuEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        menu = qtw.QMenu("Options")
        # edit_act = menu.addAction("Edit...")
        edit_event_act = menu.addAction("Edit...")
        view_act = menu.addAction("Event view")
        del_event_act = menu.addAction("Delete event")
        selected_act = menu.exec(event.screenPos())

        # if selected_act == edit_act:
        #     self.parent().edit_char.emit(self._id)
        if selected_act == edit_event_act:
            self.add_edit.emit(self._id)
        elif selected_act == view_act:
            self.add_view.emit(self._id)
        elif selected_act == del_event_act:
            self.del_event_act.emit(self._id)

        event.accept()
        self.unsetCursor()


    def mouseReleaseEvent(self, event):
        self.setCursor(qtc.Qt.PointingHandCursor)
        self.stopped_movement.emit(EVENT_TYPE.EVENT, self._id, self.start, self.end)
        super(TimelineEventEntry, self).mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        painter.setPen(qtc.Qt.NoPen)
        painter.fillPath(self._shape, self.brush)
        # painter.setPen(self.outline_pen)
        painter.drawPath(self._shape)

    def boundingRect(self):
        return self._shape.boundingRect()
    
    def shape(self):
        return self._shape


class MainTimelineAxis(qtw.QGraphicsObject):

    AXIS_HEIGHT = 60
    # YEAR_WEIGHT = 10

    def __init__(self, minDate, maxDate, parent=None):
        super(MainTimelineAxis, self).__init__(parent)
        self.materializer = Materializer()
        
        self.min_date = minDate
        self.max_date = maxDate
        # self.interval = self.materializer.getTimeDifference(maxDate, minDate)
        self.interval = maxDate - minDate
        self.num_intervals = 10
        self.brush = qtg.QBrush(qtg.QColor('#374a6e'))
        self.pen = qtg.QPen(qtg.QColor('gray'), 4, qtc.Qt.DashLine)
        self.font = qtg.QFont('Cochin', 36)
        self.font_metric = qtg.QFontMetrics(self.font)
        # TimelineCharEntry.ABS_ZERO = minYear
        # self.display_rect = qtc.QRectF(self.AXIS_PADDING, (2*self.AXIS_HEIGHT), 
                            # (self.YEAR_WEIGHT * self.interval) - (2*self.AXIS_PADDING), self.AXIS_HEIGHT)
        width =  self.materializer.mapTimeRange(self.max_date, self.min_date)
        #self.materializer.TIMELINE_AXIS_PADDING
        self.display_rect = qtc.QRectF(0, 2 * self.AXIS_HEIGHT, width, self.AXIS_HEIGHT)

        self.interval_lines = {}
        # self.drawIntervals()

    def drawIntervals(self):
        start_x = self.display_rect.x()
        top_y = self.display_rect.top() - 10
        bottom_y = self.display_rect.bottom() + 10
        line_spacer = self.display_rect.width() / self.num_intervals
        year_spacer = int(self.interval.getYear() / self.num_intervals)

        for x in range(1, self.num_intervals):
            # line = qtc.QLineF(start_x + (x * line_spacer), top_y, start_x + (x * line_spacer), bottom_y)
            # self.interval_lines[int(self.min_date[0] + (x * year_spacer))] = line
            # current_date = self.materializer.getTimeSummation(self.min_date, [(x * year_spacer), 0, 0])
            current_date = self.min_date + Time(day=0, month=0, year=x*year_spacer)
            
            target_pt = qtc.QPointF(self.materializer.mapTime(current_date), 0)
            target_x = self.mapFromParent(target_pt).x()
            # target_x = target_pt.x()
            line = qtc.QLineF(target_x, top_y, target_x, bottom_y)
            self.interval_lines[current_date.getYear()] = line


    def setMinDate(self, date):
        self.minDate = date
    
    def setMaxDate(self, date):
        self.maxDate = date
    
    def setNumIntervals(self, intervals):
        self.num_intervals = intervals
    
    def width(self):
        return self.display_rect.width()

    def height(self):
        return self.display_rect.height()

    def paint(self, painter, options, widget):
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        painter.setBrush(self.brush)
        painter.drawRoundedRect(self.display_rect, 8, 8)
        
        painter.setFont(self.font)
        # painter.drawLines(self.interval_lines)
        for label, line in self.interval_lines.items():
            self.pen.setColor(qtg.QColor('black'))
            painter.setPen(self.pen)
            rect = qtc.QRectF(self.font_metric.boundingRect(str(label)))
            rect.moveTo(line.p2())
            painter.drawText(rect, str(label))
            self.pen.setColor(qtg.QColor('gray'))
            painter.setPen(self.pen)
            painter.drawLine(line)

    def boundingRect(self):
        return self.display_rect


class EntryView(qtw.QGraphicsWidget):

    closed = qtc.pyqtSignal()
    CURRENT_SPAWN = qtc.QPoint(20, 60)  #NOTE: Magic Number

    def __init__(self, event_dict, parent=None):
        super(EntryView, self).__init__(parent)
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setFlags(qtw.QGraphicsItem.ItemIsMovable | qtw.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(qtc.Qt.OpenHandCursor)
        self.setScale(1.4)

        self._event = event_dict
        self._id = self._event['event_id']
        self.setObjectName('view{}'.format(self._id))

        self.brush = qtg.QBrush(qtg.QColor('#c9cdd4')) # make dependent upon gender? kingdom?
        self.translucent_effect = qtw.QGraphicsOpacityEffect(self)
        self.translucent_effect.setOpacity(0.8)
        self.setGraphicsEffect(self.translucent_effect)
        self.translucent_effect.setEnabled(False)

        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )

        self.display_widgets = qtw.QGraphicsItemGroup(self)

        # Set layout
        layout = qtw.QGraphicsLinearLayout(qtc.Qt.Vertical)
        label_style = """ QLabel {
                    background-color: #e3ddcc;
                    border-radius: 5px;
                    border-color: gray;
                    padding: 4px;
                    font: 24px;
                }"""
        
        # Create and add label widgets
        self.name_label = qtw.QGraphicsProxyWidget(self)
        self.name_label.setWidget(EntryViewLabel())
        self.name_label.widget().setStyleSheet("""QLabel {
                    background-color: rgba(255, 255, 255, 0);
                    border-radius: 5px;
                    border-color: gray;
                    padding: 4px;
                    font: 36px 'Didot';
                }""")
        self.name_label.widget().setAlignment(qtc.Qt.AlignHCenter | qtc.Qt.AlignVCenter)
        self.name_label.setAcceptHoverEvents(False)
        layout.addItem(self.name_label)


        self.start_label = qtw.QGraphicsProxyWidget(self)
        self.start_label.setWidget(EntryViewLabel())
        self.start_label.widget().setStyleSheet(label_style)
        self.start_label.setAcceptHoverEvents(False)
        layout.addItem(self.start_label)

        self.end_label = qtw.QGraphicsProxyWidget(self)
        self.end_label.setWidget(EntryViewLabel())
        self.end_label.widget().setStyleSheet(label_style)
        self.end_label.setAcceptHoverEvents(False)
        layout.addItem(self.end_label)


        self.loc_label = qtw.QGraphicsProxyWidget(self)
        self.loc_label.setWidget(EntryViewLabel())
        self.loc_label.widget().setStyleSheet(label_style)
        self.loc_label.setAcceptHoverEvents(False)
        layout.addItem(self.loc_label)

        self.updateView()

        self.cancel_btn = qtw.QGraphicsProxyWidget(self)
        self.cancel_btn.setWidget(qtw.QPushButton(
            'Cancel',
            clicked=self.close
        ))
        self.cancel_btn.widget().setStyleSheet("""
                        QPushButton { 
                            border: 1px solid black;
                            border-style: outset;
                            border-radius: 2px;
                            color: black;
                            font: 24px;
                            font-family: Baskerville;
                        }
                        QPushButton:pressed { 
                            background-color: rgba(255, 255, 255, 70);
                            border-style: inset;
                        }""")
        layout.addItem(self.cancel_btn)
        layout.setSpacing(16)
        self.setLayout(layout)
        
    
    def getID(self):
        return self._id
    
    def updateView(self):
        if self._event['event_name']:
            label_string = self._event['event_name']
        else:
            label_string = 'Event: ...'
        self.name_label.widget().setText(label_string)
        
        if self._event['start']:
            # label_string = f"<b>Start Date</b>: {'{0} • {1} • {2}'.format(*self._event['start'])}"
            label_string = f"<b>Start Date</b>: {str(self._event['end'])}"
        else:
            label_string = 'Start Date: ...'
        self.start_label.widget().setText(label_string)

        if self._event['end']:
            # label_string = f"<b>End Date</b>: {'{0} • {1} • {2}'.format(*self._event['end'])}"
            label_string = f"<b>End Date</b>: {str(self._event['end'])}"
        else:
            label_string = 'End Date: ...'
        self.end_label.widget().setText(label_string)

        if self._event['location']:
            label_string = f"<b>Location</b>: {self._event['location']}"
        else:
            label_string = 'Location: ...'
        self.loc_label.widget().setText(label_string)
    

    def check_selected(self):
        if self.isSelected():
            self.translucent_effect.setEnabled(False)
        else:
            self.translucent_effect.setEnabled(True)
    
    def sceneEventFilter(self, source, event):
        if event.type() != qtc.QEvent.GraphicsSceneHoverMove:
            # Intercept event
            return True
        return super(EntryView, self).sceneEventFilter(source, event)

    ## Override drawing methods ##

    def paint(self, painter, option, widget):
        frame = qtc.QRectF(qtc.QPointF(0, 0), self.geometry().size())
        painter.setBrush(self.brush)
        painter.drawRoundedRect(frame, 10, 10)
    
    def shape(self):
        path = qtg.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ## Override Built-In Slots ##
    def closeEvent(self, event):
        self.closed.emit()
        super(EntryView, self).closeEvent(event)
    
    def mousePressEvent(self, event):
        self.setCursor(qtc.Qt.ClosedHandCursor)
        event.accept()
        super(EntryView, self).mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(qtc.Qt.OpenHandCursor)
        event.accept()
        super(EntryView, self).mouseReleaseEvent(event)
    

class EntryViewLabel(qtw.QLabel):

    def __init__(self, parent=None):
        super(EntryViewLabel, self).__init__(parent)
        self.setTextFormat(qtc.Qt.RichText)
        self.setFont(qtg.QFont('Baskerville', 26))
        self.setCursor(qtc.Qt.OpenHandCursor)


# Event creation form
class EventCreator(qtw.QDialog):

    submitted = qtc.pyqtSignal(dict)
    closed = qtc.pyqtSignal()

    DFLT_PROFILE_PATH = ':/dflt-event-images/unknown_event_loc.png'

    TYPE_ITEMS = ["Select Type"]
    LOC_ITEMS = ["Select Location"]

    IMAGES_PATH = 'tmp/' # TODO: FIX THIS

    def __init__(self, parent=None, editingEvent=None):
        super(EventCreator, self).__init__(parent)
        self.setSizePolicy(
            qtw.QSizePolicy.Preferred,
            qtw.QSizePolicy.Preferred
        )
        self.setAttribute(qtc.Qt.WA_DeleteOnClose)
        self.setModal(True) # CAUSES BUG 

        self.setFixedSize(415, self.minimumHeight())

        self._id = 0

        layout = qtw.QFormLayout()

        # Create input widgets
        self.name = qtw.QLineEdit()
        self.name.setFont(qtg.QFont('Baskerville', 16))
        self.start_date = DateLineEdit()
        self.start_date.setFont(qtg.QFont('Baskerville', 16))
        self.end_date = DateLineEdit()
        self.end_date.setFont(qtg.QFont('Baskerville', 16))
        self.location_select = qtw.QComboBox()
        self.location_select.setFont(qtg.QFont('Baskerville', 16))
        self.type_select = qtw.QComboBox()
        self.type_select.setFont(qtg.QFont('Baskerville', 16))
        self.event_desc = qtw.QTextEdit()
        self.event_desc.setFont(qtg.QFont('Baskerville', 16))

        # Modify widgets
        self.location_select.addItems(EventCreator.LOC_ITEMS)
        self.location_select.model().item(0).setEnabled(False)

        self.type_select.addItems(EventCreator.TYPE_ITEMS)
        self.type_select.model().item(0).setEnabled(False)

        self.event_desc.setPlaceholderText('Description...')

        # Connect signals
        self.location_select.currentTextChanged.connect(self.on_loc_change)
        self.type_select.currentTextChanged.connect(self.on_type_change)

        self.submit_btn = qtw.QPushButton(
            'Submit',
            clicked=self.onSubmit
        )
        self.submit_btn.setDefault(True)
        self.submit_btn.setFont(qtg.QFont('Baskerville', 16))
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.close
        )
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setFont(qtg.QFont('Baskerville', 16))
        
        
        # Define layout
        layout.addRow('Name', self.name)
        label = layout.labelForField(self.name)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Start Date', self.start_date)
        label = layout.labelForField(self.start_date)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('End Date', self.end_date)
        label = layout.labelForField(self.end_date)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Event Type', self.type_select)
        label = layout.labelForField(self.type_select)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Location', self.location_select)
        label = layout.labelForField(self.location_select)
        label.setFont(qtg.QFont('Baskerville', 16))
        layout.addRow('Event Description', self.event_desc)
        label = layout.labelForField(self.event_desc)
        label.setFont(qtg.QFont('Baskerville', 16))


        button_box = qtw.QHBoxLayout()
        button_box.addWidget(self.cancel_btn)
        button_box.addWidget(self.submit_btn)
        layout.addRow(button_box)

        layout.setLabelAlignment(qtc.Qt.AlignLeft)

        self.setLayout(layout)

        if editingEvent:
            self._event = editingEvent
            self.setWindowTitle(self._event['event_name'])
            self.parseExistingEvent()
        else:
            self._event = {}
            self.setWindowTitle('Create a new event')
        #self.setVisible(True)
    

    def parseExistingEvent(self):
        self._id = self._event['event_id']
        self.name.setText(self._event['event_name'])
        if self._event['start']:
            self.start_date.setText(str(self._event['start']))
        if self._event['end']:
            self.end_date.setText(str(self._event['end']))
        self.type_select.setCurrentText(self._event['event_type'])
        print(self._event['location'])
        self.location_select.setCurrentText(self._event['location'])

    
    # def closeEvent(self, event):
    #     self.closed.emit()
    #     super(CharacterCreator, self).closeEvent(event)
    
    @qtc.pyqtSlot(str)
    def on_loc_change(self, text):
        if text == 'New...':
            text, ok = qtw.QInputDialog.getText(self, 'Define new location', 'Enter name:')
            if ok:
                self.location_select.addItem(text)
                EventCreator.LOC_ITEMS.insert(len(EventCreator.LOC_ITEMS)-2, text)
                self.location_select.setCurrentText(text)
            else:
                self.location_select.setCurrentIndex(0)
    
    @qtc.pyqtSlot(str)
    def on_type_change(self, text):
        if text == 'Other...':
            text, ok = qtw.QInputDialog.getText(self, 'Define other type', 'Enter type:')
            if ok:
                self.type_select.addItem(text)
                self.TYPE_ITEMS.insert(len(EventCreator.TYPE_ITEMS)-2, text)
                self.type_select.setCurrentText(text)
            else:
                self.type_select.setCurrentIndex(0)


    def onSubmit(self):
        self._event['event_name'] = self.name.text()
        start, start_state = self.start_date.getDate()
        if start_state:
            self._event['start'] = start
        else:
            self._event['start'] = Time()
        end, state = self.end_date.getDate()
        if state:
            self._event['end'] = end
        elif start_state:
            self._event['end'] = start
        else:
            self._event['end'] = Time()
        selectedType = str(self.type_select.currentText())
        if selectedType == 'Select Type':
            selectedType = ''
        self._event['event_type'] = selectedType
        selectedLoc = str(self.location_select.currentText())
        if selectedLoc == 'Select Location':
            selectedLoc = ''
        self._event['location'] = selectedLoc
        self._event['event_description'] = self.event_desc.toPlainText()
        self.close()
        self.submitted.emit(self._event)
        
    
    def keyPressEvent(self, event):
        if event.key() == qtc.Qt.Key_Escape:
            self.close()
        super(EventCreator, self).keyPressEvent(event)

