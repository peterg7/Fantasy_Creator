''' Main window of the application. Serves as a governor

Creates instances of the database, welcome window, and all of the tabs. 
Connects all of the signals between tabs and popup windows. Handles
global saving & opening of files. 

Copyright (c) 2020 Peter C Gish

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__contact__ = "peter.gish11@gmail.com"
__copyright__ = "Copyright 2020"
__date__ = "Summer 2020"
__license__ = "MIT"
__maintainer__ = "Peter C Gish"
__status__ = "Development"
__version__ = "1.0.1"


# Required for packaging
COMPANY_NAME = "PeterGish"
APPLICATION_NAME = "Fantasy Creator"

## Necessary imports
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

# Built-in Modules
import os
import sys
import json
from fractions import Fraction
import math
import datetime
import uuid
import logging
import logging.config

# 3rd party
import numpy as np
from tinydb import where

# User-defined Modules
from fantasycreator.Mechanics.storyTime import TimeConstants, Time
from fantasycreator.Mechanics.materializer import Materializer
from fantasycreator.Tree.treeTab import TreeTab
from fantasycreator.Tree.character import Character
from fantasycreator.Tree.family import Family
from fantasycreator.Timeline.timelineTab import TimelineTab
from fantasycreator.Map.mapBuilderTab import MapBuilderTab
from fantasycreator.Scroll.scrollTab import ScrollTab
from fantasycreator.Data.database import VolatileDB
from fantasycreator.Data.characterLookup import LookUpTableModel, LookUpTableView
from fantasycreator.Dialogs.aboutWindow import AboutWindow
from fantasycreator.Dialogs.bugReporter import BugReporter
from fantasycreator.Dialogs.welcomeWindow import WelcomeWindow
from fantasycreator.Dialogs.preferencesWindow import PreferencesWindow
from fantasycreator.Mechanics.separableTabs import DetachableTabWidget
from fantasycreator.Mechanics.flags import LAUNCH_MODE

# External resources
from fantasycreator.resources import resources

# create main window class
class MainWindow(qtw.QMainWindow):

    # Necessary for Big Sur
    os.environ['QT_MAC_WANTS_LAYER'] = '1'

    # Define constants
    SCREEN_WIDTH = 1400
    SCREEN_HEIGHT = 1000
    BORDER_HEIGHT = 100

    # Set in SETTINGS
    TABLE_FEATURES = ['Name', 'Sex', 'Race', 'Birth Date', 'Death Date', 
                'Ruler', 'Kingdom', 'Family Name']
    
    TMP_FILENAME = 'temp.json'

    global_save = qtc.pyqtSignal()
    pref_update = qtc.pyqtSignal()
    update_table = qtc.pyqtSignal()
    pref_change = qtc.pyqtSignal()
    time_change = qtc.pyqtSignal(bool)
    loading_progress = qtc.pyqtSignal()

    database = None
    meta_db = None
    character_db = None
    families_db = None
    kingdoms_db = None

    MasterTrees = {}

    def __init__(self, args):
        '''MainWindow constructor'''
        super().__init__()
 
        # Initialize logging
        logging.config.fileConfig('./logs/logging.conf')
        logger = logging.getLogger() # instance of root logger

        self.verbose = args['verbose']
        if self.verbose:
            logger.info('Permanently in verbose mode currently!')
        else:
            logger.info('Apologies, application can only run verbosely')

        # self.launch_mode = LAUNCH_MODE.USER_SELECT
        ## TODO: REMOVE THIS SIMPLY FOR DEV
        self.launch_mode = LAUNCH_MODE.NEW_STORY
        self.filename = args['open']
        if self.filename:
            if qtc.QFileInfo(self.filename):
                self.launch_mode = LAUNCH_MODE.OPEN_EXISTING
                logger.info(f'Opening {self.filename}')
            else:
                logger.error(f'Could not open {self.filename}')

        if mode := args['mode']:
            if mode == 'new':
                self.launch_mode = LAUNCH_MODE.NEW_STORY
                logger.info(f'Launching application with a new story')
            elif mode.startsWith('sample'):
                self.launch_mode = LAUNCH_MODE.SAMPLE
                logger.info(f'Launch sample story')
            else:
                logger.error(f'Unrecognized option for application mode')


        # Setup + layout
        # self.resize(qtc.QSize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.layout = qtw.QHBoxLayout()

        self.setWindowIcon(qtg.QIcon(':/window-icons/main_window_icon.png'))

        # Check if running as executable
        if getattr(sys, 'frozen', False):
            self.resources_path = sys._MEIPASS
        else:
            self.resources_path = os.getcwd() + '/resources/'
        self.sample_path = os.path.join(self.resources_path, 'samples/sample_1.json')
        

        # Center the application
        self.move(qtw.QApplication.desktop().screen().rect().center() - self.frameGeometry().center())

        # Handle potential command line arguments
        if self.launch_mode == LAUNCH_MODE.OPEN_EXISTING:
            self.setup(LAUNCH_MODE.OPEN_EXISTING, self.filename)
        elif self.launch_mode == LAUNCH_MODE.USER_SELECT:
            # Welcome Window
            self.welcomeWindow = WelcomeWindow(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self)
            self.loading_progress.connect(self.welcomeWindow.incrementProgressBar)
            self.welcomeWindow.show()
            self.welcomeWindow.open_existing.connect(lambda x: self.setup(LAUNCH_MODE.OPEN_EXISTING, x))
            self.welcomeWindow.new_book.connect(lambda: self.setup(LAUNCH_MODE.NEW_STORY))
            self.welcomeWindow.open_sample.connect(lambda: self.setup(LAUNCH_MODE.SAMPLE))

        else:
            self.setup(self.launch_mode)

        self.requireSaveAs = True

    def moduleLoaded(self):
        self.loading_progress.emit()


    def setup(self, mode, arg=None):
        # Necessary constants for init of tabs
        TimeConstants.updateConstants()
        Materializer.updateConstants()

        # Declare tabs
        self.tabs = DetachableTabWidget(self)
        self.moduleLoaded()
        self.treetab = TreeTab(self)
        self.treetab.tree_loaded.connect(self.moduleLoaded)
        self.moduleLoaded()
        self.timetab = TimelineTab(self)
        self.timetab.timeline_loaded.connect(self.moduleLoaded)
        self.moduleLoaded()
        self.maptab = MapBuilderTab(self)
        self.maptab.map_loaded.connect(self.moduleLoaded)
        self.moduleLoaded()
        self.scrolltab = ScrollTab(self)
        self.scrolltab.scroll_loaded.connect(self.moduleLoaded)
        self.moduleLoaded()
        
        tree_icon = qtg.QIcon(':/tabbar-icons/tree_icon.png')
        timeline_icon = qtg.QIcon(':/tabbar-icons/timeline_icon.png')
        map_icon = qtg.QIcon(':/tabbar-icons/map_icon.png')
        scroll_icon = qtg.QIcon(':/tabbar-icons/scroll_icon.png')

        self.tabs.addTab(self.treetab, tree_icon, 'Family Tree')
        self.tabs.addTab(self.timetab, timeline_icon, 'Timeline')
        self.tabs.addTab(self.maptab, map_icon, 'Map Builder')
        self.tabs.addTab(self.scrolltab, scroll_icon, 'Character Scroll')

        self.tabs.setIconSize(qtc.QSize(25, 25))
        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self.handleTabChange)

        # Sync table across tabs 1 & 2
        self.table_model = LookUpTableModel(self)
        self.treetab.tableview.setModel(self.table_model)
        self.timetab.tableview.setModel(self.table_model)

        ##----------- Establish signals/connections --------------##
        # SAVE REQUESTS
        self.global_save.connect(self.treetab.saveRequest)
        self.global_save.connect(self.timetab.saveRequest)
        self.global_save.connect(self.maptab.saveRequest)
        self.global_save.connect(self.scrolltab.saveRequest)

        # PREFERENCE UPDATES
        self.pref_update.connect(self.treetab.preferenceUpdate)
        self.pref_update.connect(self.timetab.preferenceUpdate)
        self.pref_update.connect(self.maptab.preferenceUpdate)
        self.pref_update.connect(self.scrolltab.preferenceUpdate)
        self.time_change.connect(self.table_model.preferenceUpdate)
        self.time_change.connect(self.timetab.timelineview.handleTimeChange)

        self.table_model.cell_changed.connect(self.treetab.treeview.tree.receiveCharacterUpdate)
        self.table_model.visible_change.connect(self.timetab.timelineview.toggleCharViz)

        # TREE ORIGINATING SIGNALS
        self.treetab.tableview.char_selected.connect(self.treetab.treeview.addCharacterView)
        self.treetab.treeview.tree.addedChars.connect(self.table_model.insertNewChars)
        self.treetab.treeview.tree.removedChars.connect(self.table_model.removeChars)
        self.treetab.treeview.tree.updatedChars.connect(self.table_model.updateChars)
        self.treetab.treeview.tempStatusbarMsg.connect(self.statusBar().showMessage)
        
        self.treetab.treeview.tree.addedChars.connect(self.timetab.timelineview.addChars)
        self.treetab.treeview.tree.removedChars.connect(self.timetab.timelineview.removeChars)
        self.treetab.treeview.tree.updatedChars.connect(self.timetab.timelineview.updateChars)

        self.treetab.treeview.tree.addedChars.connect(self.scrolltab.scroll_widget.addChars)
        self.treetab.treeview.tree.removedChars.connect(self.scrolltab.scroll_widget.removeChars)
        self.treetab.treeview.tree.updatedChars.connect(self.scrolltab.scroll_widget.updateChars)

        self.treetab.treeview.tree.updatedChars.connect(self.maptab.mapview.updateChars)

        # TIMELINE ORIGINATING SIGNALS
        self.timetab.timelineview.updatedChars.connect(self.table_model.updateChars)
        self.timetab.timelineview.updatedChars.connect(self.scrolltab.scroll_widget.updateChars)
        self.timetab.timelineview.updatedChars.connect(self.treetab.treeview.tree.updateChars)
        self.timetab.timelineview.updatedChars.connect(self.maptab.mapview.updateChars)

        # MAP ORIGINATING SIGNALS
        self.maptab.mapview.updatedChars.connect(self.table_model.updateChars)
        self.maptab.mapview.updatedChars.connect(self.scrolltab.scroll_widget.updateChars)
        self.maptab.mapview.updatedChars.connect(self.treetab.treeview.tree.updateChars)
        self.maptab.mapview.updatedChars.connect(self.timetab.timelineview.updateChars)

        # SCROLL ORIGINATING SIGNALS
        self.scrolltab.status_message.connect(self.statusBar().showMessage)

        # Create MenuBar
        self.menu_bar = self.menuBar()

        file_menu = self.menu_bar.addMenu('File')
        edit_menu = self.menu_bar.addMenu('Edit')
        view_menu = self.menu_bar.addMenu('View')
        help_menu = self.menu_bar.addMenu('Help')

        #open_action = file_menu.addAction('Open')
        save_action = file_menu.addAction('Save')
        save_as_action = file_menu.addAction('Save As')

        undo_action = edit_menu.addAction('Undo')
        redo_action = edit_menu.addAction('Redo')

        help_action = help_menu.addAction(qtw.QAction(
            'Help',
            self,
            triggered=lambda: self.statusBar().showMessage('Sorry, no help yet!', 5000)
        ))

        bug_action = help_menu.addAction(qtw.QAction(
            'Report Bug',
            self,
            triggered=self.reportBug
        ))

        self.preferences_act = help_menu.addAction('Preferences')
        self.preferences_act.triggered.connect(self.launchPreferences)

        self.about_act = help_menu.addAction('About')
        self.about_act.triggered.connect(self.launchAboutWindow)

        #open_action.triggered.connect(self.openFile)
        #open_action.setShortcut(qtg.QKeySequence.Open)
        save_action.triggered.connect(self.saveFile)
        save_action.setShortcut(qtg.QKeySequence.Save)
        save_as_action.triggered.connect(self.saveAsFile)
        save_as_action.setShortcut(qtg.QKeySequence.SaveAs)

        undo_action.setShortcut(qtg.QKeySequence.Undo)

        redo_action.setShortcut(qtg.QKeySequence.Redo)

        max_size = qtw.QApplication.desktop().screenGeometry()
        self.setFixedSize(max_size.width(), max_size.height())
        self.adjusted_scroll = False

        # EXECUTE
        if mode == LAUNCH_MODE.OPEN_EXISTING:
            if arg:
                self.openFile(arg)
                self.initUI()
            else:
                self.cleanBoot()
        elif mode == LAUNCH_MODE.SAMPLE:
            self.buildSample()
            self.initUI()
        else:
            self.cleanBoot()

    def initUI(self):
        self.show()
        self.setWindowState(qtc.Qt.WindowMaximized)
        self.setMaximumSize(self.size())
   
    def cleanBoot(self):
        self.database = VolatileDB(self.sample_path)
        self.database.filename = MainWindow.TMP_FILENAME
        self.database.drop_table('meta')
        self.database.drop_table('characters')
        self.database.drop_table('families')
        self.database.drop_table('kingdoms')
        self.database.drop_table('events')
        self.database.drop_table('locations')
        self.database.drop_table('timestamps')

        self.preferences_db = self.database.table('preferences')
        self.character_db = self.database.table('characters')
        self.timestamps_db = self.database.table('timestamps')

        self.initTime()
        self.initMaterializer()
        self.initDatabase()
        null_id = uuid.uuid4()
        self.meta_db = self.database.table('meta')
        self.meta_db.insert(
            {'NULL_ID': null_id}
        )
        self.families_db = self.database.table('families')
        self.families_db.insert({'fam_id': null_id, 'fam_name': 'None'})
        self.kingdoms_db = self.database.table('kingdoms')
        self.kingdoms_db.insert({'kingdom_id': null_id, 'kingdom_name': 'None'})
        self.initUI()
    
    def initDatabase(self):
        self.table_model.set_columns(self.TABLE_FEATURES)
        self.table_model.connect_db(self.database)
        self.scrolltab.build_scroll(self.database)
        self.timetab.build_timeline(self.database)
        self.maptab.build_map(self.database)
        self.treetab.build_tree(self.database)
    

    def initTime(self):
        if time_record := self.preferences_db.get(where('tab') == 'mechanics'):
            TimeConstants.init(
                params = {
                    'time_order': time_record['time_order'],
                    'day_range': time_record['day_range'],
                    'month_range': time_record['month_range'],
                    'year_range': time_record['year_range'],
                    'day_format': time_record['day_format'],
                    'month_format': time_record['month_format'],
                    'year_format': time_record['year_format']
                }
            )
            
    def initMaterializer(self):
        materializer_params = {}
        if timeline_record := self.preferences_db.get(where('tab') == 'timeline'):
            materializer_params['timeline_padding'] = timeline_record['timeline_padding']
            materializer_params['timeline_scene_bounds'] = timeline_record['timeline_scene_bounds']
            materializer_params['timeline_axis_padding'] = timeline_record['timeline_axis_padding']
        if map_record := self.preferences_db.get(where('tab') == 'map'):
            materializer_params['map_scene_bounds'] = map_record['map_scene_bounds']
        Materializer.build(params=materializer_params)



    @qtc.pyqtSlot()
    @qtc.pyqtSlot(str)
    def buildSample(self, sample_name=None):
        if sample_name is None:
            sample_name = self.sample_path

        try:
            self.database = VolatileDB(sample_name)
            self.database.filename = MainWindow.TMP_FILENAME
        except Exception as e:
            qtw.QMessageBox.critical(self, 'Error', f'Could not load sample: {str(e)}')
            print(f'Could not load file: {e}')
            return
        
        # Create tables
        self.meta_db = self.database.table('meta')
        self.preferences_db = self.database.table('preferences')
        self.character_db = self.database.table('characters')
        self.families_db = self.database.table('families')
        self.kingdoms_db = self.database.table('kingdoms')
        locations_db = self.database.table('locations')
        self.timestamps_db = self.database.table('timestamps')

        meta_data = self.meta_db.all()
        if meta_data:
            self.title = meta_data[0].get('book_title', 'Untitled')
        else:
            self.title = 'Untitled'
        self.setWindowTitle(self.title)

        for char in self.character_db:
            if img_path := char['picture_path']:
                img = qtg.QImage(img_path, "PNG")
                self.character_db.update({'__IMG__': img}, where('char_id') == char['char_id'])
        for loc in locations_db:
            if img_path := loc['picture_path']:
                img = qtg.QImage(img_path, "PNG")
                locations_db.update({'__IMG__': img}, where('location_id') == loc['location_id'])

        self.initTime()
        self.initMaterializer()
        self.initControlPanel()
        self.initDatabase()


        
    @qtc.pyqtSlot()
    @qtc.pyqtSlot(str)
    def openFile(self, filename=None):
        if not filename:
            filename, _ = qtw.QFileDialog.getOpenFileName(
                self,
                "Select a file to open...",
                qtc.QDir.currentPath(), # static method returning user's home path
                'JSON Files (*.json) ;;Text Files (*.txt) ;;All Files (*)',
                'JSON Files (*.json)'
            )

        if filename:
            try:
                # Establish DB connection
                self.database = VolatileDB(filename)
                if filename == self.sample_path:
                    self.database.filename = MainWindow.TMP_FILENAME
                else:
                    self.requireSaveAs = False
                
                # Create tables
                self.meta_db = self.database.table('meta')
                self.preferences_db = self.database.table('preferences')
                self.character_db = self.database.table('characters')
                self.families_db = self.database.table('families')
                self.kingdoms_db = self.database.table('kingdoms')

                self.title = self.meta_db.all()
                if self.title:
                    self.title = self.title[0]['book_title']
                else:
                    self.title = 'Untitled'
                self.setWindowTitle(self.title)

                if self.isVisible():   # Clear tree if it already exists
                    # app = qtw.QApplication.instance()
                    args = sys.argv[:]
                    print(args)
                    if 'open' in args:
                        args[args.index('open')+1] = filename
                    else:
                        args.extend(['open', filename])
                    qtc.QCoreApplication.quit()
                    status = qtc.QProcess.startDetached(sys.executable, args)
                    print(status)
                    exit()
                    return


            except Exception as e:
                qtw.QMessageBox.critical(self, 'Error', f'Could not load file: {str(e)}')
                print(f'Could not load file: {e}')
            
            self.initTime()
            self.initMaterializer()
            self.initControlPanel()
            self.initDatabase()

           
    @qtc.pyqtSlot()
    def saveAsFile(self):
        self.global_save.emit()
        filename, _ = qtw.QFileDialog.getSaveFileName(
            self,
            "Select the file to save to...",
            qtc.QDir.currentPath(),
            'JSON Files (*.json)'
            # qtw.QFileDialog.DontUseNativeDialog | # force use of Qt-style box
            # qtw.QFileDialog.DontResolveSymlinks
        )
        if filename:
            try:
                self.database.dump(filename=filename)

            except Exception as e:
                qtw.QMessageBox.critical(self, 'Error', f'Could not load file: {str(e)}')
                print(f'Could not load file: {e}')
            self.statusBar().showMessage('File saved.', 4000)
            self.requireSaveAs = False
    
    @qtc.pyqtSlot()
    def saveFile(self):
        if self.requireSaveAs:
            self.saveAsFile()
        else:
            try:
                self.database.dump()

            except Exception as e:
                print(f"Could not save file: {str(e)}")
                self.statusBar().showMessage('An error occured. Could not save file.', 4000)
            self.statusBar().showMessage('File saved.', 4000)
                

    def initControlPanel(self):
        # Update families
        if self.meta_db.contains(where('NULL_ID').exists()):
            NULL_ID = self.meta_db.all()[0]['NULL_ID']
        family_select = self.treetab.control_panel.family_select
        family_select.blockSignals(True)
        if family_select.count() > 0:
            for i in range(family_select.count()):
                family_select.removeItem(i)
        
        model = family_select.model()
        index = 0
        for fam in self.families_db:
            if fam['fam_id'] != NULL_ID:
                family_select.addItem(fam['fam_name'])
                item = family_select.model().item(index)
                item.setCheckable(True)
                model.setData(model.index(index, 0),
                                qtc.Qt.Checked,
                                qtc.Qt.CheckStateRole)
                index += 1
        family_select.blockSignals(False)

        # Update kingdoms
        kingdom_select = self.treetab.control_panel.kingdom_select
        kingdom_select.blockSignals(True)
        if kingdom_select.count() > 0:
            for i in range(kingdom_select.count()):
                kingdom_select.removeItem(i)
        model = kingdom_select.model()
        index = 0
        for kingdom in self.kingdoms_db:
            if kingdom['kingdom_id'] == NULL_ID:
                continue
            kingdom_select.addItem(kingdom['kingdom_name'])
            item = kingdom_select.model().item(index)
            item.setCheckable(True)
            model.setData(model.index(index, 0),
                            qtc.Qt.Checked,
                            qtc.Qt.CheckStateRole)
            index += 1
        kingdom_select.blockSignals(False)
        

    def handleTabChange(self, index):
        
        if index == 0: # Tree widget
            # self.control_panel.setVisible(True)
            # self.control_panel.show()
            self.treetab.treeview.fitWithBorder()
        elif index == 1: # Timeline widget
            # NOTE: Need to change control panel
            # self.control_panel.setVisible(False)
            # self.control_panel.hide()
            # self.timetab.update()
            self.timetab.timelineview.fitWithBorder()
        elif index == 2: # Map Builder
            # self.control_panel.setVisible(False)
            # self.control_panel.hide()
            # self.maptab.adjustSize()
            # self.maptab.resizeEvent(qtg.QResizeEvent(self.size(), qtc.QSize()))
            self.maptab.mapview.fitWithBorder()
        if index == 3: # Character scroll
            # self.control_panel.setVisible(False)
            # self.control_panel.hide()
            self.scrolltab.update()
            if not self.adjusted_scroll:
                self.scrolltab.scroll_widget.fitWithBorder()
                self.adjusted_scroll = True
        else:
            pass

        
    
    def handlePreferenceChange(self, pref_list):
        master_prefs = []
        time_chng = False
        time_reorder = False
        for tab in pref_list:
            if tab['tab'] == 'general':
                general_prefs = {'tab': 'general'}
                if title := tab.get('book_title', None):
                    self.title = title
                    self.setWindowTitle(self.title)
                    general_prefs['book_title'] = title
                if world := tab.get('world_name', None):
                    # self.world = world
                    general_prefs['world_name'] = world
                master_prefs.append(general_prefs)

            elif tab['tab'] == 'mechanics':
                mech_prefs = {'tab': 'mechanics'}
                if time_ord := tab.get('time_order', None):
                    if time_ord != TimeConstants.NAMED_ORDER:
                        time_chng = True
                        time_reorder = True
                        TimeConstants.setOrder(time_ord)
                        # TimeConstants.NAMED_ORDER = time_ord
                        mech_prefs['time_order'] = time_ord
                if year_rng := tab.get('year_range', None):
                    if year_rng != getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['year'])):
                        if year_rng[0] <= year_rng[1]:
                            time_chng = True
                            TimeConstants.setYearRange(year_rng)
                        mech_prefs['year_range'] = year_rng
                if month_rng := tab.get('month_range', None):
                    if month_rng != getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['month'])):
                        if month_rng[0] <= month_rng[1]:
                            time_chng = True
                            TimeConstants.setMonthRange(month_rng)
                        mech_prefs['month_range'] = month_rng
                if day_rng := tab.get('day_range', None):
                    if day_rng != getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['day'])):
                        if day_rng[0] <= day_rng[1]:
                            time_chng = True
                            TimeConstants.setDayRange(day_rng)
                        mech_prefs['day_range'] = day_rng
                if year_frmt := tab.get('year_format', None):
                    if year_frmt != getattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['year'])):
                        time_chng = True
                        TimeConstants.setYearFormat(year_frmt)
                        mech_prefs['year_format'] = year_frmt
                if month_frmt := tab.get('month_format', None):
                    if month_frmt != getattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['month'])):
                        time_chng = True
                        TimeConstants.setMonthFormat(month_frmt)
                        mech_prefs['month_format'] = month_frmt
                if day_frmt := tab.get('day_format', None):
                    if day_frmt != getattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['day'])):
                        time_chng = True
                        TimeConstants.setDayFormat(day_frmt)
                        mech_prefs['day_format'] = day_frmt
                if time_chng:
                    master_prefs.append(mech_prefs)

            elif tab['tab'] == 'tree':
                tree_prefs = {'tab': 'tree'}
                if gen_space := tab.get('generation_spacing', None):
                    tree_prefs['generation_spacing'] = gen_space
                if sib_space := tab.get('sibling_spacing', None):
                    tree_prefs['sibling_spacing'] = sib_space
                if desc_drop := tab.get('desc_dropdown', None):
                    tree_prefs['desc_dropdown'] = desc_drop
                if part_space := tab.get('partner_spacing', None):
                    tree_prefs['partner_spacing'] = part_space
                if expand_fact := tab.get('expand_factor', None):
                    tree_prefs['expand_factor'] = expand_fact
                if offset_fact := tab.get('offset_factor', None):
                    tree_prefs['offset_factor'] = offset_fact
                if crown_size := tab.get('ruler_crown_size', None):
                    tree_prefs['ruler_crown_size'] = crown_size
                if char_width := tab.get('char_img_width', None):
                    tree_prefs['char_img_width'] = char_width
                if char_height := tab.get('char_img_height', None):
                    tree_prefs['char_img_height'] = char_height
                master_prefs.append(tree_prefs)

            elif tab['tab'] == 'timeline':
                timeline_adj = False
                # if min_year := tab.get('min_year', None):
                #     if min_year !=Timeline
                # if max_year := tab.get('max_year', None):

            elif tab['tab'] == 'map':
                map_adj = False
            elif tab['tab'] == 'scroll':
                scroll_adj = False

        if time_chng:
            TimeConstants.updateConstants()
            Materializer.updateConstants()
            # Update database
            if record := self.preferences_db.get(where('tab') == 'timeline'):
                for val in record['time_periods'].values():
                    if time_reorder:
                        val[0].reOrder()
                        val[1].reOrder()
                    val[0].validateTime(True)
                    val[1].validateTime(True)
            
            for record in self.character_db:
                for val in record.values():
                    if type(val) == Time:
                        if time_reorder:
                            val.reOrder()
                        val.validateTime(True)

            for record in self.timestamps_db:
                for val in record.values():
                    if type(val) == Time:
                        if time_reorder:
                            val.reOrder()
                        val.validateTime(True)

            self.time_change.emit(time_reorder)
            # self.preferences_db.update()
        
        for tab in master_prefs:
            self.preferences_db.update(tab, where('tab') == tab['tab'])
        self.pref_update.emit()


    def launchPreferences(self):
        self.pref_window = PreferencesWindow(self.database)
        self.pref_window.pref_change.connect(self.handlePreferenceChange)
        self.pref_window.show()
    
    def reportBug(self):
        self.bug_reporter = BugReporter(self)
        self.bug_reporter.show()

    def launchAboutWindow(self):
        self.about_window = AboutWindow(self)
        self.about_window.show()

    def clean_up(self):
        if self.database:
            self.database.close()


# Non-bundled execution
# if __name__ == '__main__':
#     parser = qtc.QCommandLineParser()
    
#     # qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling)
#     app = qtw.QApplication(sys.argv)
#     app.setApplicationName('Fantasy Creator')
#     app.setApplicationVersion('1.1')
    
#     # set up command line argument parser
#     parser.setApplicationDescription('GUI to create fantastical stories!')
#     parser.addHelpOption()
#     parser.addVersionOption()

#     # define arguments
#     # parser.addPositionalArgument("open", qtc.QCoreApplication.translate("MainWindow", "An existing .story file to open."))
#     existing = qtc.QCommandLineOption(["o", "open"], qtc.QCoreApplication.translate("MainWindow", "Open an existing .story <file>"), 
#                 qtc.QCoreApplication.translate("MainWindow", "file"))
#     parser.addOption(existing)

#     verbose = qtc.QCommandLineOption("verbose", qtc.QCoreApplication.translate("MainWindow", "Run in verbose mode."))
#     parser.addOption(verbose)

#     dev_mode = qtc.QCommandLineOption(["m", "mode"], 
#                 qtc.QCoreApplication.translate("MainWindow", "Skip welcome window and use provided launch <option>.\n - 'new' launch a new instance. \n - 'sample(x)' launch sample x."),
#                 qtc.QCoreApplication.translate("MainWindow", "option"))
#     parser.addOption(dev_mode)
    
#     parser.process(app)
    
#     args = {
#         'open': parser.value(existing),
#         'mode': parser.value(dev_mode),
#         'verbose': parser.isSet(verbose)
#     }

#     #app.setStyle(qtw.QStyleFactory.create('Fusion'))
#     mw = MainWindow(args)
#     app.aboutToQuit.connect(mw.clean_up)
#     sys.exit(app.exec())