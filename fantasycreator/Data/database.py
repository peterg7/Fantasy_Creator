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
from Mechanics.storyTime import Time

iteritems = getattr(dict, 'iteritems', dict.items)
itervalues = getattr(dict, 'itervalues', dict.values)


class VolatileDB(TinyDB):

    def __init__(self, filename=None):
        super().__init__(storage=MemoryStorage)
        if filename:
            self.load(filename)


    def load(self, filename=None):
        if filename:
            self.filename = filename
        if os.path.exists(filename):
            with open(self.filename, 'r') as f:
                self._storage.write(json.load(f, cls=UUIDDecoder))


    def dump(self, filename=None):
        if filename:
            self.filename = filename

        with open(self.filename, 'w') as f:
            json.dump(self._storage.read(), f, indent=4, cls=UUIDEncoder)
    

class DataFormatter():

    def char_entry(self, char_dict, fam_id=None, kingdom_id=None):

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
        if not rom_id:
            rom_id = uuid.uuid4()
        return {
            'rom_id': rom_id,
            'p_id': p_id }


    def family_entry(self, fam_name, fam_type, fam_id=None):
        if not fam_id:
            fam_id = uuid.uuid4()
        return {
            'fam_id': fam_id,
            'fam_name': fam_name,
            'fam_type':  fam_type }
    
    def kingdom_entry(self, kingdom_name, kingdom_id=None):
        if not kingdom_id:
            kingdom_id = uuid.uuid4()
        return {
            'kingdom_id': kingdom_id,
            'kingdom_name': kingdom_name }

    def globalLocationEntry(self, loc_dict, loc_id=None):
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


class UUIDEncoder(json.JSONEncoder):
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
            #return "__{}__:{}".format(self.IMG_CLASS, base64.encodebytes(obj).decode("utf-8"))
            # return "__{}__:{}".format(self.IMG_CLASS, EncodeImage(obj))
            return EncodeImage(obj)
        return super().default(obj)


class UUIDDecoder(json.JSONDecoder):
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
                    # obj[key] = QRectF(dimensions[0], dimensions[1], dimensions[2], dimensions[3])
                    obj[key] = QRectF(*dimensions)
                elif key == self.img_tag: #value.startswith(self.img_tag):
                    if value:
                        obj[key] = DecodeImage(value)
                    else:
                        obj[key] = None
            except AttributeError:
                if isinstance(value, (dict, list)):
                    self.hook(value)
        return obj


def enumerate_element(element):
    if isinstance(element, dict):
        return iteritems(element)
    else:
        return enumerate(element)


def EncodeImage(pix):
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

def DecodeImage(val):
    encoded = bytes(val, 'utf-8')
    img = QImage()
    if not img.loadFromData(QByteArray.fromBase64(encoded), "PNG"):
        img = None
    return img

