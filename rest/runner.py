# coding: utf8
#!/usr/local/bin/python3.2


import restclient
import case
import logging
import logging.config
import utils
import report
import os
import urllib
import json
import re
from dubbo import ZookeeperRegistry,DubboClient
# import fuzzmock
import time
from datetime import  datetime



if utils.getPythonVersion() == '2':
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')


logger = logging.getLogger("test.rest.runner")
clr=utils.Color()
def get_body(case):
    body = None
    if case.bodyText is not None:
        body = case.bodyText#.encode('UTF-8')
    elif case.bodyArgs is not None:
        if case.headers.__contains__('Content-Type') and 'x-www-form-urlencoded' in case.headers['Content-Type']:
            if utils.getPythonVersion() == '2':
                body = urllib.urlencode(case.bodyArgs)
            else:
                body = urllib.parse.urlencode(case.bodyArgs)
        if case.headers.__contains__('Content-Type') and 'json' in case.headers['Content-Type']:
            body = json.dumps(case.bodyArgs)
    return body


def postcase(case,sso_cookie):
    body = get_body(case)
    headers = case.headers
    if case.type == 'rest':
        resp = restclient.post(case.url, sso_cookie, body=body, args=case.args, parts=case.bodyParts, headers=headers)
    elif case.type == 'rpc':
        resp = rpc_post(case, sso_cookie, body)
    else:
        raise Exception('unkown case type %s' % case)
    return resp

def rpc_post(case,sso_cookie,body ):
    rpcbody = {}
    if case.zkHost is not None:
         registry = ZookeeperRegistry(case.zkHost)
         user_provider = DubboClient(case.reference, registry,group=case.group,version=case.version)
         hosts = registry.get_provides(case.reference, group=case.group,version=case.version)
         if len(hosts) < 1:
             raise Exception('zookeeper查询不到该服务的注册信息' % case)
         host = list(hosts.keys())[0]
         rpcbody['reference'] = 'dubbo://{0}/{1}'.format(host,case.reference)
    elif case.host is not None:
        rpcbody['reference'] = 'dubbo://{0}/{1}'.format(case.host,case.reference)
    else:
        raise Exception('rpc case zkhost 和 host 至少包含一个' % case)

    rpcbody['data'] = body#.decode("utf-8")
    rpcbody['version']=case.version
    rpcbody['group'] = case.group
    #rpcbody['reference'] = case.reference
    rpcbody['action'] = case.action
    return restclient.post(case.url, sso_cookie, body=str(rpcbody).encode("utf-8"), args=case.args, parts=case.bodyParts, headers=case.headers)

def putcase(case,sso_cookie):
    body = get_body(case)
    headers = case.headers
    resp = restclient.put(case.url, sso_cookie, body=body, args=case.args, headers=headers)
    return resp


def deletecase(case,sso_cookie):
    body = get_body(case)
    headers = case.headers
    resp = restclient.delete(case.url, sso_cookie, headers=headers)
    return resp


def checkStatusExpect(case, resp):
    if case.expStatusEqual:
       utils.assertEqual(case.expStatus, resp['headers']['status'])
        #utils.assertIn(case.expStatus, resp['headers']['status'])
    else:
        utils.assertNotIn(case.expStatus, resp['headers']['status'])


def checkExpect(case, resp):
    checkStatusExpect(case, resp)

    if case.expBody is not None:
        utils.assertEqual(case.expBody, resp['body'])
    if case.expBodyHaves is not None:
        for i in case.expBodyHaves:
            if i is not None and len(i.strip()) != 0:
                utils.assertContain(i, resp['body'])
            else:
                # 忽略为空的期望值
                pass

def checkJsonExpect(env,case):
    for i in range(len(case.expJsons)):
        casejson=case.expJsons[i]
        logger.info('执行期望Json的key是[%s],value是[%s]'%(casejson.jsonkey,casejson.expJson))
        findjson={}
        findjson[casejson.jsonkey]=casejson.expJson

        within_json=case.context['self']
        checkjson=check_json_returnval(within_json,findjson)
        if checkjson==False :
            logger.error('检查Json返回结果失败')
            raise Exception('检查Json返回结果失败')
        else:
            logger.info('检查Json返回结果成功')

