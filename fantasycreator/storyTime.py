
# PyQt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg

# Built-in Modules
import re
from threading import Lock


class TimeConstants():

    TIME_THREE_RNG = (1500, 2400)
    TIME_TWO_RNG = (1, 65)
    TIME_ONE_RNG = (1, 52)

    NAMED_ORDER = {'day': 'ONE', 'month': 'TWO', 'year': 'THREE'}
    NAMED_ORDER_INV = dict((val, key) for key, val in NAMED_ORDER.items()) # {'ONE': "year", 'TWO': "month", 'THREE':"day"}
    INDEXED_ORDER = dict(enumerate(NAMED_ORDER.keys())) # {0: year, 1: month ...}
    INDEXED_ORDER_INV = dict((val, key) for key, val in INDEXED_ORDER.items()) # {'year': 0', 'month': 2 ...}
    
    MIN_YEAR, MAX_YEAR = 0, 0
    MIN_MONTH, MAX_MONTH = 0, 0
    MIN_DAY, MAX_DAY = 0, 0

    ONE_FRMT = 2
    TWO_FRMT = 2
    THREE_FRMT = 4
    TIME_FRMT = r'(\d{1,%s} *[•,] *\d{1,%s} *[•,] *\d{1,%s})' % (ONE_FRMT, TWO_FRMT, THREE_FRMT)
    


    MAX_TIME_ONE = TIME_ONE_RNG[1]
    MAX_TIME_TWO = TIME_TWO_RNG[1]
    MAX_TIME_THREE = TIME_THREE_RNG[1]
    # MAX_TIME = [2400, 65, 52]
    MAX_TIME = None
    

    MIN_TIME_ONE = TIME_ONE_RNG[0]
    MIN_TIME_TWO = TIME_TWO_RNG[0]
    MIN_TIME_THREE = TIME_THREE_RNG[0]
    # MIN_TIME = [1500, 1, 1]
    MIN_TIME = None

    PREV_TIME_TRANSFORM = None

    mutex = Lock()

    def init(params):
        if time_ord := params.get('time_order', None):
            TimeConstants.NAMED_ORDER = time_ord
        if day_rng := params.get('day_range', None):
            TimeConstants.setDayRange(day_rng)
        if month_rng := params.get('month_range', None):
            TimeConstants.setMonthRange(month_rng)
        if year_rng := params.get('year_range', None):
            TimeConstants.setYearRange(year_rng)
        if day_frmt := params.get('day_format', None):
            TimeConstants.setDayFormat(day_frmt)
        if month_frmt := params.get('month_format', None):
            TimeConstants.setMonthFormat(month_frmt)
        if year_frmt := params.get('year_format', None):
            TimeConstants.setYearFormat(year_frmt)

        TimeConstants.updateConstants()
        
    def updateConstants():
        TimeConstants.mutex.acquire()
        TimeConstants.NAMED_ORDER_INV = dict((val, key) for key, val in TimeConstants.NAMED_ORDER.items()) # {'ONE': "year", 'TWO': "month", 'THREE':"day"}
        ordered_names = [TimeConstants.NAMED_ORDER_INV['ONE'], TimeConstants.NAMED_ORDER_INV['TWO'], TimeConstants.NAMED_ORDER_INV['THREE']]
        TimeConstants.INDEXED_ORDER = {0: ordered_names[0], 1: ordered_names[1], 2: ordered_names[2]} # {0: year, 1: month ...}
        TimeConstants.INDEXED_ORDER_INV = dict((val, key) for key, val in TimeConstants.INDEXED_ORDER.items()) # {'year': 0', 'month': 2 ...}

        TimeConstants.MAX_TIME_ONE = TimeConstants.TIME_ONE_RNG[1]
        TimeConstants.MAX_TIME_TWO = TimeConstants.TIME_TWO_RNG[1]
        TimeConstants.MAX_TIME_THREE = TimeConstants.TIME_THREE_RNG[1]

        TimeConstants.MIN_TIME_ONE = TimeConstants.TIME_ONE_RNG[0]
        TimeConstants.MIN_TIME_TWO = TimeConstants.TIME_TWO_RNG[0]
        TimeConstants.MIN_TIME_THREE = TimeConstants.TIME_THREE_RNG[0]

        TimeConstants.MAX_TIME = Time(TimeConstants.MAX_TIME_ONE, TimeConstants.MAX_TIME_TWO, 
                                                TimeConstants.MAX_TIME_THREE)
        TimeConstants.MIN_TIME = Time(TimeConstants.MIN_TIME_ONE, TimeConstants.MIN_TIME_TWO, 
                                                TimeConstants.MIN_TIME_THREE)
        TimeConstants.MIN_DAY = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['day']))[0]
        TimeConstants.MAX_DAY = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['day']))[1]       
        TimeConstants.MIN_MONTH = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['month']))[0]
        TimeConstants.MAX_MONTH = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['month']))[1]
        TimeConstants.MIN_YEAR = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['year']))[0]
        TimeConstants.MAX_YEAR = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['year']))[1]
        TIME_FRMT = r'(\d{1,%s} *[•,] *\d{1,%s} *[•,] *\d{1,%s})' % (TimeConstants.ONE_FRMT, 
                                                        TimeConstants.TWO_FRMT, 
                                                        TimeConstants.THREE_FRMT)
        TimeConstants.mutex.release()

    def setOrder(order_dict):
        TimeConstants.mutex.acquire()
        TimeConstants.PREV_TIME_TRANSFORM = dict(TimeConstants.INDEXED_ORDER)
        tmp_year_FRMT = getattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['year']))
        tmp_month_FRMT = getattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['month']))
        tmp_day_FRMT = getattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['day']))
        setattr(TimeConstants, "{}_FRMT".format(order_dict['year']), tmp_year_FRMT)
        setattr(TimeConstants, "{}_FRMT".format(order_dict['month']), tmp_month_FRMT)
        setattr(TimeConstants, "{}_FRMT".format(order_dict['day']), tmp_day_FRMT)

        tmp_year_RNG = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['year']))
        tmp_month_RNG = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['month']))
        tmp_day_RNG = getattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['day']))
        setattr(TimeConstants, "TIME_{}_RNG".format(order_dict['year']), tmp_year_RNG)
        setattr(TimeConstants, "TIME_{}_RNG".format(order_dict['month']), tmp_month_RNG)
        setattr(TimeConstants, "TIME_{}_RNG".format(order_dict['day']), tmp_day_RNG)
        TimeConstants.NAMED_ORDER = order_dict
        TimeConstants.mutex.release()

    def setYearFormat(frmt_len):
        setattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['year']), frmt_len)
    
    def setMonthFormat(frmt_len):
        setattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['month']), frmt_len)
    
    def setDayFormat(frmt_len):
        setattr(TimeConstants, "{}_FRMT".format(TimeConstants.NAMED_ORDER['day']), frmt_len)
    
    def setYearRange(rng_tuple):
        setattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['year']), rng_tuple)

    def setMonthRange(rng_tuple):
        setattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['month']), rng_tuple)
    
    def setDayRange(rng_tuple):
        setattr(TimeConstants, "TIME_{}_RNG".format(TimeConstants.NAMED_ORDER['day']), rng_tuple)



