import sqlite3
import sys
import os

num_expected_args = 2
if len(sys.argv) != num_expected_args + 1:
  print('USAGE: <mendeley_sqlite> <output_file>')
  sys.exit()

mendeley_sqlite_path = sys.argv[1]
output_file_path = sys.argv[2]

if not os.path.exists(mendeley_sqlite_path):
  print('ERROR: mendeley sqlite path must exist, "' + mendeley_sqlite_path + '"')
  sys.exit()

connection = sqlite3.connect(mendeley_sqlite_path)
cursor = connection.cursor()

folder_id_to_name = dict()
for row in cursor.execute('SELECT id,name FROM Folders;'):
  folder_id = row[0]
  folder_name = row[1]
  folder_id_to_name[folder_id] = folder_name

folder_id_to_document_ids = dict()
for row in cursor.execute('SELECT documentId,folderId FROM DocumentFolders;'):
  document_id = row[0]
  folder_id = row[1]
  if folder_id in folder_id_to_document_ids:
    folder_id_to_document_ids[folder_id].append(document_id)
  else:
    folder_id_to_document_ids[folder_id] = [document_id]

document_id_to_title = dict()
document_id_to_year = dict()
for row in cursor.execute('SELECT id,title,year FROM Documents;'):
  document_id = row[0]
  document_title = row[1]
  document_year = row[2]
  document_id_to_title[document_id] = document_title
  document_id_to_year[document_id] = document_year

output = open(output_file_path, 'w')
first_folder = True
for folder_id in folder_id_to_name:
  folder_name = folder_id_to_name[folder_id]
  if not first_folder:
    output.write('\n')
  first_folder = False
  output.write('=' * len(folder_name) + '\n')
  output.write(folder_name + '\n')
  output.write('-' * len(folder_name) + '\n')
  
  if folder_id not in folder_id_to_document_ids:
    continue
  document_ids = folder_id_to_document_ids[folder_id]
  for document_id in document_ids:
    document_title = document_id_to_title[document_id]
    document_year = document_id_to_year[document_id]
    output.write('"' + document_title + '", ' + str(document_year) + '\n')
output.close()
