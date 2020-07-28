# External Signals (outside of own class)

## TreeTab

      - submitted --> ()

## TreeGraphics

### TreeView

      - addedChars --> list(Characters)
      - removedChars --> list(Characters)
      - updatedChars --> list(Characters)
      - temp_statusbar_msg --> (str, int)
      - families_removed --> list()
      - families_added --> list()

### TreeScene
  
      - add_descendants --> (uuid)
      - remove_char --> (uuid)
      - edit_char --> (uuid)

## CharacterLookup

### LookUpTableView

      - char_selected --> (uuid)

### LookUpTableModel

      - cell_changed --> (dict)

## ControlPanel

### TreeControlPanel

      - filtersChanged --> (int)

## Character

### CharacterCreator

      - submitted --> (dict)
      - closed --> ()
  