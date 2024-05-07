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
#     "severity": "INFO",
#     "mode": "normal",
#     "rcms_request_id": "15314a79-3ce1-4bab-87f8-11c62aecde55",
#     "remote_addr": "192.168.65.1",
#     "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
#     "sess_id": "lcmi4scompstn498p5rr8t1n57sbi2ufmt105dfme06e50lvpmt1",
#     "member_id": 1,
#     "host": "https://docker.r-cms.jp",
#     "uri": "/management/menu/update/?pageID=1&per_page=20&filters=%7B%22filter%22%3A%22member_id%20!=%205%20AND%20module_id%20%3C%203432%20AND%20content_exists%20=%201%22%2C%22order%22%3A%22%22%7D&status=&batch_type=&search_flg=1&own=1&module_type=&search_lang=ja&search_update=&from_dt=2024/02/01&to_dt=2024/03/12",
#     "message": "LOGGG<</opt/rcms/lib/modules/common/admin/common_list_history.php:run:112>>LOGGG",
#     "message1": "LOGGG<</opt/rcms/lib/modules/common/admin/common_list_history.php:run:112>>LOGGG",
#     "message2": "strSQL_forHistory: SELECT lang, member_id, module_id, module_type , status ,change_ymdhi AS change_ymdhi, data_history_id, (SELECT name1 FROM t_member_header vmh WHERE vmh.member_id = t_da.member_id) AS admin_nm,admin_nm AS admin_nm2 FROM t_data_history AS t_da where module_type IN ('topics','csvtable','tag','rcms_api','files','kuroco_front','edge','comment','inquiry','magazine','member','ownmember','pre_member','group','member_custom_search','onetime','mailtemplateedit','logs','batch','staticcontents','approvalflow','ec','menu','site','site_payment','memberregist_sso_saml_idp','memberregist_sso_saml_sp','memberregist_sso_oauth_sp','memberregist_sso_idaas_sp','sendgrid','twilio','firebase','s3','vimeo','openai','slack','recaptcha','access_data','vaddy','stripe','hubspot','twitter','wordpress','searchconsole','line','topics_admin','ec_admin','topics_category','external','memberregist') and member_id = 1 and lang = 'ja' and change_ymdhi >= '2024-02-01' and change_ymdhi <= '2024-03-12 23:59:59'  ORDER BY change_ymdhi DESC, status ASC LIMIT 200 ",
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
