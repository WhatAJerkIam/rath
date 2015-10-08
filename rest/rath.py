#coding:utf-8

import time
import os
import logging
import logging.config
import utils
import sys
import report
import runner

try:
    import httplib2
except ImportError as msg:
    import platform
    if platform.system()=="Windows":
        os.chdir('..\\external\\httplib2-0.9.1\\')
        cmd = 'python setup.py install'
        lines = utils.run_cmd(cmd)
        os.chdir('..\\..\\rest\\')



if utils.getPythonVersion() == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')

logger = logging.getLogger("test.rest.rath")
logging.config.fileConfig('./conf/rest-test-log.conf',disable_existing_loggers=False)
starttime = time.time()


def get_log_level(level_name):
    if level_name == 'debug':
        return logging.DEBUG
    if level_name == 'info':
        return logging.INFO
    if level_name == 'warn':
        return logging.WARN
    if level_name == 'error':
        return logging.ERROR

    raise Exception('不支持日志级别：%s' % level_name)


def get_cmd_parser():
    import argparse

    parser = argparse.ArgumentParser(prog='rath.py', description='RESTful接口测试工具RESTful API Test Harness (Rath).')
    parser.add_argument('-p', '--profile', choices=['local', 'dev','test', 'betafunc', 'prod'],
                        help='指定测试运行环境的配置。')
    parser.add_argument('-t', '--testfile', nargs='?',
                        help='指定测试文件。不指定时，对./cases目录下的所有*.xml文件进行测试。指定文件时，例如xxx-rest-test.xml，只对选定的文件进行测试。若指定文件：用例ID时, 例如xxx-rest-test.xml:1，只对特定用例进行测试')
    parser.add_argument('--pinghost', action='store_true', help='是否需要在测试开始之前检查测试主机PING连通性。')
    parser.add_argument('--checktestonly', action='store_true', help='仅仅检查测试XML文件的有效性和合法性。')
    parser.add_argument('--includemanual', action='store_true', help='同时运行手工参与的测试用例。')
    parser.add_argument('--debug', action='store_true', help='调试性输出，含打印异常的调用堆栈。')
    parser.add_argument('--failfast', action='store_true', help='测试出错就暂停。')
    parser.add_argument('-v',action='version',version='2015-08-26 Ver0.99')

    parser.set_defaults(profile='test', loglevel='debug', pinghost=False, checktestonly=False, includemanual=False,
                        debug=False, fuzz=False, failfast=False)
    return parser


def locate_test_file(testfile):
    if os.path.splitext(testfile)[1] in('.xlsx','.xls'):
        cmd="python exceltoxml.py -i "+testfile

        os.system(cmd)
        testfile=os.path.splitext(testfile)[0]+'.xml'
    files = utils.findall(testfile, '.')
    if len(files) == 0:
        logger.error('在当前目录[.]及其子目录下找不到测试文件[%s]。退出测试！' % (testfile))
        return
    elif len(files) > 1:
        logger.error('在当前目录[.]及其子目录下找到多个测试文件[%s]。退出测试！' % (','.join(files)))
        return
    testfile = files[0]
    logger.info('测试文件路径为：%s' % testfile)
    return testfile


def main(args, properties):
    logger.setLevel(get_log_level(args.loglevel))
    if args.pinghost:
        logger.info('检查测试目标主机[%s]的PING连通性。' % properties['host.ip'])
        if not utils.is_host_pingable(properties['host.ip']):
            logger.error('不能PING通所要测试的目标主机[%s]。测试中断！请检查机器IP地址设置，或者目标服务器是否已经启动。' % properties['host.ip'])
            sys.exit()

    stats = {}
    if args.testfile is not None:
        case_id = None
        items = args.testfile.split(':')
        testfile = locate_test_file(items[0])
        if len(items) > 1:
            case_id = items[1]
        
        stat = runner.runfile(testfile, properties, case_id=case_id, checktestonly=args.checktestonly,
                              includemanual=args.includemanual)
        stats[testfile] = stat
    else:
        stats = runner.runfiles(properties, checktestonly=args.checktestonly, includemanual=args.includemanual)

    report.console(None,stats,properties['host.ip'])
if __name__ == '__main__':
    parser = get_cmd_parser()
    args = parser.parse_args(sys.argv[1:])
    properties = utils.load_properties('./conf/test.%s.properties' % args.profile)
    logger.info('运行参数：%s' % args)
    logger.info('测试设置：%s' % properties)
    properties['debug'] = True#args.debug
    properties['fuzz'] = args.fuzz
    properties['failfast'] = args.failfast

    main(args, properties)