''' Database module for storage of all pertenant application data

Creates a volatile database using the tinydb package that stores contents
in memory until being flushed to a file (on save) in JSON format. Holds 
methods for formatting objects into a standardized form. Also has encoder/decoder
for objects that can't be stored in a dictionary, such as images.

Copyright (c) 2020 Peter C Gish

See the MIT License (MIT) for more information. You should have received a copy
of the MIT License along with this program. If not, see 
<https://www.mit.edu/~amini/LICENSE.md>.
'''
__author__ = "Peter C Gish"
__date__ = "3/16/21"
__maintainer__ = "Peter C Gish"
__version__ = "1.0.1"


# PyQt
from PyQt5.QtCore import QPointF, QRectF, QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QImage
from PyQt5 import QtWidgets as qtw

# 3rd party
from tinydb import TinyDB, where
from tinydb.table import Table
from tinydb.storages import MemoryStorage

# Built-in Modules
import os
import re
import json
import uuid
import base64

# User-defined Modules
from fantasycreator.Mechanics.storyTime import Time

iteritems = getattr(dict, 'iteritems', dict.items)
itervalues = getattr(dict, 'itervalues', dict.values)


class VolatileDB(TinyDB):
    ''' Database class which extends TinyDB. Contains methods to load JSON
    files and dump the database contents to disk. Possess all methods/variables
    from TinyDB for maintaining the database
    '''

    def __init__(self, filename=None):
        ''' Constructor. Main purpose is to instantiate a tinydb instance

        Args:
            filename - optional string path of file to load into database
        '''
        super().__init__(storage=MemoryStorage)
        if filename:
            self.load(filename)

    def load(self, filename=None):
        ''' Load a file stored on disc into the database.

        Args:
            filename - string path of file to load
        '''
        if filename:
            self.filename = filename
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self._storage.write(json.load(f, cls=Decoder))

    def dump(self, filename=None):
        ''' Dump the database's contents to a file

        Args:
            filename - string path of output file
        '''
        if filename:
            self.filename = filename

        with open(self.filename, 'w') as f:
            json.dump(self._storage.read(), f, indent=4, cls=Encoder)
    

