import json
import os
import sys


def validate_json_files(root_directory):
    all_valid = True
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(root_directory) for f in filenames if
             f.endswith('.json')]

    print(f'Validating {len(files)} JSON files...')

    for f in files:
        try:
            print(f'Validating {f}')
            with open(f, 'r') as file:
                json.load(file)
        except json.JSONDecodeError as e:
            print(f'Invalid JSON file: {f}, error: {e}')
            all_valid = False
        except Exception as e:
            print(f'Error reading file: {f}, error: {e}')
            all_valid = False

    return all_valid


if __name__ == "__main__":
    directory = '.'  # Current directory
    if not validate_json_files(directory):
        sys.exit(1)
    else:
        sys.exit(0)