class Time():

    def __init__(self, slot1=TimeConstants.MIN_TIME_ONE, 
                        slot2=TimeConstants.MIN_TIME_TWO, 
                        slot3=TimeConstants.MIN_TIME_THREE,
                        day=None, month=None, year=None):

        if all(x is not None for x in (day, month, year)):
            tmp = [locals()[TimeConstants.NAMED_ORDER_INV['ONE']],
                locals()[TimeConstants.NAMED_ORDER_INV['TWO']],
                locals()[TimeConstants.NAMED_ORDER_INV['THREE']]]

        elif isinstance(slot1, str):
            if re.match(TimeConstants.TIME_FRMT, slot1):
                tmp = [int(x) for x in re.findall(r'\d+', slot1)]
            else: 
                tmp = []

        elif isinstance(slot1, list):
            tmp = slot1
        
        else:
            tmp = [slot1, slot2, slot3]
        

        ## TODO: FIX THIS
        try:
            self.time_1 = int(tmp[0])
        except:
            self.time_1 = TimeConstants.MIN_TIME_ONE
        try:
            self.time_2 = int(tmp[1])
        except:
            self.time_2 = TimeConstants.MIN_TIME_TWO
        try:
            self.time_3 = int(tmp[2])
        except:
            self.time_3 = TimeConstants.MIN_TIME_THREE
            
        

    def reOrder(self):
        self.tmp_1 = int(self.time_1)
        self.tmp_2 = int(self.time_2)
        self.tmp_3 = int(self.time_3)
        # setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[0]]+1), 
        #             getattr(self, 'tmp_{}'.format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.PREV_TIME_TRANSFORM[0]]+1)))
        # setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[1]]+1), 
        #             getattr(self, 'tmp_{}'.format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.PREV_TIME_TRANSFORM[1]]+1)))
        # setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[2]]+1), 
        #             getattr(self, 'tmp_{}'.format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.PREV_TIME_TRANSFORM[2]]+1)))

        setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.PREV_TIME_TRANSFORM[0]]+1), 
                    getattr(self, 'tmp_{}'.format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[0]]+1)))
        setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.PREV_TIME_TRANSFORM[1]]+1), 
                    getattr(self, 'tmp_{}'.format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[1]]+1)))
        setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.PREV_TIME_TRANSFORM[2]]+1), 
                    getattr(self, 'tmp_{}'.format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[2]]+1)))

        del self.tmp_1, self.tmp_2, self.tmp_3
    
    def getYear(self):
        return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1))
    
    def getMonth(self):
        return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1))
    
    def getDay(self):
        return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1))


    def setYear(self, year):
        # self.year = year
        setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1), year)
        
    def setMonth(self, month):
        # self.month = month
        setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1), month)
    
    def setDay(self, day):
        # self.day = day
        setattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1), day)



    def addYears(self, years):
        self.setYear(getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)) + years)

    def addMonths(self, months):
        self.setMonth(getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)) + months)
        
    def addDays(self, days):
        self.setDay(getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)) + days)

    def validateTime(self, update=False):
        if self.time_1 < TimeConstants.TIME_ONE_RNG[0] or self.time_1 > TimeConstants.TIME_ONE_RNG[1]:
            # print(f'Failure: time 1 was {self.time_1}')
            if update:
                self.time_1 = TimeConstants.MIN_TIME_ONE
            else:
                return False
        if self.time_2 < TimeConstants.TIME_TWO_RNG[0] or self.time_2 > TimeConstants.TIME_TWO_RNG[1]:
            # print(f'Failure: time 2 was {self.time_2}')
            if update:
                self.time_2 = TimeConstants.MIN_TIME_TWO
            else:
                return False
        if self.time_3 < TimeConstants.TIME_THREE_RNG[0] or self.time_3 > TimeConstants.TIME_THREE_RNG[1]:
            # print(f'Failure: time 3 was {self.time_3}')
            if update:
                self.time_3 = TimeConstants.MIN_TIME_THREE
            else:
                return False
        return True
    
    def validateYear(self, year):
        year = getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1))
        return year > TimeConstants.MIN_YEAR and year < TimeConstants.MAX_YEAR
    
    def validateMonth(self, month):
        month = getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1))
        return month > TimeConstants.MIN_MONTH and month < TimeConstants.MAX_MONTH
    
    def validateDay(self, day):
        day = getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1))
        return day > TimeConstants.MIN_DAY and day < TimeConstants.MAX_DAY


    ## Operator overloads

    def __sub__(self, other):
        if not isinstance(other, Time):
            raise ValueError("Invalid operation. Can only combine Time objects")
        yr_index = TimeConstants.INDEXED_ORDER_INV['year']+1
        mnth_index = TimeConstants.INDEXED_ORDER_INV['month']+1
        day_index = TimeConstants.INDEXED_ORDER_INV['day']+1
        if getattr(other, "time_{}".format(yr_index)) > getattr(self, "time_{}".format(yr_index)):
            return
        year = getattr(self, "time_{}".format(yr_index)) - getattr(other, "time_{}".format(yr_index))
        
        month = getattr(self, "time_{}".format(mnth_index)) - getattr(other, "time_{}".format(mnth_index))
        if month < 0:
            year -= 1
            month += TimeConstants.MAX_MONTH

        day = getattr(self, "time_{}".format(day_index)) - getattr(other, "time_{}".format(day_index))
        if day < 0:
            month -= 1
            day += TimeConstants.MAX_DAY

        return Time([locals()[TimeConstants.NAMED_ORDER_INV['ONE']],
                locals()[TimeConstants.NAMED_ORDER_INV['TWO']],
                locals()[TimeConstants.NAMED_ORDER_INV['THREE']]])


    def __add__(self, other):
        if not isinstance(other, Time):
            raise ValueError("Invalid operation. Can only combine Time objects")
        carry = 0
        yr_index = TimeConstants.INDEXED_ORDER_INV['year']+1
        mnth_index = TimeConstants.INDEXED_ORDER_INV['month']+1
        day_index = TimeConstants.INDEXED_ORDER_INV['day']+1
        day = getattr(self, "time_{}".format(day_index)) + getattr(other, "time_{}".format(day_index))
        if day > TimeConstants.MAX_DAY:
            carry = 1
            day -= TimeConstants.MAX_DAY
        month = getattr(self, "time_{}".format(mnth_index)) + getattr(other, "time_{}".format(mnth_index)) + carry
        if month > TimeConstants.MAX_MONTH:
            carry = 1
            month -= TimeConstants.MAX_MONTH
        else:
            carry = 0
        year = getattr(self, "time_{}".format(yr_index)) + getattr(other, "time_{}".format(yr_index)) + carry
        return Time([locals()[TimeConstants.NAMED_ORDER_INV['ONE']],
                locals()[TimeConstants.NAMED_ORDER_INV['TWO']],
                locals()[TimeConstants.NAMED_ORDER_INV['THREE']]])



    def __getitem__(self, key):
        if isinstance(key, int):
            return getattr(self, "time_{}".format(key+1))
        elif isinstance(key, str):
            return getattr(self, key)
        elif isinstance(key, slice):
            return Time([self.time_1, self.time_2, self.time_3][key])
        return ValueError("Invalid access type")

    def __eq__(self, other):
        return [self.time_1, self.time_2, self.time_3] == [other.time_1, other.time_2, other.time_3]
    
    def __neq__(self, other):
        return [self.time_1, self.time_2, self.time_3] != [other.time_1, other.time_2, other.time_3]

    def __gt__(self, other):
        if getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)) != getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)):
            return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)) > getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1))
        if getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)) != getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)):
            return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)) > getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1))
        if getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)) != getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)):
            return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)) > getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1))
        return False
    
    def __lt__(self, other):
        if getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)) != getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)):
            return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1)) < getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['year']+1))
        if getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)) != getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)):
            return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1)) < getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['month']+1))
        if getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)) != getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)):
            return getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1)) < getattr(other, "time_{}".format(TimeConstants.INDEXED_ORDER_INV['day']+1))
        return False
    
    def encode(self):
        return "({0}, {1}, {2})".format(self.time_1, self.time_2, self.time_3)

    def __str__(self):
        return "{0} • {1} • {2}".format(str(self.time_1).zfill(TimeConstants.ONE_FRMT), 
                                        str(self.time_2).zfill(TimeConstants.TWO_FRMT), 
                                        str(self.time_3).zfill(TimeConstants.THREE_FRMT))
        #     getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[0]]+1)),
        #     getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[1]]+1)),
        #     getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[2]]+1))
        # )
    
    def __repr__(self):
        return [self.time_1, self.time_2, self.time_3]
        #     getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[0]]+1)),
        #     getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[1]]+1)),
        #     getattr(self, "time_{}".format(TimeConstants.INDEXED_ORDER_INV[TimeConstants.INDEXED_ORDER[2]]+1))
        # ]

    def __hash__(self):
        return hash((self.time_1, self.time_2, self.time_3))
    