class DataFormatter():
    ''' Object to standardize the inputs into the database. Classes may create
    an instance of this and create formatted entries to then be input into the
    database.
    '''

    def char_entry(self, char_dict, fam_id=None, kingdom_id=None):
        ''' Formatter for a character entry. Provided with a character's
        dictionary, extract data (and fill in vacancies).

        Args:
            char_dict - required dictionary representation of a character
            fam_id - optional id of the family this character belongs to
            kingdom_id - optional id of the kingdom this character belongs to
        '''

        c_id = char_dict.get('char_id', uuid.uuid4())
        name = char_dict.get('name', '')
        if not fam_id:
            fam_id = char_dict.get('fam_id', None)
        parent_0 = char_dict.get('parent_0', None)
        parent_1 = char_dict.get('parent_1', None)
        relationship_list = char_dict.get('partnerships', [])
        sex = char_dict.get('sex', '')
        birth = char_dict.get('birth', None) or [0, 0, 0]
        if isinstance(birth, str):
            birth = list(map(int, re.findall('\d+', birth)))
        death = char_dict.get('death', None) or [0, 0, 0]
        if isinstance(death, str):
            death = list(map(int, re.findall('\d+', death)))
        ruler = char_dict.get('ruler', False)
        if isinstance(ruler, str):
            if ruler.lower() in ['yes', 'true']:
                ruler = True
            else:
                ruler = False
        picture_path = char_dict.get('picture_path', '')
        if picture := char_dict.get('__IMG__', None):
            if picture.isNull():
                picture = None
        if not kingdom_id:
            kingdom_id = char_dict.get('kingdom_id', None)
        race = char_dict.get('race', '')
        timeline_ord = char_dict.get('timeline_ord', 0)
        events = char_dict.get('events', [])
        graph_rect = char_dict.get('graphical_rect', None)
        notes = char_dict.get('notes')

        # prep new character entry
        return {
            'char_id': c_id,
            'name': name,
            'fam_id': fam_id,
            'parent_0': parent_0,
            'parent_1': parent_1,
            'partnerships': relationship_list,
            'sex': sex,
            'birth': birth,
            'death': death,
            'ruler': ruler,
            'picture_path': picture_path,
            '__IMG__': picture,
            'kingdom_id': kingdom_id,
            'race': race,
            'timeline_ord': timeline_ord,
            'graphical_rect': graph_rect,
            'events': events,
            'notes': notes }
    
    def partnership_entry(self, p_id, rom_id=None):
        ''' Formats a partnership entry by creating a romance id if not provided
        and returning a dictionary with the two ids.

        Args:
            p_id - id of one of the partners
            rom_id - optional id of the relationship (WARNING: assumes no id exists 
                        for this relationship if none provided)
        '''
        if not rom_id:
            rom_id = uuid.uuid4()
        return {
            'rom_id': rom_id,
            'p_id': p_id }

    def family_entry(self, fam_name, fam_type, fam_id=None):
        ''' Formats a family entry by creating a family id if not provided and
        returning a dictionary with the family information.

        Args:
            fam_name - required name of the family
            fam_type - required type of family (flag)
            fam_id - optional id of the family, one will be created if set to None
                    (WARNING: assumes no id exists for this family if none provided)
        '''
        if not fam_id:
            fam_id = uuid.uuid4()
        return {
            'fam_id': fam_id,
            'fam_name': fam_name,
            'fam_type':  fam_type }
    
    def kingdom_entry(self, kingdom_name, kingdom_id=None):
        ''' Formats a kingdom entry by creating a kingdom id if not provided and
        returning a dictionary with the kingdom information ready to be inserted
        into the database.

        Args:
            kingdom_name - required name of the kingdom
            kingdom_id - optional id of this kingdom (WARNING: assumes no id exists 
                            for this kingdom if none provided)
        '''
        if not kingdom_id:
            kingdom_id = uuid.uuid4()
        return {
            'kingdom_id': kingdom_id,
            'kingdom_name': kingdom_name }

    def globalLocationEntry(self, loc_dict, loc_id=None):
        ''' Formats a location entry. Creates a location id if none provided and
        returns a dictionary of all the location's information.

        Args:
            loc_dict - required dictionary representation of the location
            loc_id - optional id of this location (WARNING: assumes no id exists 
                        for this location if none provided)
        '''
        if not loc_id:
            loc_id = uuid.uuid4()
        graph_rect = loc_dict.get('graphical_rect', (0, 0, 0, 0))
        name = loc_dict.get('location_name', '')
        loc_type = loc_dict.get('location_type', '')
        loc_details = loc_dict.get('location_details', '')
        picture_path = loc_dict.get('picture_path', '')
        picture = loc_dict.get('__IMG__', None)

        return {
            'location_id': loc_id,
            'graphical_rect': graph_rect,
            'location_name': name,
            'location_type': loc_type,
            'location_details': loc_details,
            'picture_path': picture_path,
            '__IMG__': picture }
    
    def timestampEntry(self, graph_pt, timestamp, char_id, loc_id=None, new_loc=False):
        ''' Formats a timestamp entry to be inserted in the database. Returns
        a standardized dictionary for the timestamp.

        Args:
            graph_pt - required graphical point that is associated with this timestamp
            timestamp - required time object for this timestamp
            char_id - required id of the character involved in this timestamp
            loc_id - optional id for the location of this timestamp
            new_loc - optional boolean indicating if the location is new or not
        '''
        if not loc_id and new_loc:
            loc_id = uuid.uuid4()
        else:
            loc_id = None
        return {
            'graphical_point': graph_pt,
            'timestamp': timestamp,
            'char_id': char_id,
            'location_id': loc_id }
    
    def eventEntry(self, event_dict, new_loc=False):
        ''' Formats an event into a standardized dictionary to be inserted
        into the database. (WARNING: will create new event and location ids
        if no event_id is provided or new_loc is true)

        Args:
            event_dict - required dictionary representation of the event
            new_loc - optional boolean indicating if the location is new or not
        '''
        event_id = event_dict.get('event_id', None)
        if not event_id:
            event_id = uuid.uuid4()
        event_name = event_dict.get('event_name', None)
        location_id = event_dict.get('location_id', None)
        if not location_id and new_loc:
            location_id = uuid.uuid4()
        event_type = event_dict.get('event_type', None)
        start = event_dict.get('start', None) or Time()
        if isinstance(start, str):
            start = Time(start)
        end = event_dict.get('end', None) or Time()
        if isinstance(end, str):
            end = Time(end)
        event_desc = event_dict.get('event_description', None)

        return {
            'event_id': event_id,
            'event_name': event_name,
            'location_id': location_id,
            'event_type': event_type,
            'start': start,
            'end': end,
            'event_description': event_desc }


