import os
import json
import glob

def add_prefix_to_classes(data):
    if 'classes' in data and isinstance(data['classes'], list):
        for class_item in data['classes']:
            if isinstance(class_item, dict):
                class_item['prefix'] = 'mondial'

def process_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Update the JSON content
    add_prefix_to_classes(data)

    # Write the updated JSON back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def process_all_json_files_in_directory(directory):
    for file_path in glob.iglob(os.path.join(directory, '**', '*.json'), recursive=True):
        process_json_file(file_path)

# Specify the directory to process
directory_to_process = '/Users/lukaslaskowski/Documents/HPI/KG/ontology_mappings/rdb2ontology/real-world/mondial/mapping'

# Process all JSON files in the specified directory and its subdirectories
process_all_json_files_in_directory(directory_to_process)