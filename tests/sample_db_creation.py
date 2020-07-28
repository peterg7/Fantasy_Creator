# PyQt 
from PyQt5.QtCore import QPointF, QRectF

# Built-in Modules
import uuid

# User-defined modules
from storyTime import Time
from database import VolatileDB
# BREAK

db = VolatileDB('sample_1.json')


meta_db = db.table('meta')
meta_db.insert( # Holds meta data regarding this project
    {
        'book_title': 'Sample Book Title',
        'world_name': 'Sample World',
        'NULL_ID': uuid.UUID('4d78932d2af949fd8bb54dba3d9c9db6'),
        'TERM_ID': uuid.UUID('ccebb29b98054cd7bfa76135604fa96c'),
        'world_name': 'Sample World',
        'map_path': ':/sample-images/sample_map.png',
        '__IMG__': ''
    } # Maybe add some sort of month as words?
)

preferences_db = db.table('preferences')
preferences_db.insert_multiple([
    {
        'tab': 'general',
        'book_title': 'Sample Book Title',
        'world_name': 'Sample World',
        'char_img_size': [125, 125]
    },
    {
        'tab': 'mechanics',
        'year_format': 4,
        'month_format': 2,
        'day_format': 2,
        'year_range': (1500, 2400),
        'month_range': (1, 65),
        'day_range': (1, 32),
        'time_order': {
            'year': 'THREE',
            'month': 'TWO',
            'day': 'ONE'
        }
    },
    {
        'tab': 'tree',
        'generation_spacing': 300,
        'sibling_spacing': 100,
        'desc_dropdown': 125,
        'partner_spacing': 200,
        'expand_factor': 20,
        'offset_factor': 12,

        'ruler_crown_size': 50,
        'ruler_crown_img': ':/dflt-tree-images/crown.png',
        'char_img_width': 180,
        'char_img_height': 180
    },
    {
        'tab': 'timeline',
        'min_year': 'auto',
        'max_year': 'auto',
        'time_periods': {
            'Elation': [Time(year=1643, month=1, day=1), Time(year=1911, month=1, day=1)],
            'Dispora': [Time(year=1920, month=1, day=1), Time(year=1960, month=1, day=1)],
            'Tenebrae': [Time(year=1965, month=1, day=1), Time(year=2002, month=1, day=1)],
            'Resurgence': [Time(year=2005, month=1, day=1), Time(year=2200, month=1, day=1)]
        },
        'timeline_padding': 100,
        'timeline_scene_bounds': (0, 0, 8500, 3000),
        'timeline_axis_padding': 25
    },
    {
        'tab': 'map',
        'map_scene_bounds': (0, 0, 10000, 10000)
    },
    {
        'tab': 'scroll'
    }
])

