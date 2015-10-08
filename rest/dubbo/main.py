from registry import ZookeeperRegistry
from rpclib import DubboClient
from rpcerror import DubboClientError

if __name__ == '__main__':
    print('test start')
    registry = ZookeeperRegistry('172.24.2.35:2181')
    #registry.subscribe('com.wangyin.industry.fundshop.query.facade.IFundInfoQueryNSortFacade')
    print(registry.get_provides('com.wangyin.industry.fundshop.query.facade.IFundInfoQueryNSortFacade' ,group='shopbetafunc' ,version='1.0.0'))


    user_provider = DubboClient('com.wangyin.industry.fundshop.query.facade.IFundInfoQueryNSortFacade', registry,group='shopbetafunc', version='1.0.0')
    # print(user_provider.registry)

    val = (registry.get_provides('com.wangyin.industry.fundshop.query.facade.IFundInfoQueryNSortFacade', group='shopbetafunc', version='1.0.0'))
    print(val.popitem())
    print(val)
    # try:
    #     # print(user_provider.query());
    #
    # except DubboClientError as client_error:
    #     print (client_error)
    print ('test end')