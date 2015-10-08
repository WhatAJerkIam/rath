__author__ = 'Peterz'
import urllib.request as request
def access_url(url):
    resp=request.urlopen(url)
    print("http header:%s"%resp.info())
    print("http status: %s"%resp.getcode())
    print("url: %s"%resp.geturl())
url="http://www.che08.com/pentaho/Pivot?solution=bi-developers&path=&action=yuantian_rentle.analysisview.xaction&userid=joe&password=password"
access_url(url)
