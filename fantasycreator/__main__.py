
# PyQt 
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCommandLineParser, QCoreApplication

# Built-in Modules
import sys
import numpy
import tinydb

# User-defined Modules
from fantasycreator.mainWindow import MainWindow

# execute the code
def main():
    # if sys.platform.startswith('darwin'): 
    #     try:
    #         from Foundation import NSBundle # Method requires pyobj-c
    #         bundle = NSBundle.mainBundle()
    #         if bundle:
    #             # app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    #             app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    #             if app_info:
    #                 app_info['CFBundleName'] = "Fantasy Creator"
    #     except ImportError:
    #         pass
    # else:
    #     qtc.QCoreApplication.setApplicationName("Fantasy Creator")

    parser = QCommandLineParser()
    app = QApplication(sys.argv)
    # app.setApplicationName('Fantasy Creator')
    # app.setApplicationVersion('0.1')

    parser.setApplicationDescription('GUI to create fantastical stories!')
    parser.addPositionalArgument("open", QCoreApplication.translate("main", "A file to open."))
    
    parser.process(app)
    args = parser.positionalArguments()

    #app.setStyle(qtw.QStyleFactory.create('Fusion'))
    mw = MainWindow(args)
    app.aboutToQuit.connect(mw.clean_up)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()