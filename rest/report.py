# coding: utf8
import os
import logging
import datetime
import time
import rath
import utils

clr=utils.Color()

class Stat(object):
    def __init__(self):
        self.success = 0
        self.skip = 0
        self.fail = 0
        self.skip_cases=[]
        self.failed_cases = []
        self.passed_cases = []
        self.message = None

    def __repr__(self):
        return str(self.__dict__)

    def default(self):
        return str(self.__dict__)


class FileStat(Stat):
    def __init__(self):
        Stat.__init__(self)
        self.ignore = None
        self.loginSuccess = None
        self.logoutSuccess = None

    def merge(self, stat):
        self.success = stat.success
        self.failed_cases = stat.failed_cases
        self.passed_cases = stat.passed_cases
        self.skip_cases=stat.skip_cases
        self.skip = stat.skip
        self.fail = stat.fail


def calc_total(stats):
    totalSuccess = sum([stats[s].success for s in stats])
    totalFailure = sum([stats[s].fail for s in stats])
    totalSkip = sum([stats[s].skip for s in stats])
    total = totalSuccess + totalFailure + totalSkip
    successPercent = 0
    failuePercent = 0
    skipPercent = 0
    if total != 0:
        successPercent = totalSuccess / total * 100
        failuePercent = totalFailure / total * 100
        skipPercent = totalSkip / total * 100
    return totalSuccess, successPercent, totalFailure, failuePercent, totalSkip, skipPercent

def to_console(stats):
    totalSuccess, successPercent, totalFailure, failuePercent, totalSkip, skipPercent = calc_total(stats)
    lines = []
    messages = {None: '', True: 'pass', False: 'fail'}
    lines.extend(['casefile                      \tlogin\tlogout\tsuccess        \tfailure        \tskip'])
    for s in stats:
        lines.extend(['%-30s\t%-5s\t%-6s\t%-15s\t%-15s\t%s' % (os.path.basename(s), messages[stats[s].loginSuccess],
                                                               messages[stats[s].logoutSuccess], stats[s].success,
                                                               stats[s].fail, stats[s].skip)])

    lines.extend(['',
                  '合计: success: %d (%.1f%%)\t\tfailure: %d (%.1f%%)\t\tskip: %d (%.1f%%)' %
                  (totalSuccess, successPercent, totalFailure, failuePercent, totalSkip, skipPercent)])
    endtime = time.time()
    lines.extend(['', '自动化测试运行总时间为:%.2f 秒' % (endtime - rath.starttime)])

    for s in stats:

        if len(stats[s].skip_cases) > 0:
            lines.extend(['略过用例总数为 %d：测试文件是：%s' %(totalSkip,s)])
            for case_id, description,url,method,status,ms in stats[s].skip_cases:
                lines.extend(['%-40s %s' % ((case_id), description)])

        if len(stats[s].failed_cases) > 0:
            lines.extend(['失败用例总数为 %d：测试文件是：%s' %((totalFailure),s)])
            for case_id, description,url,method,status,ms,failed_status in stats[s].failed_cases:
                lines.extend(['%-40s %s' % (case_id, description)])


        if totalSuccess==1:
                no=(stats[s].passed_cases[0][0].split(':')[1])
                desc=stats[s].passed_cases[0][1]
                url=stats[s].passed_cases[0][2]
                method=stats[s].passed_cases[0][3]
                exectime=stats[s].passed_cases[0][5]
                lines.extend(['',"用例编号为: %s,描述是：%s, URL是 %s, 方法是: %s 执行时间为: %s 毫秒 "%(no,desc,url, method,exectime)])
                clr.print_green_text('用例执行正确')
        if totalFailure==1:
                no=(stats[s].failed_cases[0][0].split(':')[1])
                url=stats[s].failed_cases[0][2]
                method=stats[s].failed_cases[0][3]
                lines.extend(['',"用例编号为: %s, URL是 %s, 方法是: %s "%(no,url,method)])


    return lines

logger = logging.getLogger("test.rest.report")

def console(resource, stats, host):
    logger.info('接口测试报告 (%s)- %s ' % (host, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    logger.info('\n' + '\r\n'.join(to_console(stats)))

if __name__ == '__main__':
    host='127.0.0.1'
