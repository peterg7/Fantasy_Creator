import re
import os
from pathlib import Path
from distutils.dir_util import copy_tree

SRC_DIR = '/Users/petergish/Nucleus/PersonalTime/PyQt/Fantasy_Creator'
DEST_DIR = '/Volumes/Skylab/Fantasy_Creator_source'

MODULE_PREFIX = 'fantasycreator'

EXCLUDED_DIRS = ('.vscode', '.git', 'fantasycreator/resources', '__pycache__')
EXCLUDED_FILES = ('moduleConverter.py', 'config.py', 'resources.py', 'run.py', 
                    'setup.py')

MODULE_FILES = []

# Copy entire dev tree
try:
    copy_tree(SRC_DIR, DEST_DIR)
except:
    print('Could not access external drive. Aborting...')
    exit()

for path in Path(DEST_DIR).rglob('*.py'):
    if path.name not in EXCLUDED_FILES and not path.name.startswith('__'):
        MODULE_FILES.append(path)

for current_file in MODULE_FILES:

    with open(current_file, 'r') as read_file:
        contents = read_file.readlines()

    found_imports = False
    line_count = 0
    for line in contents:
        if not line.startswith(('class', 'def', '# BREAK')):
            if found_imports and line != '\n':
                # print([ord(c) for c in line])
                if line.startswith('from'): # importing user module
                    line = f'from {MODULE_PREFIX}.' + line[len('from '):]
                elif line.startswith('import'): # import resources
                    line = f'from {MODULE_PREFIX} ' + line
                contents[line_count] = line

            elif re.sub(r'\s', '', line.rstrip()).casefold() in ('#user-definedmodules',
                                                                '#externalresources'):
                found_imports = True
            line_count += 1
        else:
            break

    if current_file.name == 'mainWindow.py':
        cutoff = 0
        for line in reversed(contents):
            cutoff += 1
            if re.sub(r'\s', '', line.strip()).casefold() == '#non-bundledexecution':
                break
        contents = contents[:-(cutoff+1)]


    with open(f'{current_file}', 'w') as write_file:
        write_file.writelines(contents)