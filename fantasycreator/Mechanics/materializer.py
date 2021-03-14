
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

# 3rd Party
from tinydb import where
import numpy as np

# Built-in Modules
import uuid
from threading import Lock

# User-defined Modules
from Mechanics.storyTime import TimeConstants, Time


class Materializer():

    # Story Space
    TIMELINE_PADDING = 100

    # Graphic Space
    TIMELINE_COORDS_BOUNDS = (0, 0, 8500, 3000)
    TIMELINE_AXIS_PADDING = 25
    MAP_COORDS_BOUNDS = (0, 0, 10000, 10000)
    MAP_COORDS = {}

    TOTAL_TIME_PIXELS = 8500
    TOTAL_DAYS = 3042000

    DAY_TO_PIXEL = 0.002794214
    MONTH_TO_PIXEL = 0.145299128
    YEAR_TO_PIXEL = 9.44444332

    mutex = Lock()

    def build(params):
        time_pad = params.get('timeline_padding', None)
        if time_pad:
            Materializer.TIMELINE_PADDING = time_pad
        timeline_bnds = params.get('timeline_scene_bounds', None)
        if timeline_bnds:
            Materializer.TIMELINE_COORDS_BOUNDS = timeline_bnds
        timeline_axis_pad = params.get('timeline_axis_padding', None)
        if timeline_axis_pad:
            Materializer.TIMELINE_AXIS_PADDING = timeline_axis_pad
        map_bnds = params.get('map_scene_bounds', None)
        if map_bnds:
            Materializer.MAP_COORDS_BOUNDS = map_bnds
        
        Materializer.updateConstants()
    

    def updateConstants():
        Materializer.mutex.acquire()
        Materializer.TOTAL_DAYS = ((TimeConstants.MAX_DAY - TimeConstants.MIN_DAY) *  
                        (TimeConstants.MAX_MONTH - TimeConstants.MIN_MONTH) *  
                        (TimeConstants.MAX_YEAR - TimeConstants.MIN_YEAR))
        

        Materializer.TOTAL_TIME_PIXELS = (Materializer.TIMELINE_COORDS_BOUNDS[2] 
                                    - Materializer.TIMELINE_COORDS_BOUNDS[0])
        
        Materializer.DAY_TO_PIXEL = Materializer.TOTAL_TIME_PIXELS / Materializer.TOTAL_DAYS
        Materializer.MONTH_TO_PIXEL = Materializer.DAY_TO_PIXEL * (TimeConstants.MAX_DAY - TimeConstants.MIN_DAY)
        Materializer.YEAR_TO_PIXEL = (Materializer.MONTH_TO_PIXEL * 
                                    (TimeConstants.MAX_MONTH - TimeConstants.MIN_MONTH))
        Materializer.mutex.release()


    def mapTime(self, time):
        # if self.validateTime(year, month, day):
        return (time.getDay() * Materializer.DAY_TO_PIXEL + 
                        time.getMonth() * Materializer.MONTH_TO_PIXEL + 
                        (time.getYear() - TimeConstants.MIN_YEAR) * 
                        Materializer.YEAR_TO_PIXEL)
    
    def mapTimeRange(self, time1, time2):
        pt_1 = self.mapTime(time1)
        pt_2 = self.mapTime(time2)
        return abs(pt_1 - pt_2)

    def mapLocation(self, loc_dict, x, y):
        Materializer.MAP_COORDS[loc_dict['location_id']] = (x, y)


    def mapToTime(self, x):
        # if (x < Materializer.TIMELINE_COORDS_BOUNDS[0] 
        #         or x > Materializer.TIMELINE_COORDS_BOUNDS[2]):
        #     return
        year, remainder = divmod(x, Materializer.YEAR_TO_PIXEL)
        # if remainder:
        #     year += 1
        month, remainder = divmod(remainder, Materializer.MONTH_TO_PIXEL)
        # if remainder:
            # month += 1
        day = np.ceil(remainder / Materializer.DAY_TO_PIXEL)
        year, month, day = int(year), int(month), int(day)
        year += TimeConstants.MIN_YEAR
        return Time(year=year, month=month, day=day)
    


    # def getStoryDistance(self, loc1_id, loc2_id)

    def getGraphicDistance(self, loc1_id, loc2_id):
        try:
            x, y = np.subtract(Materializer.MAP_COORDS[loc2_id] 
                                - Materializer.MAP_COORDS[loc1_id])
        except:
            return
        return (x, y)