character_db = db.table('characters')
character_db.insert_multiple([  # Main Family
    { # Sample character 1
        'char_id': uuid.UUID('4376f9449f7c11ea87f48c8590793824'), 
        'name': 'Yadrig', 
        'fam_id': uuid.UUID("4335d57e036743e4bf0139937d152348"), 
        'parent_0': uuid.UUID('ccebb29b98054cd7bfa76135604fa96c'), 
        'parent_1': None, 
        'partnerships': [{'rom_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
                        'p_id': uuid.UUID("817ce5dca3c311ea8bab8c8590793824")}],
        'sex': 'Male',
        'birth': Time(year=1910, month=54, day=3), 
        'death': Time(year=1972, month=22, day=9), 
        'ruler': True, 
        'picture_path': ":/sample-images/11.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 0,
        'graphical_rect': None,
        'events': [
            {
                'event_id': uuid.UUID('8a2efee23930454e94e242ac71e86848'),
                'event_name': "The Night War",
                'location_id': uuid.UUID('84101ffdb78f43c7aea35a1dc66a25c8'),
                'event_type': 'Death',
                'start': Time(year=1972, month=22, day=9),
                'end': Time(year=1972, month=22, day=9),
                'event_description': 'Homie died'
            }
        ],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 2
        'char_id': uuid.UUID("511271d29f7c11ea87f48c8590793824"), 
        'name': 'Ludimar', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("4376f9449f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Male',
        'birth': Time(year=1899, month=34, day=21), 
        'death': Time(year=2034, month=12, day=30), 
        'ruler': False, 
        'picture_path': ":/sample-images/2.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 1,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 3
        'char_id': uuid.UUID("6158048a9f7c11ea87f48c8590793824"), 
        'name': 'Terük', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("4376f9449f7c11ea87f48c8590793824"), 
        'parent_1': None,
        'partnerships' : [], 
        'sex': 'Male',
        'birth': Time(year=1991, month=38, day=1), 
        'death': Time(year=2054, month=15, day=18), 
        'ruler': True, 
        'picture_path': ":/sample-images/3.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 2,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 4
        'char_id': uuid.UUID("7f62a2329f7c11ea87f48c8590793824"), 
        'name': 'Bellinar', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("511271d29f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [], 
        'sex': 'Female',
        'birth': Time(year=1852, month=38, day=1), 
        'death': Time(year=1938, month=5, day=26), 
        'ruler': False, 
        'picture_path': ":/sample-images/4.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 3,
        'graphical_rect': None,
        'events': [
            {
                'event_id': uuid.UUID('54d817aa-1864-4d52-8de1-e8aaee6de52a'),
                'event_name': "Fall of Brisbane",
                'location_id': uuid.UUID('0f0d3169be054ecbb989c9b9b00483a7'),
                'event_type': 'Ruler Change',
                'start': Time(year=1911, month=31, day=9),
                'end': Time(year=1911, month=31, day=9),
                'event_description': 'My boi is king'
            }
        ],
        'notes': """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Baskerville'; font-size:14pt;">This homie knows what's up. She's been all over the place just being a savage.</span></p></body></html>""",
        "__IMG__": ""
    },
    { # Sample character 5
        'char_id': uuid.UUID("8bc724c69f7c11ea87f48c8590793824"), 
        'name': 'Glodrick', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("511271d29f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Male',
        'birth': Time(year=2021, month=24, day=17), 
        'death': Time(year=2108, month=43, day=4), 
        'ruler': False, 
        'picture_path': ":/sample-images/5.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 4,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 6
        'char_id': uuid.UUID("9e5b169c9f7c11ea87f48c8590793824"), 
        'name': 'Tormin', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("6158048a9f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Male',
        'birth': Time(year=2019, month=33, day=6), 
        'death': Time(year=2102, month=4, day=25), 
        'ruler': False, 
        'picture_path': ":/sample-images/6.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 5,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 7
        'char_id': uuid.UUID("a532d9149f7c11ea87f48c8590793824"), 
        'name': 'Dolamyr', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("6158048a9f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Male',
        'birth': Time(year=2033, month=13, day=7), 
        'death': Time(year=2112, month=42, day=11), 
        'ruler': True, 
        'picture_path': ":/sample-images/7.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 6,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 8
        'char_id': uuid.UUID("aeb167309f7c11ea87f48c8590793824"), 
        'name': 'Slyth', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("6158048a9f7c11ea87f48c8590793824"), 
        'parent_1': None,  
        'partnerships': [{'rom_id': uuid.UUID("9de9ba438ce04c738a82f25be646f1cb"),
                        'p_id': uuid.UUID("f4a7a1a6a54311ea9839acde48001122")}],
        'sex': 'Male',
        'birth': Time(year=2035, month=18, day=17), 
        'death': Time(year=2112, month=12, day=6), 
        'ruler': False, 
        'picture_path': ":/sample-images/8.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 7,
        'events': [],
        'graphical_rect': None,
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 9
        'char_id': uuid.UUID("944064dc9f7c11ea87f48c8590793824"), 
        'name': 'Morryl', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("511271d29f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Male',
        'birth': Time(year=2040, month=43, day=14), 
        'death': Time(year=2112, month=22, day=13), 
        'ruler': False, 
        'picture_path': ":/sample-images/9.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 8,
        'graphical_rect': None,
        'events': [
            {
                'event_id': uuid.UUID('d297819f66974505b95e2b3fdf242e64'),
                'event_name': "Sample9's Montage",
                'location_id': uuid.UUID('fe3ba3943366446880922972e424f461'),
                'event_type': 'Training',
                'start': Time(year=2045, month=12, day=10),
                'end': Time(year=2061, month=34, day=2),
                'event_description': 'Training to be the very best'
            }
        ],
        'notes': "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\np, li { white-space: pre-wrap; }\n</style></head><body style=\" font-family:'Baskerville'; font-size:16pt; font-weight:400; font-style:normal;\">\n<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'Baskerville';\">They say looks can be decieving but this boi is the stapleton of that, looking like a fragile, innocent child this dude's actually the lands best Scout (the group of elite fighters known for their ferocity and bloodlust)</span></p></body></html>",
        "__IMG__": ""
    },
    { # Sample character 10
        'char_id': uuid.UUID("b530f1669f7c11ea87f48c8590793824"), 
        'name': 'Navari', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("7f62a2329f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Female',
        'birth': Time(year=2044, month=15, day=7), 
        'death': Time(year=2118, month=45, day=13), 
        'ruler': False, 
        'picture_path': ":/sample-images/10.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 9,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 11
        'char_id': uuid.UUID("bb4cad929f7c11ea87f48c8590793824"), 
        'name': 'Ardin', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("7f62a2329f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Male',
        'birth': Time(year=2064, month=21, day=17), 
        'death': Time(year=2126, month=52, day=11), 
        'ruler': False, 
        'picture_path': ":/sample-images/1.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 10,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    },
    { # Sample character 12
        'char_id': uuid.UUID("c0bc3a369f7c11ea87f48c8590793824"), 
        'name': 'Dryll', 
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("944064dc9f7c11ea87f48c8590793824"), 
        'parent_1': None, 
        'partnerships' : [],
        'sex': 'Female',
        'birth': Time(year=2052, month=35, day=19), 
        'death': Time(year=2212, month=16, day=8), 
        'ruler': True, 
        'picture_path': ":/sample-images/12.png",
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'), 
        'race': 'Dwarf',
        'timeline_ord': 11,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    }])

character_db.insert(    # Partner 1
    { 
        'char_id': uuid.UUID("817ce5dca3c311ea8bab8c8590793824"), 
        'name': 'Thalién', 
        'fam_id': uuid.UUID("fed47a08a3c411ea8bab8c8590793824"), 
        'parent_0': uuid.UUID("4d78932d2af949fd8bb54dba3d9c9db6"), 
        'parent_1': None,  
        'partnerships' : [{'rom_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"),
                        'p_id': uuid.UUID("4376f9449f7c11ea87f48c8590793824")}],
        'sex': 'Male',
        'birth': Time(year=1987, month=44, day=12), 
        'death': Time(year=2054, month=37, day=8), 
        'ruler': False, 
        'picture_path': ":/sample-images/13.png",
        'kingdom_id': uuid.UUID('e1dc129b-63f3-447a-9565-7396c69aea9c'), 
        'race': 'Elf',
        'timeline_ord': 12,
        'graphical_rect': None,
        'events': [
            {
                'event_id': uuid.UUID('8a2efee2-3930-454e-94e2-42ac71e86848'),
                'event_name': "The Night War",
                'location_id': uuid.UUID('84101ffdb78f43c7aea35a1dc66a25c8'),
                'event_type': 'Battle',
                'start': Time(year=1911, month=31, day=9),
                'end': Time(year=1911, month=31, day=9),
                'event_description': 'Cemented himself as an all-time GOAT'
            }
        ],
        'notes': '',
        "__IMG__": ""
    })

character_db.insert(    # Partner 2
    { 
        'char_id': uuid.UUID("f4a7a1a6a54311ea9839acde48001122"), 
        'name': 'Rochin', 
        'fam_id': uuid.UUID("b94d301ca54311ea9839acde48001122"), 
        'parent_0': uuid.UUID("4d78932d2af949fd8bb54dba3d9c9db6"), 
        'parent_1': None, 
        'partnerships': [{'rom_id': uuid.UUID("9de9ba438ce04c738a82f25be646f1cb"),
                        'p_id': uuid.UUID("aeb167309f7c11ea87f48c8590793824")}],
        'sex': 'Male',
        'birth': Time(year=2038, month=4, day=22), 
        'death': Time(year=2054, month=26, day=10), 
        'ruler': False, 
        'picture_path': ":/sample-images/14.png",
        'kingdom_id': uuid.UUID('9e6f1bfc-6546-48c4-8d9e-fe20702b8130'), 
        'race': 'Dwarf',
        'timeline_ord': 13,
        'graphical_rect': None,
        'events': [],
        'notes': '',
        "__IMG__": ""
    })


families_db = db.table('families')
families_db.insert_multiple([
    {
        "fam_id": uuid.UUID("4d78932d2af949fd8bb54dba3d9c9db6"),
        "fam_name": "None",
        "fam_type": None
    },
    {
        'fam_id': uuid.UUID("5f49ddc0a3c411ea8bab8c8590793824"),
        'fam_name': 'Pelagus',
        "fam_type": 19
    },
    {
        'fam_id': uuid.UUID("fed47a08a3c411ea8bab8c8590793824"),
        'fam_name': 'Argnarum',
        'fam_type': 18
    },
    {
        'fam_id': uuid.UUID("b94d301ca54311ea9839acde48001122"),
        'fam_name': 'Dundrake',
        'fam_type': 18
    }
])

kingdoms_db = db.table('kingdoms')
kingdoms_db.insert_multiple([
    {
        "kingdom_id": uuid.UUID("4d78932d2af949fd8bb54dba3d9c9db6"),
        "kingdom_name": "None"
    },
    {
        'kingdom_id': uuid.UUID('2a678c89-56d0-4fa5-af25-959b7a04c894'),
        'kingdom_name': 'Mythryl'
    },
    {
        'kingdom_id': uuid.UUID('9e6f1bfc-6546-48c4-8d9e-fe20702b8130'),
        'kingdom_name': 'Farfalle'
    },
    {
        'kingdom_id': uuid.UUID('e1dc129b-63f3-447a-9565-7396c69aea9c'),
        'kingdom_name': 'Kahl Dorvin'
    }
])

events_db = db.table('events')
events_db.insert_multiple([
    
    {
        'event_id': uuid.UUID('54d817aa-1864-4d52-8de1-e8aaee6de52a'),
        'event_name': 'Fall of Brisbane',
        'start': Time(year=1911, month=31, day=9),
        'end': Time(year=1911, month=31, day=9),
        'location_id': uuid.UUID('0f0d3169be054ecbb989c9b9b00483a7'),
        'event_type': 'Kingdom collapse',
        'event_description': 'With this collapse, the city of Trebech was eliminated from history'
    },
    {
        'event_id': uuid.UUID('8a2efee2-3930-454e-94e2-42ac71e86848'),
        'event_name': 'The Night War',
        'start': Time(year=1964, month=2, day=13),
        'end': Time(year=2001, month=22, day=4),
        'location_id': uuid.UUID('84101ffdb78f43c7aea35a1dc66a25c8'),
        'event_type': 'War',
        'event_desription': 'A war so destructive it left the skies black for years'
    }
])

locations_db = db.table('locations')
locations_db.insert_multiple([
    {
        'location_id': uuid.UUID('0f0d3169be054ecbb989c9b9b00483a7'),
        'graphical_rect': QRectF(3994.6057739089756, 4940.871544564103, 180.0, 180.0),
        'location_name': 'Trebech',
        'location_type': 'Large city',
        'location_details': 'Hotbed area, like a Tarbean',
        'picture_path': ':/sample-images/trebech.png',
        "__IMG__": ""
    },
    {
        'location_id': uuid.UUID('84101ffdb78f43c7aea35a1dc66a25c8'),
        'graphical_rect': QRectF(5873.92759051186, 5678.658551810238, 180.0, 180.0),
        'location_name': "West Y'll",
        'location_type': 'Local port',
        'location_details': 'This is a pretty cool port',
        'picture_path': ':/sample-images/west-yll.png',
        "__IMG__": ""
    },
    {
        'location_id': uuid.UUID('fe3ba3943366446880922972e424f461'),
        'graphical_rect': QRectF(5766.547440699125, 4088.561797752809, 180.0, 180.0),
        'location_name': "Korvithe",
        'location_type': 'Unknown',
        'location_details': 'All the cool kids know about Korvithe',
        'picture_path': ':/sample-images/korvithe.png',
        "__IMG__": ""
    }
])

timestamps_db = db.table('timestamps')
timestamps_db.insert_multiple([
    {
        'graphical_point': QPointF(4500, 5000),
        'timestamp': Time(year=2233, month=21, day=3),
        'char_id': uuid.UUID("944064dc9f7c11ea87f48c8590793824"),
        'location_id': None
    },
    {
        'graphical_point': QPointF(4000, 4100),
        'timestamp': Time(year=2200, month=12, day=5),
        'char_id': uuid.UUID("944064dc9f7c11ea87f48c8590793824"),
        'location_id': None
    }
    ,
    {
        'graphical_point': QPointF(5000, 5600),
        'timestamp': Time(year=1940, month=32, day=11),
        'char_id': uuid.UUID("a532d9149f7c11ea87f48c8590793824"),
        'location_id': None
    }
])

db.dump()

db.close()
# for item in character_db:
#     print(item['name'])

# for item in families_db:
#     print(item['name'])

# User = Query()
# print(character_db.search(User.fam_id))

