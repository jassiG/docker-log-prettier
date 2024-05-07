import sys
import json

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[31m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# {
#     "time": "2024-03-14T21:52:11+09:00",
#     "time_micro": "2024-03-14 21:52:11.582016",
#     "site_id": 126931,
#     "app": "PHP",
#     "level": "info",
#     "severity": "...",
#     "mode": "normal",
#     "member_id": 1,
#     "host": "...",
#     "uri": "...",
#     "message": "LOGGG<<./.../*.php:run:112>>LOGGG",
#     "message1": "LOGGG<</*.php:run:112>>LOGGG",
#     "message2": "message",
#     "message3": "",
#     "message4": "",
#     "message5": ""
# }

raw = "--raw" in sys.argv

def json_dumps_with_base_indent(obj, indent=2, base_indent=1):
    # Convert the object to a JSON string with the specified normal indentation
    json_string = json.dumps(obj, indent=indent)
    
    # Split the string into lines
    lines = json_string.split('\n')
    
    # Add the base indentation to each line
    base_indent_str = ' ' * base_indent
    lines_with_base_indent = [base_indent_str + line for line in lines]
    
    # Join the lines back into a single string
    return '\n'.join(lines_with_base_indent)

for line in sys.stdin:
    try:
        if "lite_mode=1" in line:
            print('', end='')
            continue
        parsed_json = json.loads(line)
        blacklist = ['time', 'site_id', 'app', 'level', 'severity', 'mode', 'rcms_request_id', 'remote_addr', 'ua', 'sess_id', 'member_id', 'host', 'uri', 'message']
        for key in blacklist:
            parsed_json.pop(key, None)

        if parsed_json.get('message1') and 'LOGGG' in parsed_json['message1']:
            if parsed_json.get('message2') and '--SM' in parsed_json['message2']:
                for (key, value) in parsed_json.items():
                    if key == 'time_micro':
                        continue
                    if "message" in key:
                        key = key.replace('message', 'M')
                    if key == 'M1':
                        value = value.replace('LOGGG<<', '').replace('>>LOGGG', '').split(':')
                        print(' ' + f'{key}: ', end='')
                        print(bcolors.OKGREEN + f'{value[0]}' + bcolors.ENDC, end=' ')
                        print(bcolors.BOLD + f'{value[2]}' + bcolors.ENDC, end=': ')
                    elif value:
                        value = value.replace('--SM', '')
                        value = value.replace(',', f'{bcolors.ENDC}{bcolors.OKGREEN},{bcolors.ENDC}{bcolors.OKCYAN}')
                        print('|' + bcolors.OKCYAN + value + bcolors.ENDC, end='|\t\t')
                print('', end='\n')
            else:
                print(bcolors.OKCYAN + '{' + bcolors.ENDC, end='\n')
                for (key, value) in parsed_json.items():
                    if "message" in key:
                        key = key.replace('message', 'M')
                    if key == 'time_micro':
                        key = 'T'
                    if key == 'M1':
                        value = value.replace('LOGGG<<', '').replace('>>LOGGG', '').split(':')
                        print(' ' + f'{key}: ', end='')
                        print(bcolors.OKGREEN + f'{value[0]}' + bcolors.ENDC, end='')
                        print(bcolors.BOLD + f' {value[1]} ' + bcolors.ENDC, end='')
                        print(bcolors.OKGREEN + f'{value[2]}' + bcolors.ENDC, end='\n')
                    else:
                        print(' ' + f'{key}: ', end='')
                        if (value.startswith('{') or value.startswith('[')) and (value.endswith('}') or value.endswith(']')) and not raw:
                            value = '\n' + json_dumps_with_base_indent(json.loads(value), indent=2, base_indent=2)
                        print(bcolors.OKCYAN + value + bcolors.ENDC, end='\n')
                print(bcolors.OKCYAN + '}' + bcolors.ENDC, end='\n')
    except json.JSONDecodeError:
            print(line, end='\n')
