import json
import os


AUTO_INPUT = False

defaults_file = "./data/defaults.json"

if not os.path.exists(defaults_file):
    with open(defaults_file, 'w') as w:
        w.write('{}')


def _input(prompt, dtype=str, default=None):
    if not default:
        default = read_default(prompt)
    print(prompt)
    if AUTO_INPUT:
        print(f'AUTO:{default}')
        if default == None:
            raise SystemExit("Default not available")
        return default
    while True:
        try:
            user_input = input(f'<{default}>?')
            if user_input == '':
                user_input = default
            else:
                user_input = dtype(user_input)
            save_default(prompt, user_input)
            return user_input
        except ValueError:
            print(f'Enter value of data type {dtype.__name__}.')


def get_yn(prompt):
    while True:
        choice = _input(f'{prompt} (y/n):', str).lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        print(f"Given response '{choice}' is not 'y' or 'n'.")


def choose_from_list(input_list):
    if len(input_list) == 0:
        return None, None
    print('\nAvailable Options:')
    for i, l in enumerate(input_list):
        print(f'{i}-{l}')
    choice = _input(f'your choice(0-{i})', int)
    return choice, input_list[choice]


def read_default(prompt):
    with open(defaults_file, 'r') as r:
        defaults = json.load(r)
    return defaults.get(prompt)


def save_default(prompt, val):
    with open(defaults_file, 'r') as r:
        defaults = json.load(r)

    defaults[prompt] = val

    with open(defaults_file, 'w') as w:
        json.dump(defaults, w)
