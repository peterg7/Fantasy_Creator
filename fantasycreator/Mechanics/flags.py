
from enum import IntFlag, unique

# Enum for whether partners are included
@unique
class FAMILY_FLAGS(IntFlag):
    BASE = 0
    BLOOD_RELATIVES = 1
    INCLUDE_PARTNERS = 2
    DISPLAY_FAM_NAMES = 3
    CONNECT_PARTNERS = 4
    INCLUDE_UNKNOWNS = 5
    DISPLAY_RULERS = 6

@unique
class TREE_ICON_DISPLAY(IntFlag):
    BASE = 7
    IMAGE = 8
    NAME = 9

@unique
class GROUP_SELECTION_ITEM(IntFlag):
    BASE = 10
    FAMILY = 11
    KINGDOM = 12

@unique
class CHAR_TYPE(IntFlag):
    BASE = 13
    DESCENDANT = 14
    PARTNER = 15

@unique
class FAM_TYPE(IntFlag):
    BASE = 16
    SUBSET = 17
    SINGLETON = 18
    NULL_TERM = 19

@unique
class SELECTIONS_UPDATE(IntFlag):
    BASE = 20
    ADDED_FAM = 21
    REMOVED_FAM = 22
    CHANGED_FAM = 23
    ADDED_KINGDOM = 24
    REMOVED_KINGDOM = 25
    CHANGED_KINGDOM = 26

@unique
class ANIMATION_MODE(IntFlag):
    YEAR = 27
    MONTH = 28
    DAY = 29

@unique
class EVENT_TYPE(IntFlag):
    CHAR = 30
    EVENT = 31
    LOC = 32

@unique
class LAUNCH_MODE(IntFlag):
    USER_SELECT = 33
    OPEN_EXISTING = 34
    NEW_STORY = 35
    SAMPLE = 36

@unique
class DIRECTION(IntFlag):
    UP = 38
    DOWN = 39
    LEFT = 40
    RIGHT = 41

@unique
class RELATIONSHIP(IntFlag):
    DESCENDANT = 42
    SIBLING = 43
    PARTNER = 44
    PARENT = 45
    
@unique
class REL_TREE_POS(IntFlag):
    ''' Enum class to store the node's position relative to its parent (the
    "middle" being num_siblings/2).
    '''
    LEFT = 46
    RIGHT = 47
    MIDDLE = 48

    @classmethod
    def exists(cls, value):
        values = set(item.value for item in cls)
        return value in values