# Technical Documentation

# Fantasty Creator Code Outline

## Data

#### `characterLookup.py`

#### `database.py`

#### `graphStruct.py`

#### `hashList.py`

#### `treeStruct.py`

### Data Storage

#### Meta Data

- `book_title` - book title as entered by user (default to "Untitled")
- `world_name` - name of the storie's world (default to "Unnamed")
- `NULL_ID` - constant value serving as a universal NULL for any aspect of the database
- `map_path` - file path of the current map image
- `__IMG__` - byte string representing an encoded image which is the map

#### Preferences

##### General

- `book_title` - as reflected in the preferences window
- `world_name` - as reflected in the preferences window

##### Mechanics

- `year_format` - number of digits needed for the world's years
- `month_format` - number of digits for the world's months
- `day_format` - number of digits for the world's days
- `year_range` - interval of years involved in the story
- `month_range` - interval of months used in the world
- `day_range` - interval of days used in the world
- ` time_order` - stores the order of dates ie. day/month/year

##### Tree Tab

- `generation_spacing` - the vertical spacing between generations
- `sibling_spacing` - the initial horizontal value between two siblings before offset is applied
- `desc_dropdown` - vertical offset describing the "dropdown" distance from the horizontal connecting lines of siblings
- `partner_spacing` - initial distance between sibling before offset
- `expand_factor` - constant factor to scale the tree horizontally
- `offset_factor` - constant factor to scale each generation based on the number of siblings and its height
- `ruler_crown_size` - single integer representing the side length of the square crown image
- `ruler_crown_img` - file path to the universal crown image
- `char_img_width` - universal width of character images
- `char_img_height` - universal height of character images

##### Timeline Tab

- `min_year` - year to start the timeline
- `max_year` - year to end the timeline
- `time_periods` - dictionary of time periods created by the user which hold a name and interval of dates
- `timeline_padding` - in the event of min_year/max_year being set to "auto", adds a cushion to the time ranges supplied in the mechanics tab
- `timeline_scene_bounds` - rectangular coordinates outlining the timeline scene
- `timeline_axis_padding` - *deprecated* 

##### Map Tab

- `map_scene_bounds` - rectangular coordinates of the map scene

##### Scroll Tab

- TBD

#### Characters

- `char_id` - unique id distinguishing a character
- `name` - character's name
- `fam_id` - the blood family the character belongs to
- `parent_0` - the character's first (primary) parent's unique id
- `parent_1` - the character's second parent's unique id
- `partnerships` - list of dictionaries holding the unique romantic id of the partnership and the partner's unique id
- `sex` - sex assigned to the character by the user
- `birth` - date (using story time) of the character's birth
- `death` - date (using story time) of the character's death
- `ruler` - boolean indicating if the character is a ruler
- `picture_path` - file path to the image associated with the character
- `kingdom_id` - unique id of the kingdom the character belongs to
- `race` - race assigned to the character by the user
- `timeline_ord` - hack to determine the position of the character in the timeline
- `graphical_rect` - *soon to be deprecated* stores the character's position on map when user saves (should be integrated with time stamps)
- `events` - list of dictionaries describing events the character was involved in. Event dictionaries hold:
  - `event_id` - unique id of the event
  - `event_name` - name of the event
  - `location_id` - unique id of the location where the event occurred
  - `event_type` - category created by the user to classify the event
  - `start` - date (in story time) when the event started
  - `end` - date (in story time) when the event ended
  - `event_description` - user supplied notes about the event
- `notes` - any notes the character added about the character
- `__IMG__` - encoded character image

#### Families

- `fam_id` - unique id of the family
- `fam_name` - family name associated with `fam_id`
- `fam_type` - flag classifying the type of family

#### Kingdoms

- `kingdom_id` - unique id of the kingdom
- `kingdom_name` - family name associated with `kingdom_id`

#### Events

- `event_id` - unique id of the event
- `event_name` - name of the event
- `start` - date (in story time) of the beginning of the event
- `end` - date (in story time) of the end of the event
- `location_id` - unique id of the location where the event occurred
- `event_type` - user supplied classification of the event
- `event_description` - notes the user supplied regarding the event

#### Locations

- `location_id` - unique id of the location
- `graphical_rect` - rectangular coordinates of the location on the map
- `location_name` - name of the location
- `location_type` - user supplied classification of the location
- `location_details` - notes the user supplied regarding the location
- `picture_path` - file path of the image chosen for the location
- `__IMG__` - encoded image of the location

#### Timestamps

- `graphical_point` - (x, y) coordinates of the timestamp's graphical location on the map
- `timestamp` - date (in story time) of the timestamp
- `char_id` - unique id of the character involved in the timestamp
- `location_id` - unique id of the location where the timestamp occurred

## Map

#### `mapBuilderGraphics.py`

#### `mapBuilderObjects.py`

#### `mapBuilderTab.py`

#### `mapBuilderUI.py`

## Mechanics

#### `animator.py`

#### `flags.py`

#### `materializer.py`

#### `separableTabs.py`

## Popups

#### `aboutWindow.py`

#### `bugReporter.py`

#### `controlPanel.py`

#### `preferencesWindow.py`

#### `welcomeWindow.py`

## Scroll

#### `scrollGraphics.py`

#### `scrollTab.py`

## Timeline

#### `timelineEntries.py`

#### `timelineGraphics.py`

#### `timelineTab.py`

## Tree

#### `character.py`

#### `family.py`

#### `Tree.py`

#### `treeAccessories.py`

#### `treeGraphics.py`

#### `treeTab.py`

## Signals & Slots

