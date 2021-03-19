# BUG HUNTER!

This document is meant as a way to track currently unresolved bugs that are discovered by a user interacting with the application. It's not the cleanest method for debugging but it's quite useful given the size of the app and there only being one developer. There is also a [Jira tracker](https://petergish.atlassian.net/jira/software/projects/FC/boards/1) that provides a more organized and thorough bug tracking system. 

## Crickets *(global bugs)*

## Termites *(tree bugs)*

#### Working with sample

- adding characters to a parent in an existing family doesn't carry over their family name (or kingdom)

- toggling 'Connect Families' filter does not restore the families that were removed

- removing head of family that is a sibling in another family (Slyth) causes crash : 

  ```bash
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 992, in removeCharacter
      char_removed, partner_removed = Tree.MasterFamilies[instance.getTreeID()].delete_character(char_id)
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/family.py", line 332, in delete_character
      self.scene().removeItem(char)
  AttributeError: 'NoneType' object has no attribute 'removeItem'
  [1]    41901 abort      python -u
  ```

- creating new family off of partners in a family (Slyth) does not generate a new character

- deleting clone created by adding an offspring to partners in a family (Slyth) causes crash:

  ```bash
  QGraphicsScene::removeItem: item 0x7fd6f78d2a60's scene (0x0) is different from this scene (0x7fd75fefb3e0)
  2021-03-15 19:40:44.192 python[42032:2226916] modalSession has been exited prematurely - check for a reentrant call to endModalSession:
  Removing member: Slyth
  QGraphicsScene::removeItem: item 0x7fd6f708bb90's scene (0x0) is different from this scene (0x7fd75fefb3e0)
  Removing family head: Slyth
  QGraphicsScene::removeItem: item 0x7fd6f7095400's scene (0x0) is different from this scene (0x7fd75fefb3e0)
  Removing member: Slyth
  Split family heads and remove Slyth
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 1030, in deleteFamily
      delete_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Warning, "Delete family?", 
  TypeError: arguments did not match any overloaded call:
    QMessageBox(parent: QWidget = None): argument 1 has unexpected type 'Icon'
    QMessageBox(QMessageBox.Icon, str, str, buttons: Union[QMessageBox.StandardButtons, QMessageBox.StandardButton] = QMessageBox.NoButton, parent: QWidget = None, flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog|Qt.MSWindowsFixedSizeDialogHint): argument 5 has unexpected type 'Tree'
  [1]    42032 abort      python -u 
  ```

- removing Slyth on fresh restart causes error:

  ```bash
  Removing member: Slyth
  QGraphicsScene::removeItem: item 0x7fbf39de23f0's scene (0x0) is different from this scene (0x7fbf8cf292d0)
  Removing family head: Slyth
  QGraphicsScene::removeItem: item 0x7fbf39ecbfa0's scene (0x0) is different from this scene (0x7fbf8cf292d0)
  Removed Slyth from tree
  Removed Slyth - timeline
  Removed Slyth - scroll
  ```

- removing head of family when they are all that remains (Yadrig) causes crash:

  ```bash
  Removing family head: Yadrig
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 992, in removeCharacter
      char_removed, partner_removed = Tree.MasterFamilies[instance.getTreeID()].delete_character(char_id)
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/family.py", line 332, in delete_character
      self.scene().removeItem(char)
  AttributeError: 'NoneType' object has no attribute 'removeItem'
  [1]    42081 abort      python -u
  ```

- removing both partners of full family (Yadrig & Thalien) causes crash:

  ```bash
  Removing member: Thalién
  Could not remove character. Has children
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 992, in removeCharacter
      char_removed, partner_removed = Tree.MasterFamilies[instance.getTreeID()].delete_character(char_id)
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/family.py", line 303, in delete_character
      self.parent().temp_statusbar_msg.emit('Could not remove character. Has children.', 5000)
  AttributeError: 'Tree' object has no attribute 'temp_statusbar_msg'
  [1]    42118 abort      python -u 
  ```

- filtering kingdoms (removing Farfalle) causes crash:

  ```bash
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/treeTab.py", line 234, in handleFilters
      self.tree.filterTree(flag_type, flag)
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 1310, in filterTree
      self.filterKingdoms(kingdom_record, False)
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 1189, in filterKingdoms
      self.delCharFromScene(graphic_char)
  TypeError: native Qt signal is not callable
  [1]    42143 abort      python -u 
  ```

- families are not added back after being filtered

- alignment issues on single family member (Thalien) when adding offspring to their partner (Yadrig) <-- **URGENT** how should this actually work? There's a problem with having one character in two families. Not impossible and is realistic but a methodology needs to be established. For instance it doesn't make sense for Thalien to be in their own family with no offspring but Yadrig has all the characters in their family? 

- prevent duplicate names?

- tree spacing is incorrect for middle child + it gets too crowded at level 4

- removing child of parents in families (Slyth) causes crash:

  ```bash
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 994, in removeCharacter
      Tree.CharacterList.remove(instance)
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Data/hashList.py", line 52, in remove
      self.hashd[last][self.hashd[last].index(size-1)] = i
  ValueError: 22 is not in list
  [1]    42186 abort      python -u 
  ```

- PictureEditor needs improvement. Zoom is limited and can't pan the picture 

- CharacterCreator doesn't resize when a photo is chosen (gives warped perception of the imported photo)

- crowns aren't centering (and getting cut off) when transitioning to 'Name' display mode

- adding partner as 'Create New Character' causes crash:

  ```bash
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 558, in addNewCharacter
      create_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Question, "Create family?", 
  TypeError: arguments did not match any overloaded call:
    QMessageBox(parent: QWidget = None): argument 1 has unexpected type 'Icon'
    QMessageBox(QMessageBox.Icon, str, str, buttons: Union[QMessageBox.StandardButtons, QMessageBox.StandardButton] = QMessageBox.NoButton, parent: QWidget = None, flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog|Qt.MSWindowsFixedSizeDialogHint): argument 5 has unexpected type 'Tree'
  [1]    42218 abort      python -u 
  ```

- attempting to add a character by 'Select Existing' causes crash:

  ```bash
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 844, in <lambda>
      self.selection_window.char_select.clicked.connect(lambda: self.matchMaker(char_id))
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 881, in matchMaker
      if char1_id == char_2.getID():
  AttributeError: 'NoneType' object has no attribute 'getID'
  [1]    42261 abort      python -u 
  ```

- attempting to remove partnership (Slyth) causes crash:

  ```bash
  QGraphicsScene::removeItem: item 0x7fbb7f062b60's scene (0x0) is different from this scene (0x7fbbf23fbc00)
  Removed partnership Rochin
  QGraphicsScene::removeItem: item 0x7fbb7f304750's scene (0x0) is different from this scene (0x7fbbf23fbc00)
  Split family heads and remove Slyth
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 1030, in deleteFamily
      delete_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Warning, "Delete family?", 
  TypeError: arguments did not match any overloaded call:
    QMessageBox(parent: QWidget = None): argument 1 has unexpected type 'Icon'
    QMessageBox(QMessageBox.Icon, str, str, buttons: Union[QMessageBox.StandardButtons, QMessageBox.StandardButton] = QMessageBox.NoButton, parent: QWidget = None, flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog|Qt.MSWindowsFixedSizeDialogHint): argument 5 has unexpected type 'Tree'
  [1]    42291 abort      python -u 
  ```

  

#### Working with new book

- removing first character with no other character created causes crash:

  ```bash
  Removing member: Stiff
  Traceback (most recent call last):
    File "/Users/petergish/Nucleus/CSProjects/FantasyCreator/fantasycreator/Tree/tree.py", line 1030, in deleteFamily
      delete_fam_prompt = qtw.QMessageBox(qtw.QMessageBox.Warning, "Delete family?", 
  TypeError: arguments did not match any overloaded call:
    QMessageBox(parent: QWidget = None): argument 1 has unexpected type 'Icon'
    QMessageBox(QMessageBox.Icon, str, str, buttons: Union[QMessageBox.StandardButtons, QMessageBox.StandardButton] = QMessageBox.NoButton, parent: QWidget = None, flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.Dialog|Qt.MSWindowsFixedSizeDialogHint): argument 5 has unexpected type 'Tree'
  [1]    42352 abort      python -u 
  ```

- editing crown status does not display until toggling 'Show Rulers'
- race case of requesting user to select

## Millipede *(timeline bugs)*

## Booklice *(map bugs)*

## Beetles *(scroll bugs)*

