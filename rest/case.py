# coding: utf8
#!/usr/local/bin/python3.2


import xml.etree.ElementTree as etree
import os
import re
import logging
import json
import copy
import utils

logger = logging.getLogger("test.rest.case")
INIT_FLAG = False
clr=utils.Color()

def realize_string(str, env):
    temp = str
    ret = str
    while True:
        m = re.match(r'.*\$\{(.+)\}.*', temp);
        if m is not None:
            val = m.group(1)
            if env.__contains__(val):
                temp = temp.replace('${%s}' % val, env[val])
                ret = ret.replace('${%s}' % val, env[val])
            else:
                temp = temp.replace('${%s}' % val, '')
        else:
            break
    return ret


class TestcaseBase(object):
    def __repr__(self):
        return str(self.__dict__)

    def default(self):
        return str(self.__dict__)


class Part(TestcaseBase):
    def __init__(self):
        self.key = None
        self.contentType = None
        self.text = None
        self.type = 'string'

    def parse(self, node):
        self.key = node.attrib['key']
        if node.attrib.__contains__('contentType'):
            self.contentType = node.attrib['contentType']
        else:
            self.contentType = None
        self.text = node.text.strip()
        self.type = 'string'
        if node.attrib.__contains__('type'):
            self.type = node.attrib['type']
        return self