def check_json_returnval(within_json,find_json):
    for find_k,find_v in find_json.items():
        for k,v in within_json.items():
            if isinstance(v,list):
                for l in range(len(v)):
                    for item_k,item_v in v[l].items():
                        if find_k==item_k:
                            m=re.match(find_v,item_v)
                            if m is not None:
                                return True
            else:
                if find_k==k:
                    return True
    return False

def checkBSExpect(env, case):
    if case.expSqls is not None and len(case.expSqls) > 0:
        for i in range(len(case.expSqls)):
            sql = case.expSqls[i]
            logger.info('执行期望SQL[%s]' % (sql.cmd))
            mycon = None
            try:
                if sql.chkdb == None:
                    sql.chkdb = env['db.host']
                mycon = DbConnect(sql.chkdb, sql.chkusr, sql.chkpwd, sql.chkschema)
                resp = mycon.queryTable(sql.cmd)
                logger.debug('实际结果: [%s],期望结果:[%s]' % (resp[0], sql.expResult))
                if sql.cmp is None:
                    utils.assertEqual(sql.expResult, str(resp[0]))
                else:
                    utils.assertCmp(sql.expResult, str(resp[0]), sql.cmp)
            except Exception as msg:
                newMsg = '测试业务数据结果失败。原因:%s' % (msg)
                logger.error(newMsg)
                raise Exception(newMsg)
            finally:
                mycon.close()


def runcommand(case,sso_cookie):
    start_=datetime.utcnow()
    resp = None
    if case.method == 'get':
        if case.args =={}:
            resp = restclient.get(case.url, sso_cookie, case.bodyArgs, case.headers)
        else:
            resp = restclient.get(case.url, sso_cookie, case.args, case.headers)
    elif case.method == 'post':
        resp = postcase(case, sso_cookie)
    elif case.method == 'put':
        resp = putcase(case, sso_cookie)
    elif case.method == 'delete':
        resp = deletecase(case, sso_cookie)
    else:
        raise Exception('不支持的方法 %s。只支持get, post, put' % case.method)

    #强制保留2位
    end_=datetime.utcnow()
    c=(end_-start_)
    #microseconds 微秒 ：1000微秒=1毫秒
    runtime=int(c.microseconds/1000)

   # interface_runtime=(float('%.2lf'%((time.time()-interfaces_runstarttime)*1000)))

    return resp,runtime


def propogate_str(value, context):
    temp = value
    ret = value
    m = re.match(r'.*\$\{(.+)\}.*', temp);
    if m is not None:
        val = m.group(1)
        items = val.split('.')
        if context.__contains__(items[0]):
            set = context[items[0]]
            if set.__contains__(items[1]):
                replacement = set[items[1]]
                if type(replacement) is type(0):
                    replacement = str(replacement)
                temp = temp.replace('${%s}' % val, replacement)
                ret = ret.replace('${%s}' % val, replacement)
            else:
                temp = temp.replace('${%s}' % val, '')

    #while True:
    #    m = re.match( r'.*\$\{(.+)\}.*', temp);
    #   if m is not None:
    #        val = m.group(1)
    #        items = val.split('.')
    #        if not context.__contains__(items[0]):
    #            continue;
    #        set = context[items[0]]
    #        if set.__contains__(items[1]):
    #            replacement = set[items[1]]
    #            if type(replacement) is type(0):
    #                replacement = str(replacement)
    #           temp = temp.replace('${%s}' % val,replacement)
    #            ret = ret.replace('${%s}' % val, replacement)
    #        else:
    #            temp = temp.replace('${%s}' % val, '')
    #    else:
    #        break
    return ret


def propogate_args(args, context):
    for key in args:
        value = args[key]
        if isinstance(value, str) and (value.startswith('${') or value.startswith('[${')):
            m = re.match(r'.*\$\{(.+)\}.*', value);
            if m is not None:
                names = m.group(1)
                items = names.split('.')
                if len(items) != 2:
                    raise Exception('参数引用名是无效的，必须是由.点号区分开的命令名和参数名组成。参数引用[%s]没有包含.点号。' % value)
                if not context.__contains__(items[0]):
                    #raise Exception('测试用例的执行上下文中没有包含名称为[%s]的命令。当前上下文中只有如下命令：[%s]' % (items[0], ', '.join(context.keys())))
                    continue;
                set = context[items[0]]
                if type(set) is type({}):
                    replacement = set[items[1]]
                    if value.startswith('[${'):
                        args[key] = '[' + str(replacement) + ']'
                    else:
                        args[key] = replacement
    return args

