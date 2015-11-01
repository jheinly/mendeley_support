import sqlite3
import glob
import sys
import os
from unidecode import unidecode

if sys.version_info.major < 3:
    print('ERROR: Python 3 required in order to read SQLite file')
    sys.exit()

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print('USAGE: <output_file> [mendeley_sqlite]')
    print('    output_file     - file where the Mendeley folder structure will be written')
    print('    mendeley_sqlite - path to Mendeley sqlite file, or empty if the script')
    print('                      should attempt to find it automatically')
    sys.exit()

output_file_path = sys.argv[1]

def find_sqlite_in_folder(folder):
    if os.path.exists(folder):
        files = glob.glob(folder + '/*.sqlite')
        files = [f for f in files if os.path.basename(f) != 'monitor.sqlite']
        if len(files) > 1:
            print('ERROR: multiple sqlite files found')
            for file in files:
                print(file)
            sys.exit()
        elif len(files) == 1:
            return files[0]
    return 'invalid-path'

if len(sys.argv) == 3:
    mendeley_sqlite_path = sys.argv[2]
    if not os.path.exists(mendeley_sqlite_path):
        print('ERROR: mendeley sqlite path must exist, "' +
            mendeley_sqlite_path + '"')
        sys.exit()
else:
    print('Attempting to automatically find Mendeley sqlite file...')
    mendeley_sqlite_path = 'invalid-path'
    if os.name == 'nt': # Windows
        folder = os.path.join(os.path.expanduser('~'),
            'AppData/Local/Mendeley Ltd/Mendeley Desktop')
        mendeley_sqlite_path = find_sqlite_in_folder(folder)
    elif os.name == 'mac': # Mac
        folder = os.path.join(os.path.expanduser('~'),
            'Library/Application Support/Mendeley Desktop')
        mendeley_sqlite_path = find_sqlite_in_folder(folder)
    elif os.name == 'posix': # Posix
        folder = os.path.join(os.path.expanduser('~'),
            '.local/share/data/Mendeley Ltd./Mendeley Desktop')
        mendeley_sqlite_path = find_sqlite_in_folder(folder)
    else:
        print('ERROR: operating system not supported')
        sys.exit()
    if os.path.exists(mendeley_sqlite_path):
        print('Found Mendeley sqlite file:')
        print(mendeley_sqlite_path)
    else:
        print('ERROR: failed to automatically find Mendeley sqlite file')
        sys.exit()

connection = sqlite3.connect(mendeley_sqlite_path)
cursor = connection.cursor()

# Get a mapping between folder ids and their names.
folder_names_and_ids = []
for row in cursor.execute('SELECT id,name FROM Folders;'):
    folder_id = row[0]
    folder_name = unidecode(row[1])
    folder_names_and_ids.append((folder_name, folder_id))
folder_names_and_ids.sort()

# Get a mapping between folder ids and the document ids that belong to them.
folder_id_to_document_ids = dict()
document_ids_with_folder_assignments = set()
for row in cursor.execute('SELECT documentId,folderId FROM DocumentFolders;'):
    document_id = row[0]
    folder_id = row[1]
    if folder_id in folder_id_to_document_ids:
        folder_id_to_document_ids[folder_id].append(document_id)
    else:
        folder_id_to_document_ids[folder_id] = [document_id]
    document_ids_with_folder_assignments.add(document_id)

# Get a mapping between document ids and document titles and years.
document_id_to_title = dict()
document_id_to_year = dict()
document_ids_without_folder_assignments = []
for row in cursor.execute('SELECT id,title,year FROM Documents;'):
    document_id = row[0]
    document_title = unidecode(row[1])
    document_year = row[2]
    document_id_to_title[document_id] = document_title
    document_id_to_year[document_id] = document_year
    if document_id not in document_ids_with_folder_assignments:
        document_ids_without_folder_assignments.append(document_id)

def write_folder_to_output_file(output, folder_name, document_ids):
    global document_id_to_title
    global document_id_to_year

    # Write the folder name.
    output.write('=' * len(folder_name) + '\n')
    output.write(folder_name + '\n')
    output.write('-' * len(folder_name) + '\n')

    # Write the documents in the folder.
    for document_id in document_ids:
        document_title = document_id_to_title[document_id]
        document_year = document_id_to_year[document_id]
        output.write('"' + document_title + '", ' + str(document_year) + '\n')

# Write the output file.
output = open(output_file_path, 'w')
first_folder = True
for folder_name_and_id in folder_names_and_ids:
    # If this isn't the first folder written to the file, add an empty line to
    # the file.
    if not first_folder:
        output.write('\n')
    first_folder = False

    folder_name = folder_name_and_id[0]
    folder_id = folder_name_and_id[1]

    # Get the documents assigned to this folder.
    if folder_id in folder_id_to_document_ids:
        document_ids = folder_id_to_document_ids[folder_id]
    else:
        document_ids = []

    # Write the output for this folder.
    write_folder_to_output_file(output, folder_name, document_ids)

# If there were documents that were not assigned to a folder, write them at the
# end of the file.
if len(document_ids_without_folder_assignments) > 0:
    if not first_folder:
        output.write('\n')
    write_folder_to_output_file(output, 'Unsorted',
        document_ids_without_folder_assignments)

output.close()
