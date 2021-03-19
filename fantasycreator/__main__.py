
# PyQt 
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCommandLineParser, QCommandLineOption, QCoreApplication

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
    app.setApplicationName('Fantasy Creator')
    app.setApplicationVersion('1.1')

    # set up command line argument parser
    parser.setApplicationDescription('GUI to create fantastical stories!')
    parser.addHelpOption()
    parser.addVersionOption()

    # define arguments
    # parser.addPositionalArgument("open", qtc.QCoreApplication.translate("MainWindow", "An existing .story file to open."))
    existing = QCommandLineOption(["o", "open"], QCoreApplication.translate("MainWindow", "Open an existing .story <file>"), 
                QCoreApplication.translate("MainWindow", "file"))
    parser.addOption(existing)

    verbose = QCommandLineOption("verbose", QCoreApplication.translate("MainWindow", "Run in verbose mode."))
    parser.addOption(verbose)

    dev_mode = QCommandLineOption(["m", "mode"], 
                QCoreApplication.translate("MainWindow", "Skip welcome window and use provided launch <option>.\n - 'new' launch a new instance. \n - 'sample(x)' launch sample x."),
                QCoreApplication.translate("MainWindow", "option"))
    parser.addOption(dev_mode)
    
    parser.process(app)
    
    args = {
        'open': parser.value(existing),
        'mode': parser.value(dev_mode),
        'verbose': parser.isSet(verbose)
    }

    #app.setStyle(qtw.QStyleFactory.create('Fusion'))
    mw = MainWindow(args)
    app.aboutToQuit.connect(mw.clean_up)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()