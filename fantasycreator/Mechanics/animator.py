# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# Built-in Modules
import uuid

# 3rd party
import numpy as np
from tinydb import where
from sortedcontainers import SortedDict

# User-defined Modules
from Mechanics.flags import ANIMATION_MODE
from Mechanics.storyTime import Time

class Animator():

    TIMELINE = SortedDict()

    # def __init__(self):

    def buildTimeline(self, db):
        self.timestamps_db = db.table('timestamps')
        for stamp in self.timestamps_db:
            self.addTimestamp(stamp['char_id'], stamp['timestamp'], stamp['graphical_point'])

    def addTimestamp(self, char_id, time, point):
        if time and time.validateTime():
            if time.getYear() in Animator.TIMELINE:
                year = Animator.TIMELINE[time.getYear()]
                if time.getMonth() in year:
                    month = year[time.getMonth()]
                    if time.getDay() in month:
                        month[time.getDay()].append((char_id, point))
                    else:
                        month[time.getDay()] = [(char_id, point)]
                else:
                    year[time.getMonth()] = SortedDict({time.getDay(): [(char_id, point)]})
            else:
                Animator.TIMELINE[time.getYear()] = SortedDict({time.getMonth(): SortedDict({time.getDay(): [(char_id, point)]})})

    def deleteTimestamp(self, char_id, time):
        if record := self.getDayStamps(time.getDay(), time.getMonth(), time.getYear()):
            for index, stamp in enumerate(record):
                if stamp[0] == char_id:
                    del record[index]
                    del stamp
                    break
            if record == []:
                del Animator.TIMELINE[time.year]
    
    # def updateTimestamp(self, char_id, timestamp_dict):
    #     time = timestamp_dict.get('timestamp', None)
    #     if time in Animator.TIMELINE:
    #         Animator[TimeSlider]
    
    def getYearStamps(self, year):
        # return Animator.TIMELINE.get(year, None)
        if year_dict := Animator.TIMELINE.get(year, None):
            stamps = []
            for month_dict in year_dict.values():
                for day_list in month_dict.values():
                    stamps = [*stamps, *day_list]
                return stamps
        return None
    
    def getMonthStamps(self, month, year):
        if year_dict := Animator.TIMELINE.get(year, None):
            if month_dict := year_dict.get(month, None):
                stamps = []
                for day_list in month_dict.values():
                    stamps = [*stamps, *day_list]
                return stamps    
        return None
    
    def getDayStamps(self, day, month, year):
        if year_dict := Animator.TIMELINE.get(year, None):
            if month_dict := year_dict.get(month, None):
                return month_dict.get(day, None)
        return None
    