def propogate_para(case, context):
    para = case.expResult
    if isinstance(para, str) and (para.startswith('${') or para.startswith('[${')):
        m = re.match(r'.*\$\{(.+)\}.*', para);
        if m is not None:
            names = m.group(1)
            items = names.split('.')
            if len(items) != 2:
                raise Exception('参数引用名是无效的，必须是由.点号区分开的命令名和参数名组成。参数引用[%s]没有包含.点号。' % value)
            if context.__contains__(items[0]):
                set = context[items[0]]
                if type(set) is type({}):
                    replacement = set[items[1]]
                    case.expResult = replacement
    return case.expResult


def propogate_context(caseinstance, context):
    if caseinstance.args is not None:
        caseinstance.args = propogate_args(caseinstance.args, context)
    if caseinstance.pathArgs is not None:
        caseinstance.pathArgs = propogate_args(caseinstance.pathArgs, context)
        if caseinstance.url is not None:
            caseinstance.url = propogate_str(caseinstance.url, context)
    if caseinstance.bodyArgs is not None:
        caseinstance.bodyArgs = propogate_args(caseinstance.bodyArgs, context)

    if caseinstance.expResult is not None:
        caseinstance.expResult = propogate_para(caseinstance, context)

    if caseinstance.preCommands is not None and len(caseinstance.preCommands) > 0:
        for c in caseinstance.preCommands:
            propogate_context(c, context)
    if caseinstance.postCommands is not None and len(caseinstance.postCommands) > 0:
        for c in caseinstance.postCommands:
            propogate_context(c, context)
    if caseinstance.expSqls is not None and len(caseinstance.expSqls) > 0:
        for c in caseinstance.expSqls:
            propogate_context(c, context)


def runcase_pre_command(env, case, sso_cookie):
    runcase_pre_cleanData(env, case)
    if case.preCommands is not None and len(case.preCommands) > 0:
        case.context = {}
        logger.info('执行测试用例[%s]的预置命令。共有[%d]个' % (case.id, len(case.preCommands)))
        #resp从原来的字符串变为tuple，原来的resp，使用现在的resp[0]代替
        for i in range(len(case.preCommands)):
            cmd = case.preCommands[i]
            try:
                resp = runcommand(cmd, sso_cookie)
                if isinstance(resp,tuple):
                    logger.debug('log: %s' % str(resp[0]))
                else:
                    logger.debug('log: %s' % resp)
                checkExpect(cmd, resp[0])
            except Exception as msg:
                newMsg = '测试用例[%s]的预置命令[%s]已失败。[%d]/[%d]。原因:%s' % (
                case.id, cmd.refId, i + 1, len(case.preCommands), msg)
                logger.error(newMsg)
                raise Exception(newMsg)
            logger.info('测试用例[%s]的预置命令[%s]已通过。[%d]/[%d]' % (case.id, cmd.refId, i + 1, len(case.preCommands)))
            if 'application/json' in resp[0]['headers']['content-type']:
                if resp[0]['body'] != '':
                    case.context[cmd.refId] = json.loads(resp[0]['body'])
            if len(case.context) > 0:
                propogate_context(case, case.context)


def runcase_pre_cleanData(env, case):
    if case.sqls is not None and len(case.sqls) > 0:
        case.context = {}
        logger.info('执行测试用例[%s]前，清空垃圾测试数据' % (case.id))
        for i in range(len(case.sqls)):
            sql = case.sqls[i]
            mycon = None
            try:
                if sql.dbPath == None:
                    sql.dbPath = env['db.host']
                mycon = DbConnect(sql.dbPath, sql.userName, sql.pwd, sql.schema)
                mycon.cleanTable(sql.sqlContent)
            except Exception as msg:
                newMsg = '测试用例[%s]清空垃圾数据失败。原因:%s' % (case.id, msg)
                logger.error(newMsg)
                raise Exception(newMsg)
            finally:
                mycon.close()


def runcase_post_command(case, sso_cookie):
    if case.postCommands is not None and len(case.postCommands) > 0:
        logger.info('执行测试用例[%s]的后置命令。共有[%d]个' % (case.id, len(case.postCommands)))
        for i in range(len(case.postCommands)):
            cmd = case.postCommands[i]

            try:
                resp = runcommand(cmd, sso_cookie)
                logger.debug('log: %s' % resp)
                checkExpect(cmd, resp)
            except Exception as msg:
                newMsg = '测试用例[%s]的后置命令[%s]已失败。[%d]/[%d]。原因:%s' % (
                case.id, cmd.refId, i + 1, len(case.postCommands), msg)
                logger.error(newMsg)
                raise Exception(newMsg)

            logger.info('测试用例[%s]的后置命令[%s]已通过。[%d]/[%d]' % (case.id, cmd.refId, i + 1, len(case.postCommands)))