class Encoder(json.JSONEncoder):
    ''' Implementation of a JSON encoder using tinydb's API. Provides encodings
    for all non-python native object types.
    '''
    UUID_CLASS = 'UUID'
    POINT_CLASS = 'QPOINT'
    RECT_CLASS = 'QRECT'
    TIME_CLASS = "TIME"
    IMG_CLASS = "IMG"
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return f"__{self.UUID_CLASS}__:{obj.hex}"
        if isinstance(obj, QPointF):
            return f"__{self.POINT_CLASS}__:{(obj.x(), obj.y())}"
        if isinstance(obj, Time):
            return f"__{self.TIME_CLASS}__:{obj.encode()}"
        if isinstance(obj, QRectF):
            return f"__{self.RECT_CLASS}__:{(obj.x(), obj.y(), obj.width(), obj.height())}"
        if isinstance(obj, QImage):
            return encodeImage(obj)
        return super().default(obj)


class Decoder(json.JSONDecoder):
    ''' Implementation of a JSON decoder using tinydb's API. Decodes the objects
    stored by the Encoder object.
    '''
    OBJ_CLASS = 'UUID'
    POINT_CLASS = 'QPOINT'
    RECT_CLASS = 'QRECT'
    TIME_CLASS = "TIME"
    IMG_CLASS = "IMG"
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.hook, *args, **kwargs)
        self.uuid_tag = '__{0}__:'.format(self.OBJ_CLASS)
        self.point_tag = '__{0}__:'.format(self.POINT_CLASS)
        self.time_tag = '__{0}__:'.format(self.TIME_CLASS)
        self.img_tag = '__{0}__'.format(self.IMG_CLASS)
        self.rect_tag = '__{0}__:'.format(self.RECT_CLASS)

    def hook(self, obj):
        for key, value in enumerate_element(obj):
            try:
                if value.startswith(self.uuid_tag):
                    encoded = value[len(self.uuid_tag):]
                    obj[key] = uuid.UUID(encoded)
                elif value.startswith(self.point_tag):
                    encoded = value[len(self.point_tag):]
                    pair = [float(x) for x in encoded[1:-1].split(',')]
                    obj[key] = QPointF(pair[0], pair[1])
                elif value.startswith(self.time_tag):
                    encoded = value[len(self.time_tag):]
                    obj[key] = Time(encoded[1:-1])
                elif value.startswith(self.rect_tag):
                    encoded = value[len(self.rect_tag):]
                    dimensions = [float(x) for x in encoded[1:-1].split(',')]
                    obj[key] = QRectF(*dimensions)
                elif key == self.img_tag: #value.startswith(self.img_tag):
                    if value:
                        obj[key] = decodeImage(value)
                    else:
                        obj[key] = None
            except AttributeError:
                if isinstance(value, (dict, list)):
                    self.hook(value)
        return obj


def enumerate_element(element):
    ''' Helper method for Decoder.hook() that returns an iterable list of
    a JSON block.

    Args:
        element - the JSON object to be enumerated
    '''
    if isinstance(element, dict):
        return iteritems(element)
    else:
        return enumerate(element)


def encodeImage(pix):
    ''' Helper method to encode an image into a string representation of a bytes 
    object which can be stored in a JSON file.

    Args:
        pix - pixmap object of the image to be saved
    '''
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    pix.save(buffer, "PNG")
    try: 
        encoded = bytes(data.toBase64()).decode('utf-8')
        return str(encoded)
    except Exception as e:
        print(str(e))
        return ''

def decodeImage(val):
    ''' Sibling method to encodeImage which decodes a stored image and
    creates a image object.

    Args:
        val - byte string from file representing an image
    '''
    encoded = bytes(val, 'utf-8')
    img = QImage()
    if not img.loadFromData(QByteArray.fromBase64(encoded), "PNG"):
        img = None
    return img