class AnimatorControlBar(qtw.QWidget):

    ANIMATION_BASE_SPEED = 45000
    ANIMATION_LOOP = False

    scene_change = qtc.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super(AnimatorControlBar, self).__init__(parent)
        self.animator = Animator()
        self.animation_speed = AnimatorControlBar.ANIMATION_BASE_SPEED
        self.active = False
        
        self.setMinimumSize(qtc.QSize(0, 84))
        self.setMaximumSize(qtc.QSize(16777215, 84))
        self.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
        self.setObjectName("animatorControl")

        self.gridLayout = qtw.QGridLayout(self)
        # self.gridLayout.setContentsMargins(15, 10, 15, 10)
        # self.gridLayout.setRowMinimumHeight(2, 10)
        # self.gridLayout.setRowStretch(2, 1)
        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(4, 2)
        self.gridLayout.setObjectName("gridLayout")

        self.animationSlider = TimeSlider(parent=self)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.animationSlider.setSizePolicy(sizePolicy)
        self.animationSlider.setOrientation(qtc.Qt.Horizontal)
        self.animationSlider.setObjectName("animationSlider")
        self.gridLayout.addWidget(self.animationSlider, 2, 0, 1, 5)
        
        self.starttimeLabel = qtw.QLabel(parent=self)
        self.starttimeLabel.setFont(qtg.QFont('Baskerville', 15))
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.starttimeLabel.setSizePolicy(sizePolicy)
        self.starttimeLabel.setObjectName("starttimeLabel")
        self.gridLayout.addWidget(self.starttimeLabel, 1, 0, 1, 1, qtc.Qt.AlignLeft)

        self.endtimeLabel = qtw.QLabel(parent=self)
        self.endtimeLabel.setFont(qtg.QFont('Baskerville', 15))
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.endtimeLabel.setSizePolicy(sizePolicy)
        self.endtimeLabel.setObjectName("endtimeLabel")
        self.gridLayout.addWidget(self.endtimeLabel, 1, 4, 1, 1, qtc.Qt.AlignRight)


        controls_layout = qtw.QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.speedLabel = qtw.QLabel('Speed')
        self.speedLabel.setFont(qtg.QFont('Baskerville', 14))
        self.speedLabel.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Minimum
        )

        self.speedSlider = SpeedSlider(parent=self)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.speedSlider.setSizePolicy(sizePolicy)
        self.speedSlider.setOrientation(qtc.Qt.Horizontal)
        self.speedSlider.setObjectName("speedSlider")
        
        self.rewindButton = qtw.QPushButton()
        self.rewindButton.setStyleSheet(""" 
                    QPushButton {
                        border-color: rgb(150, 150, 150);
                        border-width: 2px;        
                        border-style: outset;
                        border-radius: 13px;
                        /*padding: 5px;*/
                        color: rgb(150, 150, 150);
                        background-color: rgba(185, 185, 185, 50);
                    }
                    QPushButton:pressed { 
                        border-style: inset;
                        background-color: rgba(185, 185, 185, 75);
                    }
        """)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(True)
        self.rewindButton.setSizePolicy(sizePolicy)
        self.rewindButton.setMinimumSize(qtc.QSize(26, 26))
        self.rewindButton.setMaximumSize(qtc.QSize(26, 26))
        self.rewindButton.setText("")
        icon32 = qtg.QIcon()
        icon32.addPixmap(qtg.QPixmap(":/map-icons/rewind.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.rewindButton.setIcon(icon32)
        self.rewindButton.setIconSize(qtc.QSize(12, 12))
        self.rewindButton.setObjectName("rewindButton")

        self.fastforwardButton = qtw.QPushButton()
        self.fastforwardButton.setStyleSheet(""" 
                    QPushButton {
                        border-color: rgb(150, 150, 150);
                        border-width: 2px;        
                        border-style: outset;
                        border-radius: 13px;
                        /*padding: 5px;*/
                        color: rgb(150, 150, 150);
                        background-color: rgba(185, 185, 185, 50);
                    }
                    QPushButton:pressed { 
                        border-style: inset;
                        background-color: rgba(185, 185, 185, 75);
                    }
        """)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(True)
        self.fastforwardButton.setSizePolicy(sizePolicy)
        self.fastforwardButton.setMinimumSize(qtc.QSize(26, 26))
        self.fastforwardButton.setMaximumSize(qtc.QSize(26, 26))
        self.fastforwardButton.setText("")
        icon33 = qtg.QIcon()
        icon33.addPixmap(qtg.QPixmap(":/map-icons/fastforward.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.fastforwardButton.setIcon(icon33)
        self.fastforwardButton.setIconSize(qtc.QSize(12, 12))
        self.fastforwardButton.setObjectName("fastforwardButton")

        self.playpauseButton = qtw.QPushButton()
        self.playpauseButton.setStyleSheet(""" 
                    QPushButton {
                        border-color: rgb(150, 150, 150);
                        border-width: 2px;        
                        border-style: outset;
                        border-radius: 23px;
                        /*padding: 5px;*/
                        color: rgb(150, 150, 150);
                        /*background-color: black;*/
                        background-color: rgba(185, 185, 185, 75);
                    }
                    QPushButton:pressed { 
                        border-style: inset;
                        /*background-color: rgba(185, 185, 185, 75);*/
                    }
        """)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(True)
        self.playpauseButton.setSizePolicy(sizePolicy)
        self.playpauseButton.setMinimumSize(qtc.QSize(46, 46))
        self.playpauseButton.setMaximumSize(qtc.QSize(46, 46))
        self.playpauseButton.setText("")
        self.playIcon = qtg.QIcon()
        self.playIcon.addPixmap(qtg.QPixmap(":/map-icons/play.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.pauseIcon = qtg.QIcon()
        self.pauseIcon.addPixmap(qtg.QPixmap(":/map-icons/pause.png"), qtg.QIcon.Normal, qtg.QIcon.Off)

        self.playpauseStateMachine = qtc.QStateMachine()
        self.play = qtc.QState()
        self.play.assignProperty(self.playpauseButton, "toolTip", "Play")
        self.play.assignProperty(self.playpauseButton, "icon", self.pauseIcon)
        self.play.setObjectName("play")
        self.pause = qtc.QState()
        self.pause.assignProperty(self.playpauseButton, "toolTip", "Pause")
        self.pause.assignProperty(self.playpauseButton, "icon", self.playIcon)
        self.pause.setObjectName("pause")
        self.play.addTransition(self.playpauseButton.clicked, self.pause)
        self.pause.addTransition(self.playpauseButton.clicked, self.play)

        self.playpauseStateMachine.addState(self.play)
        self.playpauseStateMachine.addState(self.pause)
        self.playpauseStateMachine.setInitialState(self.play)
        self.playpauseButton.setIconSize(qtc.QSize(42, 42))
        self.playpauseButton.setIcon(self.playIcon)
        self.playpauseButton.setObjectName("playpauseButton")

        self.repeatButton = qtw.QPushButton()
        self.repeatButton.setStyleSheet(""" 
                    QPushButton {
                        border-color: rgb(150, 150, 150);
                        border-width: 2px;        
                        border-style: outset;
                        border-radius: 4px;
                        /*padding: 5px;*/
                        color: rgb(150, 150, 150);
                        background-color: rgba(185, 185, 185, 50);
                    }
                    QPushButton:checked { 
                        border-style: inset;
                        background-color: rgba(185, 185, 185, 75);
                    }
        """)
        sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(True)
        self.repeatButton.setSizePolicy(sizePolicy)
        self.repeatButton.setMinimumSize(qtc.QSize(30, 18))
        self.repeatButton.setMaximumSize(qtc.QSize(30, 18))
        self.repeatButton.setText("")
        self.repeatButton.setCheckable(True)
        icon35 = qtg.QIcon()
        icon35.addPixmap(qtg.QPixmap(":/map-icons/repeat-icon.png"), qtg.QIcon.Normal, qtg.QIcon.Off)
        self.repeatButton.setIcon(icon35)
        self.repeatButton.setIconSize(qtc.QSize(14, 14))
        self.repeatButton.setToolTip("Loop")
        self.repeatButton.setObjectName("repeatButton")

        controls_layout.addWidget(self.speedLabel)
        controls_layout.addWidget(self.speedSlider, qtc.Qt.AlignCenter)
        controls_layout.addWidget(self.rewindButton, qtc.Qt.AlignCenter)
        controls_layout.addWidget(self.playpauseButton, qtc.Qt.AlignCenter)
        controls_layout.addWidget(self.fastforwardButton, qtc.Qt.AlignCenter)
        controls_layout.addWidget(self.repeatButton, qtc.Qt.AlignCenter)
        self.gridLayout.addLayout(controls_layout, 0, 1, 2, 3, qtc.Qt.AlignCenter)
        self.gridLayout.setContentsMargins(0, 0, 0, 6)

        self.setLayout(self.gridLayout)
        self.animation = qtc.QPropertyAnimation(self.animationSlider, b"sliderPosition")
    

    def initControls(self, min_year, max_year):
        self.setActive(False)
        self.starttimeLabel.setText(f'yr. {str(min_year)}')
        self.starttimeLabel.adjustSize()
        self.endtimeLabel.setText(f'yr. {str(max_year)}')
        self.endtimeLabel.adjustSize()

        self.animationSlider.setMinimum(min_year)
        self.animationSlider.setMaximum(max_year)
        self.rewindButton.pressed.connect(self.seekBeginning)
        self.fastforwardButton.pressed.connect(self.seekEnd)

        self.speedSlider.setMinimum(0)
        self.speedSlider.setMaximum(2)
        
        self.play.entered.connect(self.playAnimation)
        self.pause.entered.connect(self.pauseAnimation)
        self.play.addTransition(self.animation.finished, self.pause)
        self.play.addTransition(self.rewindButton.pressed, self.pause)
        
        self.animation.setDuration(self.animation_speed)
        self.animation.setStartValue(self.animationSlider.minimum())
        self.animation.setEndValue(self.animationSlider.maximum())

        self.animationSlider.sliderPressed.connect(self.handlePressed)
        self.animationSlider.sliderReleased.connect(self.updateTime)

        self.repeatButton.toggled.connect(self.setLoop)
        self.speedSlider.valueChanged.connect(self.updateSpeed)
        self.animationSlider.scene_change.connect(self.scene_change.emit)

        self.animationSlider.isActive = 1 # Bool value

        self.year_offset = min_year
        self.year_range = max_year - min_year
        self.value_to_time = self.animation_speed / self.year_range

    @qtc.pyqtSlot()
    def handlePressed(self):
        if self.animation.state() == qtc.QAbstractAnimation.Running:
            self.animation.pause()
            self.playpauseButton.setIcon(self.playIcon)
        elif self.animation.state() == qtc.QAbstractAnimation.Stopped:
            self.animation.start()
            self.animation.pause()
            self.playpauseButton.setIcon(self.playIcon)
        
    @qtc.pyqtSlot(int)
    def updateSpeed(self, speed):
        if speed == 0:
            self.animation_speed = AnimatorControlBar.ANIMATION_BASE_SPEED
        elif speed == 1:
            self.animation_speed = AnimatorControlBar.ANIMATION_BASE_SPEED / 1.5
        else:
            self.animation_speed = AnimatorControlBar.ANIMATION_BASE_SPEED / 2
        self.value_to_time = self.animation_speed / self.year_range

        self.animation.setDuration(self.animation_speed)
        self.updateTime()



    @qtc.pyqtSlot()
    def updateTime(self):
        time = self.value_to_time * (self.animationSlider.sliderPosition() - self.year_offset)
        self.animation.setCurrentTime(int(time))

    def playAnimation(self):
        if self.active:
            if self.animation.state() == qtc.QAbstractAnimation.Stopped:
                self.animation.start()
            elif self.animation.state() == qtc.QAbstractAnimation.Paused:
                self.animation.resume()
    
    def pauseAnimation(self):
        if self.animation.state() == qtc.QAbstractAnimation.Running:
            self.animation.pause()
    
    def seekEnd(self):
        self.animationSlider.setSliderPosition(self.animationSlider.maximum())
        self.animation.setCurrentTime(self.animation.totalDuration())

    def seekBeginning(self):
        self.animationSlider.setSliderPosition(self.animationSlider.minimum())
        self.animation.setCurrentTime(0)

    def setLoop(self, state):
        if state:
            self.animation.setLoopCount(-1)
        else:
            self.animation.setLoopCount(0)

    def setActive(self, state):
        if state:
            self.setEnabled(True)
            self.animation.start()
            self.playpauseStateMachine.start()
        else:
            self.setEnabled(False)
            self.animation.stop()
            self.playpauseStateMachine.stop()



class TimeSlider(qtw.QSlider):
    
    scene_change = qtc.pyqtSignal(int, int)

    YEAR_TIMEOUT = 100
    MONTH_TIMEOUT = 50

    def __init__(self, parent=None):
        super(TimeSlider, self).__init__(parent)

        self.stylesheet = """
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: white;
            height: 10px;
            border-radius: 4px;
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
                stop: 0 #66b8ee, stop: 1 #bbedff);
            background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                stop: 0 #bbedff, stop: 1 #55b5ff);
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        QSlider::add-page:horizontal {
            background: #fff;
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #eee, stop:1 #ccc);
            border: 1px solid #777;
            width: 13px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #fff, stop:1 #ddd);
            border: 1px solid #444;
            border-radius: 4px;
        }
        QSlider::sub-page:horizontal:disabled {
            background: #bbb;
            border-color: #999;
        }
        """
        self.setStyleSheet(self.stylesheet)
        self.setFont(qtg.QFont('Baskerville', 15))
        self.font_metrics = qtg.QFontMetrics(self.font())
        self.current_mode = ANIMATION_MODE.YEAR
        self.isActive = 0 # Bool value

    
    def sliderChange(self, change):
        super(TimeSlider, self).sliderChange(change)
        if change == qtw.QAbstractSlider.SliderValueChange and self.isActive:
            self.scene_change.emit(self.value(), self.current_mode)
            style_opts = qtw.QStyleOptionSlider()
            self.initStyleOption(style_opts)
            rect = self.style().subControlRect(qtw.QStyle.CC_Slider, style_opts, 
                                                    qtw.QStyle.SC_SliderHandle, self)
            bottomRightCorner = rect.bottomLeft()

            qtw.QToolTip.showText(self.mapToGlobal( qtc.QPoint( 
                                        bottomRightCorner.x(), bottomRightCorner.y() ) ),
                                         str(self.value()), self)



class SpeedSlider(qtw.QSlider):

    tick_values = {0: '1', 1: '1.5', 2: '2'}

    def __init__(self, parent=None):
        super(SpeedSlider, self).__init__(parent)
        self.tick_font = qtg.QFont('Baskerville', 14)
        self.font_metrics = qtg.QFontMetrics(self.tick_font)
        self.setFont(self.tick_font)
        self.setTickInterval(1)
        self.setTickPosition(qtw.QSlider.TicksBelow)

    # def paintEvent(self, event):
    #     super(SpeedSlider, self).paintEvent(event)
    #     rect = self.geometry()
    #     num_ticks = 3
    #     painter = qtg.QPainter(self)
    #     painter.setPen(qtg.QPen(qtc.Qt.black))

    #     font_height = self.font_metrics.height()

    #     for i in range(0, num_ticks):
    #         tick_num = self.minimum() + (1 * i)
    #         current_tick = SpeedSlider.tick_values[tick_num]
    #         tick_x = ((rect.width() / num_ticks) * i) - (self.font_metrics.width(current_tick)/2)
    #         tick_y = rect.height() - font_height

    #         painter.drawText(qtc.QPoint(tick_x, tick_y), current_tick)

    #     painter.drawRect(rect)