def try_decode(dict):
    new = {}
    for key in dict:
        try:
            new[key] = dict[key].decode('gbk')
        except UnicodeDecodeError as msg:
            new[key] = dict[key].decode('utf-8')
    return new


def log_response(resp):
    if resp['headers'].__contains__('transfer-encoding') and 'chunked' in resp['headers']['transfer-encoding']:
        logger.debug('log-chunked data: %s, %s' % (len(str(resp)), resp['headers']))
    else:
        logger.info('log: %s' % resp)


def runcase_body(env, case, sso_cookie, checkdict,casesort):
    resp,interface_runtime = runcommand(case, sso_cookie)
    #输出日志是字典类型，不是字符串
    log_response(resp)

    if casesort=="single":
        if resp['body']!='':

           print('*'*40+"OutPut Start"+'*'*40)
           try:
               #json需要使用无bom的utf8
               #os.system("chcp 936") # 一般情况下使用
               #os.system("chcp 65001") #由于unicode导致的gbk编码错误情况使用
               jsonstr=to_nomalformat((resp['body']).replace('false','0').replace('true','1').replace('null',"''"))
               jsonformatstr=json.dumps(eval((jsonstr)),sort_keys=True,indent=4,ensure_ascii=False)
               print(jsonformatstr)
               printstatus(resp['headers'].status)
           except Exception as msg:
               print(jsonstr)
               print(msg)
              # print("请在cmd中使用 chcp 936 修改字符编码后重新执行一下")
           finally:
                # os.system("chcp 65001")
                #jsonstr_ok=to_nomalformat((resp['body'])).encode('utf-8').decode('utf-8','ignore')
                #jsonformatstr=json.dumps(eval((jsonstr_ok)),sort_keys=True,indent=4,ensure_ascii=False)
                #print(jsonformatstr)
                #printstatus(resp['headers'].status)
                print('*'*40+"OutPut End"+'*'*40)



    if resp['headers'].__contains__('content-type') and 'application/json' in resp['headers']['content-type'] and len(
            resp['body'].strip()) > 0:
        case.context['self'] = json.loads(resp['body'])
    if len(case.context) > 0:
        propogate_context(case, case.context)
    if checkdict['expjson'] is True:
        checkJsonExpect(env,case)
    if checkdict['expsql'] is True:
        checkBSExpect(env, case)

    checkExpect(case, resp)

    return interface_runtime
def to_nomalformat(strs):

    flag=0
    if 'false' in strs:
        normalstr=strs.replace('false',"'false'")
        flag=1
    if 'true' in strs:
        if flag==1:
            normalstr=normalstr.replace('true',"'true'")
        else:
            normalstr=strs.replace('true',"'true'")
            flag=1
    if 'null' in strs:
        if flag==1:
            normalstr=normalstr.replace('null',"'null'")
        else:
            normalstr=strs.replace('null',"'null'")
            flag=1
    if '（' in strs:
        if flag==1:
            normalstr=normalstr.replace('（',"(")
        else:
            normalstr=strs.replace('（',"(")
    if '）' in strs:
        if flag==1:
            normalstr=normalstr.replace('）',")")
        else:
            normalstr=strs.replace('）',")")
    if '.' in strs:
        if flag==1:
            normalstr=normalstr.replace('.',"'.'")
        else:
            normalstr=strs.replace('.',"'.'")
    if '\u200e' in strs:
        if flag==1:
            pass
        else:
            pass

    if flag==0:
        normalstr=strs
    return  normalstr


def printstatus(status):
    clr=utils.Color()
#    clr=Color()
    if status==200:
        clr.print_green_text("接口返回结果为成功,代码是:"+str(status))
    elif status==400:
       clr.print_red_text("接口返回结果为异常,代码是:"+str(status))
    elif status==401:
       clr.print_red_text("接口返回结果为未授权,代码是:"+str(status))
    elif status==403:
       clr.print_red_text("接口返回结果为禁止,代码是:"+str(status))
    elif status==404:
       clr.print_red_text("接口返回结果为未找到,代码是:"+str(status))
    elif status==500:
       clr.print_blue_text("接口返回结果为服务器内部错误,代码是:"+str(status))


