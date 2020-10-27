import json
import os

AUTO_INPUT = False
REPLACE_DOWNLOADED = False

defaults_file = "./data/defaults.json"

if not os.path.exists('./data'):
    os.mkdir('data')

if not os.path.exists(defaults_file):
    with open(defaults_file, 'w') as w:
        w.write('{}')


def _input(prompt, dtype=str, default=None, multiple=False):
    if not default:
        default = read_default(prompt)
    print(prompt)
    if multiple:
        print("Use comma to seperate multiple choices")
    if AUTO_INPUT:
        print(f'AUTO:{default}')
        if default == None:
            raise SystemExit("Default not available")
        return default
    while True:
        try:
            user_input = input(f'<{default}>?')
            if user_input == '':
                if default == None:
                    continue
                return default
            elif ',' in user_input and multiple == True:
                if user_input[0] != '[' or user_input[-1] != ']':
                    user_input = f'[{user_input}]'
                user_input = json.loads(user_input)
                for ui in user_input:
                    assert type(ui) == dtype
            elif multiple == False:
                user_input = dtype(user_input)
            else:
                user_input = [dtype(user_input)]
            save_default(prompt, user_input)
            return user_input
        except (ValueError, AssertionError):
            print(f'Enter value of data type {dtype.__name__}.')


def get_yn(prompt):
    while True:
        choice = _input(f'{prompt} (y/n):', str).lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        print(f"Given response '{choice}' is not 'y' or 'n'.")


def choose_from_list(prompt, input_list, multiple=False):
    if len(input_list) == 0:
        return None, None
    print('\nAvailable Options:')
    for i, l in enumerate(input_list):
        print(f'{i}-{l}')
    while True:
        try:
            choice = _input(f'{prompt}: (0-{i})', int, multiple=multiple)
            if multiple:
                return choice, [input_list[i] for i in choice]
            return choice, input_list[choice]
        except IndexError:
            print('Entered number is not in options.')


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
