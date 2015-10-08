#!/usr/local/bin/python3.2
# coding: utf8

import fnmatch
import sys
import os
import inspect
import platform
python_version = sys.version[0]
platform_system=platform.system()

def getPythonVersion():
    global python_version
    return python_version

def assertEqual(expected, result):
    if not isinstance(expected, str):
        expected = str(expected)
    if not isinstance(result, str):
        result = str(result)

    if result != expected:
    #       if expected != result:
        raise Exception('实际结果[%s]不等于期望结果[%s]' % (result, expected))

def assertIn(expected,result):
    if not isinstance(expected,str):
        expected=str(expected)
    if not isinstance(result,str):
        result=str(result)
    if result not  in expected:
        raise Exception('实际结果[%s]不在期望结果[%s]之内'%(result,expected))


def assertCmp(expected, result, cmp):
    if not isinstance(expected, str):
        expected = str(expected)
    if not isinstance(result, str):
        expected = str(result)

    if cmp == '>' or cmp == 'more' or cmp == 'm':
        if not (result > expected):
            raise Exception('实际结果[%s]不大于期望结果[%s]' % (result, expected))
    elif cmp == '>=' or cmp == 'more or equal' or cmp == 'me':
        if not (result >= expected):
            raise Exception('实际结果[%s]不大于等于期望结果[%s]' % (result, expected))
    elif cmp == '<' or cmp == 'less' or cmp == 'l':
        if not (result < expected):
            raise Exception('实际结果[%s]不小于期望结果[%s]' % (result, expected))
    elif cmp == '<=' or cmp == 'less or equal' or cmp == 'le':
        if not (result >= expected):
            raise Exception('实际结果[%s]不小于等于期望结果[%s]' % (result, expected))
    elif cmp == '!=' or cmp == 'not equal' or cmp == 'ne':
        if not (result != expected):
            raise Exception('实际结果[%s]等于期望结果[%s]' % (result, expected))


def assertNotIn(expected, result):
    if result in expected:
        raise Exception('实际结果[%s]存在于非期望结果[%s]' % (result, expected))


def assertContain(expected, result):
    if expected not in result:
        raise Exception('实际结果[%s]没有包含期望结果[%s]' % (result, expected))


def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)

def locatedir(pattern, root=os.curdir):
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for dirname in fnmatch.filter(dirs, pattern):
            yield os.path.join(path, dirname)

def findall(pattern, root=os.curdir):
    configs = []
    for file in locate(pattern, root):
        configs.append(file)
    return configs

def findalldir(pattern, root=os.curdir):
    configs = []
    for dir in locatedir(pattern, root):
        configs.append(dir)
    return configs