class Testcase(TestcaseBase):
    def __init__(self):
        self.id = None

        self.tag = None
        self.refId = None
        self.priority = None
        self.description = None
        self.manual = False
        self.skip = False

        self.url = None

        self.pathArgs = None
        self.bodyText = None
        self.bodyParts = None
        self.bodyArgs = None
        self.headers = {}
        self.method = 'get'
        self.args = None

        self.expStatus = 200
        self.expStatusEqual = True
        self.expBody = None
        self.expBodyHaves = None
        self.expSqls = None

        self.preCommands = None
        self.postCommands = None
        self.context = {}

        self.type = 'rest'

        self.reference = None
        self.group=None
        self.version =None
        self.action =None
        self.host=None
        self.zkHost = None

        #self.module = None
        # self.requestType = None
        # self.responseType = None
        #
        # self.ngLabel = None
        # self.ngVersion = '0.0.1'
        # self.action = None
        # self.actVersion = '0.0.1'

        self.sqls = None
        self.userName = 'root'
        self.pwd = 'clt'
        self.schema = None
        self.dbPath = None
        self.sqlContent = None

        self.chksqls = None
        self.chksql = None
        self.cmd = None
        self.chkdb = None
        self.cmp = None
        self.chkusr = 'root'
        self.chkpwd = 'clt'
        self.chkschema = None
        self.expResult = None



        self.includes = None
        self.include = None
        self.src = None

        # add checkjson
        self.checkjsons=None
        self.checkjson=None
        self.jsonkey=None
        self.expJson=None


    def parse(self, test, node):
        if node.attrib.__contains__('id'):
            self.id = node.attrib['id']
        if node.attrib.__contains__('priority'):
            self.priority = node.attrib['priority']
        if node.attrib.__contains__('description'):
            self.description = node.attrib['description']
        if node.attrib.__contains__('skip'):
            self.skip = node.attrib['skip'] == 'true'
        if node.attrib.__contains__('manual'):
            self.manual = node.attrib['manual'] == 'true'
        if node.attrib.__contains__('tag'):
            self.tag = node.attrib['tag']
        if node.attrib.__contains__('type'):
            self.type = node.attrib['type']

        if node.attrib.__contains__('userName'):
            self.userName = node.attrib['userName']
        if node.attrib.__contains__('pwd'):
            self.pwd = node.attrib['pwd']
        if node.attrib.__contains__('schema'):
            self.schema = node.attrib['schema']
        if node.attrib.__contains__('host'):
            self.dbPath = node.attrib['host']
        if node.attrib.__contains__('cmd'):
            self.cmd = node.attrib['cmd']
        if node.attrib.__contains__('cmp'):
            self.cmp = node.attrib['cmp']
        if node.attrib.__contains__('chkdb'):
            self.chkdb = node.attrib['chkdb']
        if node.attrib.__contains__('chkusr'):
            self.chkusr = node.attrib['chkusr']
        if node.attrib.__contains__('chkpwd'):
            self.chkpwd = node.attrib['chkpwd']
        if node.attrib.__contains__('chkschema'):
            self.chkschema = node.attrib['chkschema']
        #add checkjson
        if node.attrib.__contains__('jsonkey'):
            self.jsonkey=node.attrib['jsonkey']
            try :
                self.expJson=node.text.strip()
            except :
                caseseq=test.cases.__len__()+1
                logger.error("%s文件中的第%d个case格式有错误"%(test.filename,caseseq))
        ##
        if node.attrib.__contains__('src'):
            self.src = node.attrib['src']

        self.sqls = self.parse_sqls(test, node, 'pre/sql')
        if (node.attrib.__contains__('schema')):
            self.sqlContent = node.text.strip()

        if node.attrib.__contains__('chkschema'):
            self.expResult = node.text.strip()

        self.preCommands = self.parse_pre_post(test, node, 'pre/command')

        if (node.find('url') is not None):
            try:
                self.url = node.find('url').text.strip()
            except :
                caseseq=test.cases.__len__()+1
                logger.error("%s文件中的第%d个case格式有错误"%(test.filename,caseseq))
        else:
            self.url = None
        self.pathArgs = None
        if node.findall('path-args/arg') is not None:
            self.pathArgs = {}
            for a in node.findall('path-args/arg'):
                if a.text is not None:
                    self.pathArgs[a.attrib['name']] = a.text.strip()
        self.method = 'get'
        if (node.find('method') is not None):
                self.method = node.find('method').text.strip()
        self.bodyText = ''
        if (node.find('body') is not None):
            if node.find('body').text is not None:
                self.bodyText = node.find('body').text.strip()
            if len(self.bodyText.strip()) == 0:
                self.bodyText = None
        self.bodyParts = None
        if node.findall('body/part') is not None:
            self.bodyParts = []
            for a in node.findall('body/part'):
                self.bodyParts.append(Part().parse(a))
        self.bodyArgs = None
        if node.findall('body/args/arg') is not None:
            self.bodyArgs = {}
            for a in node.findall('body/args/arg'):
                if a.text is None:
                    continue
                type = None
                if a.attrib.__contains__('type'):
                    type = a.attrib['type']
                if type is None or type != 'json':
                    self.bodyArgs[a.attrib['name']] = a.text.strip()
                else:
                    self.bodyArgs[a.attrib['name']] = json.loads(a.text.strip())
            if len(self.bodyArgs) == 0:
                self.bodyArgs = None

        self.expSqls = None
        if node.findall('expect/checksqls/checksql') is not None:
            self.expSqls = []
            for a in node.findall('expect/checksqls/checksql'):
                cmd = ChkSql()
                cmd.parse(test, a)
                self.expSqls.append(cmd)
            if len(self.expSqls) == 0:
                self.expSqls = None
        # add checkjson
        if node.findall('expect/checkjsons/checkjson') is not None:
            self.expJsons=[]
            for a in node.findall('expect/checkjsons/checkjson'):
                jsonkey=ChkJson()
                jsonkey.parse(test,a)
                self.expJsons.append(jsonkey)
            if len(self.expJsons)==0:
                self.expJsons=None
        ##

        self.args = None
        if node.findall('args/arg') is not None:
            self.args = {}
            for a in node.findall('args/arg'):
                type = None
                if a.attrib.__contains__('type'):
                    type = a.attrib['type']
                if type is None or type != 'json':
                    if a.text is None:
                        self.args[a.attrib['name']] = ''
                    else:
                        self.args[a.attrib['name']] = a.text.strip()
                else:
                    self.args[a.attrib['name']] = json.loads(a.text.strip())

        self.headers = {}
        if node.findall('headers/header') is not None:
            self.headers = {}
            for a in node.findall('headers/header'):
                self.headers[a.attrib['name']] = a.text.strip()
        if self.type == 'rpc':
            if self.url is None:
                self.url = 'http://${host.ip}/dubbotest/directproxy'

            self.method = 'post'
            self.group = node.find('rpc/group').text
            self.action = node.find('rpc/action').text
            self.version = node.find('rpc/version').text
            self.reference = node.find('rpc/reference').text
            if  node.find('rpc/host') is not None:
                self.host = node.find('rpc/host').text
            if  node.find('rpc/zkHost') is not None:
                self.zkHost = node.find('rpc/zkHost').text

        self.postCommands = self.parse_pre_post(test, node, 'post/command')

        self.expStatus = 200
        if (node.find('expect/status') is not None):
            nodeStatus = node.find('expect/status')
            try:
                self.expStatus = nodeStatus.text.strip()
            except:
                clr.print_red_text("用例:%s status值不正确，请检查"%(self.id))
                exit(1)
            self.expStatusEqual = True
            if nodeStatus.attrib.__contains__('equal'):
                self.expStatusEqual = nodeStatus.attrib['equal'] == 'true'
        self.expBody = None
        if (node.find('expect/body') is not None):
            expBody = node.find('expect/body').text.strip()
            if len(expBody) != 0:
                self.expBody = expBody

        self.expBodyHaves = []
        if node.findall('expect/body/has') is not None:
            for a in node.findall('expect/body/has'):
                if a.text is not None:
                    self.expBodyHaves.append(a.text.strip())

        self.validate()

        return self

    def parse_pre_post(self, test, node, path):
        commands = None
        if node.findall(path) is not None:
            commands = []
            for a in node.findall(path):
                cmd = None
                if a.attrib.__contains__('ref'):
                    cmd_id = a.attrib['ref']
                    cmd = test.get_command(cmd_id)
                    cmd.refId = cmd_id
                else:
                    cmd = Command()
                    cmd.parse(test, a)
                commands.append(cmd)
        return commands


    def parse_sqls(self, test, node, path):
        sqls = None
        if node.findall(path) is not None:
            sqls = []
            for a in node.findall(path):
                cmd = None
                if a.attrib.__contains__('ref'):
                    cmd_id = a.attrib['ref']
                    cmd = test.get_sql(cmd_id)
                    cmd.refId = cmd_id
                else:
                    cmd = Sql()
                    cmd.parse(test, a)
                sqls.append(cmd)
        return sqls


    def validate(self):
        if self.bodyArgs is not None and self.bodyText is not None:
            raise Exception("测试用例的body内的文本内容和args不能同时存在。%s" % self)