def check_whether_run(env, case):
    supported_methods = ['get', 'post', 'put', 'delete']
    if case.method in supported_methods:
        if env['fuzz'] == False:
            return True
        elif case.tag is not None and 'fuzz' in case.tag:
            return True
        else:
            #logger.debug('忽略测试用例[%s]。用例没有TAG为 [fuzz]。' % (case.id))
            return False
    else:
        logger.warn('不支持的方法 %s。只支持: %s' % (case.method, ','.join(supported_methods)))
        logger.warn('忽略测试用例[%s], [%s]' % (case.id, case))
        return False


def dump_case(env, test, cases):
    for i in range(len(cases)):
        case = cases[i]
        case.id = case.id + '.%d' % (i + 1)
    rootE = test.to_xml(cases)
    filename = './cases-fuzz/fuzz-%s' % os.path.basename(test.filename)
    test.save(filename, rootE)
    logger.info('FUZZ失败的测试用例被保存至: %s' % filename)


def runcase_fuzz(env, test, case, sso_cookie):
    failed_cases = []
    passed_cases = []

    if case.method == 'get':
        runcase_pre_command(env, case, sso_cookie)

    for newCase in fuzzmock.generate(case):
        if case.method != 'get':
            runcase_pre_command(env, newCase, sso_cookie)

        try:
            runcase_body(env, newCase, sso_cookie, False)
            passed_cases.append(newCase)
        except Exception as msg:
            failed_cases.append(newCase)
            logger.error('FUZZ失败:%s。测试用例: %s' % (msg, newCase))
            if env['failfast'] == True:
                raise msg

        if case.method != 'get':
            runcase_post_command(newCase, sso_cookie)

    if case.method == 'get':
        runcase_pre_command(env, case, sso_cookie)

    return failed_cases, passed_cases


def runcase(env, test, case, sso_cookie,casesort):
    if not check_whether_run(env, case):
        return False, None

    passed_cases = []
    if env['fuzz'] == False:
        runcase_pre_command(env, case, sso_cookie)
        checkdict={}

        if case.expSqls==None:
            checkdict['expsql']=False
        else:
            checkdict['expsql']=True
        if case.expJsons==None:
            checkdict['expjson']=False
        else:
            checkdict['expjson']=True



        interface_runtime=runcase_body(env, case, sso_cookie, checkdict,casesort)
        passed_cases.append(case)
        runcase_post_command(case, sso_cookie)
    else:

        failed_cases, passed_cases = runcase_fuzz(env, test, case, sso_cookie)
        if failed_cases is not None and len(failed_cases) > 0:
            return True, failed_cases, passed_cases
        #
    logger.info('测试用例[%s]通过' % case.id)
    return True, None, passed_cases,interface_runtime
def isexistcase(test,case_id):
    testcasecount=test.cases.__len__()
    idcount=[]
    for id in range(0,testcasecount):
        idcount.append(test.cases[id].id)
    if case_id not in idcount:
        clr.print_red_text("未发现id为 %s 的测试用例"%(case_id))
        exit()

