

# PyQt 
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# User-defined modules
from fantasycreator.Mechanics.flags import EVENT_TYPE


class PictureLineEdit(qtw.QLineEdit):

    clicked = qtc.pyqtSignal(bool)

    def __init__(self, parent=None):
        super(PictureLineEdit, self).__init__(parent)
    
    def mousePressEvent(self, event):
        self.clicked.emit(True)


class PictureEditor(qtw.QDialog):

    CHAR_IMAGE_HEIGHT = 180
    CHAR_IMAGE_WIDTH = 180
    LOC_IMAGE_WIDTH = 260
    LOC_IMAGE_HEIGHT = 200

    submitted = qtc.pyqtSignal(str, qtg.QPixmap)

    class ImageDisplay(qtw.QGraphicsView):
        def __init__(self, pix, min_zoom, max_zoom, zoom_init, increment=1, img_mode=EVENT_TYPE.CHAR, parent=None):
            super(PictureEditor.ImageDisplay, self).__init__(parent)
            self.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
            self.setDragMode(qtw.QGraphicsView.ScrollHandDrag)
            rect = qtc.QRectF(pix.rect())
            self.scene = qtw.QGraphicsScene(self)
            self.scene.setSceneRect(rect)
            graphic_pix = self.scene.addPixmap(pix)
            self.setScene(self.scene)

            self.setSizePolicy(
                qtw.QSizePolicy.Fixed,
                qtw.QSizePolicy.Fixed)
            if img_mode == EVENT_TYPE.CHAR:
                self.setFixedSize(qtc.QSize(
                    PictureEditor.CHAR_IMAGE_WIDTH + 2,
                    PictureEditor.CHAR_IMAGE_HEIGHT + 2))
                self.fitInView(graphic_pix, qtc.Qt.KeepAspectRatioByExpanding)

            elif img_mode == EVENT_TYPE.LOC:
                self.setFixedSize(qtc.QSize(
                    PictureEditor.LOC_IMAGE_WIDTH + 2,
                    PictureEditor.LOC_IMAGE_HEIGHT + 2))
                # self.fitInView(graphic_pix, qtc.Qt.KeepAspectRatioByExpanding)

            # self.viewport().setSizePolicy(
            #     qtw.QSizePolicy.Fixed,
            #     qtw.QSizePolicy.Fixed)
            # self.viewport().setFixedSize(qtc.QSize(
            #     PictureEditor.IMAGE_WIDTH,
            #     PictureEditor.IMAGE_HEIGHT))


            self.centerOn(rect.center())

            self.max_zoom = max_zoom
            self.min_zoom = min_zoom
            self.increment = increment
            self.current_zoom = zoom_init

        
        def scaleImg(self, factor):
            center_pos = self.viewport().rect().center()
            zoomInFactor = 1.1
            zoomOutFactor = 1 / zoomInFactor
            self.setTransformationAnchor(qtw.QGraphicsView.NoAnchor)
            self.setResizeAnchor(qtw.QGraphicsView.NoAnchor)

            if factor > self.current_zoom:
                zoomFactor = zoomInFactor
                self.current_zoom += self.increment
            else:
                zoomFactor = zoomOutFactor
                self.current_zoom -= self.increment

            oldPos = self.mapToScene(center_pos)
            self.scale(zoomFactor, zoomFactor)
            newPos = self.mapToScene(center_pos)
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())


    def __init__(self, filename, img_mode=EVENT_TYPE.CHAR, parent=None):
        super(PictureEditor, self).__init__(parent)
        self.setWindowTitle("Adjust Image")

        if filename:
            self.filename = filename
            # self.current_pix = qtg.QPixmap(self.filename)
            self.current_pix = self.importPicture(self.filename, img_mode)
        else:
            self.close()

        layout = qtw.QVBoxLayout()
        
        self.img_view = PictureEditor.ImageDisplay(self.current_pix, 4, 20, 12, img_mode=img_mode, parent=self)
        layout.addWidget(self.img_view)

        self.scale_slider = qtw.QSlider()
        self.scale_slider.setSizePolicy(
            qtw.QSizePolicy.Minimum,
            qtw.QSizePolicy.Preferred)
        self.scale_slider.setOrientation(qtc.Qt.Horizontal)
        self.scale_slider.setMinimum(4)
        self.scale_slider.setMaximum(20)
        self.scale_slider.setTickInterval(1)
        self.scale_slider.setTickPosition(qtw.QSlider.TicksBelow)

        self.current_scale = 12
        self.scale_slider.setValue(self.current_scale)
        self.scale_slider.valueChanged.connect(self.img_view.scaleImg)
        layout.addWidget(self.scale_slider)

        button_layout = qtw.QHBoxLayout()
        self.cancel_btn = qtw.QPushButton(
            'Cancel',
            clicked=self.close
        )
        button_layout.addWidget(self.cancel_btn)
        self.submit_btn = qtw.QPushButton(
            'Accept',
            clicked=self.submit
        )
        button_layout.addWidget(self.submit_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    
    def importPicture(self, filename, img_mode):
        img = qtg.QImage(filename)
        # img.convertToColorSpace(qtg.QColorSpace(qtg.QColorSpace.SRgb)) # Not avaliable on 5.13
        if img_mode == EVENT_TYPE.CHAR:
            img = img.scaled(PictureEditor.CHAR_IMAGE_WIDTH, PictureEditor.CHAR_IMAGE_HEIGHT,
                                qtc.Qt.KeepAspectRatioByExpanding, qtc.Qt.SmoothTransformation)
        elif img_mode == EVENT_TYPE.LOC:
            img = img.scaled(PictureEditor.LOC_IMAGE_WIDTH, PictureEditor.LOC_IMAGE_HEIGHT,
                                qtc.Qt.KeepAspectRatioByExpanding)
        return qtg.QPixmap.fromImage(img)


    def submit(self):
        rect = self.img_view.viewport().rect()
        final_pix = qtg.QPixmap(rect.size())
        final_pix.fill(qtg.QColor(qtc.Qt.transparent))
        painter = qtg.QPainter(final_pix)
        painter.setRenderHint(qtg.QPainter.SmoothPixmapTransform)
        painter.setRenderHint(qtg.QPainter.Antialiasing)
        self.img_view.render(painter, qtc.QRectF(final_pix.rect()), rect)
        painter.end()
        self.submitted.emit(self.filename, final_pix)
        self.close()