class Command(Testcase):
    def __init__(self):
        Testcase.__init__(self)


class Login(Testcase):
    def __init__(self):
        Testcase.__init__(self)


class Logout(Testcase):
    def __init__(self):
        Testcase.__init__(self)


class Sql(Testcase):
    def __init__(self):
        Testcase.__init__(self)


class ChkSql(Testcase):
    def __init__(self):
        Testcase.__init__(self)

class ChkJson(Testcase):
    def __init__(self):
        Testcase.__init__(self)

class Include(Testcase):
    def __init__(self):
        Testcase.__init__(self)


class Test(TestcaseBase):
    def __init__(self):
        self.commands = []
        self.cases = None
        self.login = None
        self.logout = None
        self.enabled = True
        self.filename = None
        self.sqls = []
        self.expSqls = []

    def contains_command(self, command_id):
        for command in self.commands:
            if command.id == command_id:
                return True
        return False

    def get_command(self, command_id):
        for command in self.commands:
            if command.id == command_id:
                return copy.deepcopy(command)
        raise Exception('id为[%s]的command不存在！请检查其正确性。' % command_id)

    def contains_sql(self, sql_id):
        for sql in self.sqls:
            if sql.id == sql_id:
                return True
        return False

    def get_sql(self, sql_id):
        for sql in self.sqls:
            if sql.id == sql_id:
                return copy.deepcopy(sql)
        raise Exception('id 为[%s]的sql不存在！请检查其正确性。' % sql_id)

    def get_sqls(self):
        return self.sqls

    def parse(self, filename, node):
        self.filename = filename
        self.commands = []
        self.sqls = []
        if (node.find('includes/include') is not None):
            for a in node.findall('includes/include'):
                if INIT_FLAG == False:
                    object = None
                include = Include()
                include.parse(self, a)
                path = include.src
                object = includedXML(self, path)
                if object is not None:
                    if object.sqls.__len__() != 0:
                        self.sqls.extend(object.sqls)
                    if object.commands.__len__() != 0:
                        self.commands.extend(object.commands)

        if (node.find('sqls/sql') is not None):
            for a in node.findall('sqls/sql'):
                sql = Sql()
                sql.parse(self, a)
                if self.contains_sql(sql.id) == True:
                    raise Exception('Duplicated sql id [%s] in test commands is found.' % sql.id)
                sql.refId = sql.id
                self.sqls.append(sql)

        if (node.find('commands/command') is not None):
            for a in node.findall('commands/command'):
                cmd = Command()
                cmd.parse(self, a)
                if self.contains_command(cmd.id) == True:
                    raise Exception('Duplicated commond id [%s] in test commands is found.' % cmd.id)
                cmd.refId = cmd.id
                self.commands.append(cmd)

        self.cases = []
        if node.attrib.__contains__('enabled') and node.attrib['enabled'] == 'true':
            self.enabled = True
        else:
            self.enabled = False

        if (node.find('login') is not None):
            self.login = Login().parse(self, node.find('login'))

        if (node.find('logout') is not None):
            self.logout = Logout().parse(self, node.find('logout'))

        for i in node.findall('testcase'):
            case = Testcase().parse(self, i)
            self.cases.append(case)
        return self

    def includeparse(self, filename, node):
        self.filename = filename
        global INIT_FLAG
        if INIT_FLAG == False:
            self.commands = []
            self.sqls = []
            self.cases = []
            INIT_FLAG = True
        if (node.find('sqls/sql') is not None):
            for a in node.findall('sqls/sql'):
                sql = Sql()
                sql.parse(self, a)
                if self.contains_sql(sql.id) == True:
                    raise Exception('Duplicated sql id [%s] in test commands is found.' % sql.id)
                sql.refId = sql.id
                self.sqls.append(sql)

        if (node.find('commands/command') is not None):
            for a in node.findall('commands/command'):
                cmd = Command()
                cmd.parse(self, a)
                if self.contains_command(cmd.id) == True:
                    raise Exception('Duplicated commond id [%s] in test commands is found.' % cmd.id)
                cmd.refId = cmd.id
                self.commands.append(cmd)

        if node.attrib.__contains__('enabled') and node.attrib['enabled'] == 'true':
            self.enabled = True
        else:
            self.enabled = False

        if (node.find('login') is not None):
            self.login = Login().parse(self, node.find('login'))

        if (node.find('logout') is not None):
            self.logout = Logout().parse(self, node.find('logout'))

        for i in node.findall('testcase'):
            case = Testcase().parse(self, i)
            self.cases.append(case)

        return self


    def add_child_element(self, parentE, child_tag, child_text):
        childE = etree.Element(child_tag)
        childE.text = child_text
        parentE.append(childE)
        return childE

    def add_attribute(self, parentE, name, value):
        if value is not None:
            if type(value) is type(False):
                if value:
                    parentE.set(name, 'true')
                else:
                    parentE.set(name, 'false')
            else:
                parentE.set(name, value)

    def add_headers(self, parentE, headers):
        if headers is not None and len(headers) > 0:
            headersE = self.add_child_element(parentE, 'headers', None)
            for header_name in headers:
                if header_name in 'Content-Length' or header_name in 'User-Agent':
                    pass
                else:
                    headerE = self.add_child_element(headersE, 'header', headers[header_name])
                    headerE.set('name', header_name)
            return headersE

    def add_args(self, parentE, args, args_tag):
        if args is not None and len(args) > 0:
            argsE = self.add_child_element(parentE, args_tag, None)
            for arg_name in sorted(args):
                arg = args[arg_name]
                type_attr = None
                if type(arg) is type(''):
                    text = arg
                else:
                    type_attr = 'json'
                    text = json.dumps(arg)
                    print(text)
                argE = self.add_child_element(argsE, 'arg', text)
                if type_attr is not None:
                    argE.set('type', type_attr)
                argE.set('name', arg_name)
            return argsE

    def ensure_element_existed(self, parentE, child_tag):
        childE = parentE.find(child_tag)
        if childE is None:
            childE = self.add_child_element(parentE, child_tag, None)
        return childE

    def build_case_insider(self, case, caseE):
        self.add_attribute(caseE, 'id', case.id)
        self.add_attribute(caseE, 'priority', case.priority)
        self.add_attribute(caseE, 'description', case.description)
        if case.skip:
            self.add_attribute(caseE, 'skip', case.skip)
        if case.manual:
            self.add_attribute(caseE, 'manual', case.manual)
        self.add_attribute(caseE, 'tag', case.tag)

        if case.preCommands is not None and len(case.preCommands) > 0:
            presE = self.add_child_element(caseE, 'pre', None)
            for c in case.preCommands:
                commandE = self.add_child_element(presE, 'command', None)
                commandE.set('ref', c.refId)

        self.add_child_element(caseE, 'url', case.url)
        if case.pathArgs is not None and len(case.pathArgs) > 0:
            self.add_args(caseE, case.pathArgs, 'path-args')
        self.add_child_element(caseE, 'method', case.method)

        if case.bodyText is not None:
            bodyE = self.ensure_element_existed(caseE, 'body')
            bodyE.text = case.bodyText

        if case.bodyParts is not None and len(case.bodyParts) > 0:
            bodyE = self.ensure_element_existed(caseE, 'body')
            for part in case.bodyParts:
                partE = self.add_child_element(bodyE, 'part', part.text)
                self.add_attribute(partE, 'key', part.key)
                self.add_attribute(partE, 'contentType', part.contentType)
                self.add_attribute(partE, 'type', part.type)

        if case.bodyArgs is not None and len(case.bodyArgs) > 0:
            bodyE = self.ensure_element_existed(caseE, 'body')
            self.add_args(bodyE, case.bodyArgs, 'args')

        if case.args is not None and len(case.args) > 0:
            self.add_args(caseE, case.args, 'args')

        self.add_headers(caseE, case.headers)

        if case.postCommands is not None and len(case.postCommands) > 0:
            presE = self.add_child_element(caseE, 'post', None)
            for c in case.postCommands:
                commandE = self.add_child_element(presE, 'command', None)
                commandE.set('ref', c.refId)

        expectE = self.add_child_element(caseE, 'expect', None)
        expStatusE = self.add_child_element(expectE, 'status', case.expStatus)
        if case.expStatusEqual == False:
            expStatusE.set('equal', 'false')
        if case.expBody is not None:
            expBodyE = self.ensure_element_existed(expectE, 'body')
            expBodyE.text = case.expBody

        if case.expBodyHaves is not None and len(case.expBodyHaves) > 0:
            expBodyE = self.ensure_element_existed(expectE, 'body')
            for has in case.expBodyHaves:
                hasE = self.add_child_element(expBodyE, 'has', has)

    def to_xml(self, cases=None):
        if cases is None:
            cases = self.cases
        rootE = etree.Element('rest-testcases')
        self.add_attribute(rootE, 'enabled', self.enabled)
        if self.login is not None:
            loginE = self.add_child_element(rootE, 'login', None)
            self.build_case_insider(self.login, loginE)

        if len(self.commands) > 0:
            commandsE = self.add_child_element(rootE, 'commands', None)
            for command in self.commands:
                commandE = self.add_child_element(commandsE, 'command', None)
                self.build_case_insider(command, commandE)
                commandE.set('id', command.refId)

        if len(cases) > 0:
            for case in cases:
                caseE = self.add_child_element(rootE, 'testcase', None)
                self.build_case_insider(case, caseE)

        if self.logout is not None:
            logoutE = self.add_child_element(rootE, 'logout', None)
            self.build_case_insider(self.logout, logoutE)

        return rootE

    def to_xml_string(self, rootE):
        import xml.dom.minidom as minidom

        rough_string = etree.tostring(rootE, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml = reparsed.toprettyxml(indent="    ", encoding="utf-8")
        return xml.decode()

    def save(self, filename, rootE=None):
        if rootE is None:
            rootE = self.to_xml()
        xml = self.to_xml_string(rootE)

        file = open(filename, 'w', encoding="utf-8")
        file.write(xml)
        file.close();

    def realize(self, env):
        if self.login is not None:
            self.realize_case(self.login, env)

        if self.logout is not None:
            self.realize_case(self.logout, env)

        for c in self.cases:
            self.realize_case(c, env)

    def realize_case(self, case, env):
        try:
            temp = realize_string(case.url, env)
            case.url = temp
            if case.pathArgs is not None:
                case.url = realize_string(case.url, case.pathArgs)

            if case.preCommands is not None:
                for cmd in case.preCommands:
                    self.realize_case(cmd, env)
            if case.postCommands is not None:
                for cmd in case.postCommands:
                    self.realize_case(cmd, env)
        except TypeError as msg:
            if case.url is None:
                message = '用例编号为[%s] url为空，错误信息为%s' % (case.id, msg)
                logger.error(message)
            else:
                message = '用例编号为[%s]格式不对，错误信息为%s' % (case.id, msg)
                logger.error(message)

    def get_duplicated_case_unique_ids(self):
        existed = {}
        duplicated_ids = []
        if self.cases:
            for case in self.cases:
                if existed.__contains__(case.id) == True:
                    duplicated_ids.append(self.get_case_unique_id(case.id))
                else:
                    existed[case.id] = case
        return duplicated_ids

    def get_case_unique_id(self, case_id):
        return '%s:%s' % (self.filename, case_id)

    def get_case(self, case_id):
        if self.cases:
            for case in self.cases:
                if case.id == case_id:
                    yield case


def parse(path, env):
    object = None
    try:
        tree = etree.parse(path)
        root = tree.getroot()
        object = Test().parse(os.path.basename(path), root)
        object.realize(env)
    except IOError as msg:
        message = '测试文件[%s]的XML读取失败。错误消息：%s' % (path, msg)
        logger.error(message)
    except etree.ParseError as msg:
        message = '测试文件[%s]的XML格式不正确。错误消息：%s' % (path, msg)
        logger.error(message)
    return object


def includedXML(self, path):
    global INIT_FLAG
    if INIT_FLAG == False:
        object = None
    try:
        tree = etree.parse(path)
        root = tree.getroot()
        if path.find('/'):
            object = Test().includeparse(os.path.basename(path), root)
        else:
            object = Test().includeparse(path, root)
    except IOError as msg:
        message = '测试文件[%s]的XML读取失败。错误消息：%s' % (path, msg)
        logger.error(message)
    except etree.ParseError as msg:
        message = '测试文件[%s]的XML格式不正确。错误消息：%s' % (path, msg)
        logger.error(message)
    return object


if __name__ == '__main__':
    INIT_FLAG == False
    env = {'host.ip': '10.21.0.147', 'database.url': '10.23.102.33'}
    #test = parse('./cases/CDT-rest-test/cdt-rest-content_manage-zz.xml', env)
    test = parse('./cases/cdt-rest-test-debug.xml', env)
    #test = parse('./cases/auto-test-debug.xml', env)
    for c in test.get_case('3001'):
        print(c)
    test.save('fuzz-1.xml')
  #  test2 = parse('./fuzz-1.xml', env)
   # test2.save('fuzz-2.xml')
    #test3 = parse('./fuzz-2.xml', env)
    #test3.save('fuzz-3.xml')