def run_cmd2(cmd):
    import subprocess

    p = subprocess.Popen(cmd, shell=True, bufsize=1000, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    (child_stdin, child_stdout_and_stderr) = (p.stdin, p.stdout)
    p.wait()
    raw_lines = child_stdout_and_stderr.readlines()
    return raw_lines


def run_cmd(cmd):
    import subprocess
    pipe = subprocess.Popen(cmd).stdout
    if pipe is not None:
        raw_lines = pipe.readlines()
        lines = [t.strip() for t in raw_lines]
        return lines

# function definitions
def load_properties(filepath):
    propFile = open(filepath, "rU")
    properties = dict()
    for propLine in propFile:
        propDef = propLine.strip()
        if len(propDef) == 0:
            continue
        if propDef[0] in ( '!', '#' ):
            continue
        punctuation = [propDef.find(c) for c in ':= '] + [len(propDef)]
        found = min([pos for pos in punctuation if pos != -1])
        name = propDef[:found].rstrip()
        value = propDef[found:].lstrip(":= ").rstrip()
        properties[name] = value
    propFile.close()
    return properties


def is_host_pingable(host):
    import subprocess

    cmd = ['ping']
    if sys.platform.startswith('win'):
        cmd.extend(['-n', '1', host])
    else:
        cmd.extend(['-c', '1', host])
    ping = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, error = ping.communicate()
    if sys.platform.startswith('win'):
        msg = out.decode('gbk')
        if '100% 丢失' in msg:
            return False
    else:
        msg = out.decode()
        if '100% packet loss' in msg:
            return False
    return True


def test_is_host_pingable():
    host = "www.google.com"
    ret = is_host_pingable(host)
    if not ret:
        print('主机[%s]不能PING到！' % host)


from datetime import timedelta, datetime
import poplib


def parse_date(date):
    from datetime import datetime

    try:
        # 'Tue, 2 Aug 2011 03:54:25 -0700'
        date_object = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
        # print(date_object.strftime('%a, %d %b %Y %H:%M:%S %z'))
    except ValueError:
        # Tue, 2 Aug 2011 15:32:37 +0000 (UTC)
        # Wed, 3 Aug 2011 00:36:13 +0800 (CST)
        if '(' in date:
            date = date[:date.find('(')].strip()
        date_object = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
        pass
    return date_object


def get_header_value(headers, key):
    for pair in headers:
        if pair[0] == key:
            return pair[1]
    return None


def get_pop3_conn(email, password):
    username, host = email.split('@')
    pop3_host = {'163.com': ('pop3.163.com', True), 'che08.com': ('mail.che08.com', False)}
    host, ssl = pop3_host[host]
    if ssl:
        pop_conn = poplib.POP3_SSL(host)
    else:
        pop_conn = poplib.POP3(host)
    pop_conn.user(username)
    pop_conn.pass_(password)
    return pop_conn


def get_pop3_email_activation_url(email, password):
    from email import parser, header

    activeUrl = None
    pop_conn = get_pop3_conn(email, password)

    #Get messages from server:
    lists = pop_conn.list()
    total = len(lists[1]) + 1
    to_msg_index = max(total - 3, 0)
    for i in range(total, to_msg_index, -1):
        try:
            message = pop_conn.retr(i)
            content = '\n'.join([l.decode() for l in message[1]])
            message = parser.Parser().parsestr(content)
            sent_date = parse_date(get_header_value(message._headers, 'Date'))
            delta = datetime.now() - sent_date.replace(tzinfo=None)
            if delta.total_seconds() < 60:
                # 只关注最近几分钟内收到的邮件
                subject = header.decode_header(get_header_value(message._headers, 'Subject'))
                subject = subject[0][0].decode(subject[0][1])
                print(subject)
                type = message.get_content_charset()
                payload = message.get_payload(decode='base64').decode(type)

                import re

                match = re.match('.*<a href="(.*)".*', payload)
                if match:
                    activeUrl = match.groups(0)[0]
                    break
            else:
                break
        except poplib.error_proto as msg:
            if b'-ERR not that many messages' in msg.args[0]:
                pass
    pop_conn.quit()

    return activeUrl


def get_pop3_email_activation_code(email, password):
    active_url = get_pop3_email_activation_url(email, password)
    if active_url:
        code = active_url.split('/')[-1]
    return code

import ctypes

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE= -11
STD_ERROR_HANDLE = -12

FOREGROUND_BLACK = 0x0
FOREGROUND_BLUE = 0x01 # text color contains blue.
FOREGROUND_GREEN= 0x02 # text color contains green.
FOREGROUND_RED = 0x04 # text color contains red.
FOREGROUND_INTENSITY = 0x08 # text color is intensified.

BACKGROUND_BLUE = 0x10 # background color contains blue.
BACKGROUND_GREEN= 0x20 # background color contains green.
BACKGROUND_RED = 0x40 # background color contains red.
BACKGROUND_INTENSITY = 0x80 # background color is intensified.

class Color:
    ''''' See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
    for information on Windows APIs.'''
    if platform_system =='Windows':
        std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    else:
        std_out_handle=""

    def set_cmd_color(self, color, handle=std_out_handle):
        """(color) -> bit
        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        """
        if platform_system =='Windows':
            bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
            return bool

    def reset_color(self):
        if platform_system =='Windows':
            self.set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)
        else:
            pass

    def print_red_text(self, print_text):
        if platform_system =='Windows':
            self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
            print (print_text  )
            self.reset_color()
        else:
            pass

    def print_green_text(self, print_text):
        if platform_system =='Windows':
            self.set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
            print (print_text  )
            self.reset_color()
        else:
            pass

    def print_blue_text(self, print_text):
        if platform_system =='Windows':
            self.set_cmd_color(FOREGROUND_BLUE | FOREGROUND_INTENSITY)
            print (print_text  )
            self.reset_color()
        else:
            pass

    def print_red_text_with_blue_bg(self, print_text):
        if platform_system =='Windows':
            self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY| BACKGROUND_BLUE | BACKGROUND_INTENSITY)
            print (print_text  )
            self.reset_color()
        else:
            pass

def current_path():  
    path=os.path.realpath(sys.path[0])  
    if os.path.isfile(path):  
        path=os.path.dirname(path)  
        return os.path.abspath(path)  
    else:  
        caller_file=inspect.stack()[1][1]  
        return os.path.abspath(os.path.dirname(caller_file))  

def setup_package(package):
    curdir = current_path()
    todir = package
    if os.path.isabs(package) is False:
        todir = '..\\external\\' + package + '\\'
    os.chdir(todir)
    cmd = 'python setup.py install'
    lines = run_cmd(cmd)
    print('\n'.join(lines))
    os.chdir(curdir)

if __name__ == '__main__':
    #code = get_pop3_email_activation_code('carsmart2011@163.com', '2011carsmart')
    #print('收到激活码：%s' % code)
    setup_package('')