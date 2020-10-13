import json
import os


defaults_file = "./data/defaults.json"

if not os.path.exists(defaults_file):
    with open(defaults_file, 'w') as w:
        w.write('{}')


def _input(prompt, dtype=str, default=None):
    if not default:
        default = read_default(prompt)
    print(prompt)
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