class DateLineEdit(qtw.QLineEdit):
    def __init__(self, parent=None):
        super(DateLineEdit, self).__init__(parent)
        # self.setFont(qtg.QFont('Baskerville', 18))
        self.setPlaceholderText(str(TimeConstants.MIN_TIME))
        # self.mask1 = 'd' * len(Materializer.TIME_ONE_FRMT) 
        # self.mask2 = 'd' * len(Materializer.TIME_TWO_FRMT)
        # self.mask3 = 'd' * len(Materializer.TIME_THREE_FRMT)
        # self.mask = f'{self.mask1} • {self.mask2} • {self.mask3}'
        self.validator = DateValidator()
        self.setValidator(self.validator)
    
    def getDate(self):
        text = self.text()
        state = self.validator.validate(text, 0)[0] == qtg.QValidator.Acceptable
        text = [int(x.strip()) for x in text.split('•') if x.strip()]
        res_time = Time(text)
        if not res_time.validateTime():
            res_time = TimeConstants.MIN_TIME
        return res_time, state
    
    # def focusInEvent(self, event):
    #     self.setInputMask(self.mask)
    
    # def focusOutEvent(self, event):
    #     self.setInputMask('')

# create custom validator class for date input
class DateValidator(qtg.QValidator):
    def validate(self, string, index):
        segments = [x.strip() for x in string.split('•')]
        if segments[-1] == '':
            segments.pop()
        res_string = ''
        if len(segments) < 1:
            return qtg.QValidator.Intermediate, string, index
        
        deleting = string[-1] == '•'

        if len(segments) > 3:
            return qtg.QValidator.Invalid, string, index
        
        if len(segments) >= 1:
            if not segments[0].isnumeric() or len(segments[0]) > TimeConstants.ONE_FRMT:
                state = qtg.QValidator.Invalid
            else:
                res_string += segments[0]
                if len(segments[0]) == TimeConstants.ONE_FRMT:
                    if deleting and len(segments) == 1:
                        res_string = res_string[:-1]
                    else:
                        res_string += ' • '
                state = qtg.QValidator.Intermediate
    
        if len(segments) >= 2:
            if not segments[1].isnumeric() or len(segments[1]) > TimeConstants.TWO_FRMT:
                state = qtg.QValidator.Invalid
            else:
                res_string += segments[1]
                if len(segments[1]) == TimeConstants.TWO_FRMT:
                    if deleting:
                        res_string = res_string[:-1]
                    else:
                        res_string += ' • '
                state = qtg.QValidator.Intermediate
            
        if len(segments) == 3:
            if not segments[2].isnumeric() or len(segments[2]) > TimeConstants.THREE_FRMT:
                state = qtg.QValidator.Invalid
            else:
                res_string += segments[2]
                # if len(segments[0]) == len(Materializer.TIME_ONE_FRMT):
                state = qtg.QValidator.Acceptable
                # else:
                #     state = qtg.QValidator.Intermediate
        
        return state, res_string, len(res_string)