def runtest(env, test, sso_cookie, case_id=None, includemanual=False):
    stat = report.Stat()

    total_failed_cases = []
    total_passed_cases = []
    total_skip_cases=[]
    if case_id is not None:
        isexistcase(test,case_id)
    for case in test.cases:
        try:
            if case_id is None:
                if case.manual == True and includemanual == False and case.skip == False:
                    logger.info('case[%s] (manual case) skipped' % test.get_case_unique_id(case.id))
                    stat.skip = stat.skip + 1
                else:
                    if case.skip == False:

                        runned, failed_cases, passed_cases,exectime = runcase(env, test, case, sso_cookie,"multi")

                        if runned == True:
                            total_passed_cases.extend(passed_cases)
                          #  if stat.failed_cases is not None and len(stat.failed_cases) > 0:
                            if failed_cases is not None:
                                if total_failed_cases!=[]:
                                    total_failed_cases.extend(failed_cases)
                                stat.failed_cases.append((test.get_case_unique_id(case.id), case.description))
                                stat.fail = stat.fail + 1
                            else:
                                stat.passed_cases.append((test.get_case_unique_id(case.id), case.description,case.url,case.method,"Pass",exectime))
                                stat.success = stat.success + 1
                        else:
                            stat.skip = stat.skip + 1


                    else:
                        logger.info('case[%s] skipped' % test.get_case_unique_id(case.id))
                        stat.skip_cases.append((test.get_case_unique_id(case.id), case.description,case.url,case.method,"Skip",""))
                        stat.skip = stat.skip + 1
            elif case_id == case.id:
                runned, failed_cases, passed_cases,exectime = runcase(env, test, case, sso_cookie,"single")
                if runned:
                    total_passed_cases.extend(passed_cases)
                    if failed_cases is not None and len(failed_cases) > 0:
                        total_failed_cases.extend(failed_cases)
                        stat.failed_cases.append((test.get_case_unique_id(case.id), case.description))
                        stat.fail = stat.fail + 1
                    else:
                        stat.passed_cases.append((test.get_case_unique_id(case.id), case.description,case.url,case.method,"Pass",exectime))
                        stat.success = stat.success + 1
                else:
                    stat.skip = stat.skip + 1
            else:
                []
                #logger.debug('忽略case.id[%s]。不是期望的:%s' % (case.id, case_id))
        except Exception as msg:
            logger.error('测试用例[%s] %s failed [%s].' % (test.get_case_unique_id(case.id), case.description, msg))
            # write failed case info
            stat.failed_cases.append((test.get_case_unique_id(case.id), case.description,case.url,case.method,"Fail","",msg.args[0]))
            if env['debug']:
                logger.exception(msg)
            stat.fail = stat.fail + 1
            if "unexpected EOF while parsing" in str(msg):
                clr.print_red_text("接口执行失败,请检查配置文件中的Host ip是否正确")


    if len(total_failed_cases) > 0 and env['fuzz']:
        dump_case(env, test, total_failed_cases)

    return stat


def runlogin(file, case, env):
    try:
        resp = postcase(case, None)
        logger.debug(resp)
      #  comment by peterz
      #  checkStatusExpect(case, resp)
        if 'set-cookie-3' in resp.get('headers'):
            sso_cookie = resp['headers']['set-cookie-3']
        else:
            sso_cookie = resp['headers']['set-cookie']
        if sso_cookie is not None:
            logger.info('登录成功：Cookie: %s' % sso_cookie)
            return True, sso_cookie
        else:
            return False, None
    except Exception as msg:
        logger.error('case[%s] failed while login with [%s].' % (file, msg))
        return False, None


def runlogout(file, case, sso_cookie):
    try:
        resp = restclient.get(case.url, sso_cookie, case.args)
        logger.debug(resp)

        checkStatusExpect(case, resp)

        logger.info('退出成功。')
        return True
    except Exception as msg:
        logger.error('case[%s] failed while logout with [%s].' % (case.id, msg))
        return False


def report_duplicated_case_unique_id(test):
    duplicated_ids = test.get_duplicated_case_unique_ids()
    for id in duplicated_ids:
        logger.warn('发现重复的CASE标识: %s。' % id)


def runfile(file, env, checktestonly=False, case_id=None, includemanual=False):
    stat = report.FileStat()
    test = case.parse(file, env)
    if test is None:
        stat.message = '由于加载测试文件失败。取消测试[%s]！' % file
        stat.fail = 1
        stat.failed_cases.append((os.path.basename(file), '加载文件失败'))
        logger.error(stat.message)
        return stat
    if checktestonly is True:
        logger.info('取消测试，仅仅进行测试文件检查。')
        stat.success = 1
        return stat
    report_duplicated_case_unique_id(test)
    if test.enabled == True:
        logger.info('test [%s] executing.' % file)
        sso_cookie = None
        if test.login is not None:
            stat.loginSuccess, sso_cookie = runlogin(file, test.login, env)
        casestat = runtest(env, test, sso_cookie, case_id, includemanual)
        stat.merge(casestat)
        if test.logout is not None:
            stat.logoutSuccess = runlogout(file, test.logout, sso_cookie)
    else:
        logger.info('test [%s] ignored.' % file)
        self.ignore = True
    return stat


def runfiles(env, checktestonly=False, includemanual=False):
    stats = {}
    for file in utils.findall('*rest-test.xml', './cases/'):
        stat = runfile(file, env, checktestonly=checktestonly, includemanual=includemanual)
        stats[file] = stat
    return stats


