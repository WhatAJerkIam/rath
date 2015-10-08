
import os
import utils


try:
    import httplib2
except ImportError as msg:
    import platform
    if platform.system()=="Windows":
        os.chdir('..\\external\\httplib2-0.9.1\\')
        cmd = 'python setup.py install'
        lines = utils.run_cmd(cmd)
        os.chdir('..\\..\\rest\\')

import urllib
import base64
from base64 import encodestring
import base64
from encode import multipart_encode
import encode
from mimeTypes import *
import mimetypes
import logging

if utils.getPythonVersion() == '2':
    import json
    import urlparse as urlparse
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    import json

    import urllib.parse as urlparse

logger = logging.getLogger("test.restclient")

from io import StringIO

class Connection:
    def __init__(self, base_url, username=None, password=None, timeout = 10):
        self.base_url = base_url
        self.username = username
        m = mimeTypes()
        self.mimetypes = m.getDictionary()

        self.url = urlparse.parse_qs(base_url)

        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(base_url)

        self.scheme = scheme
        self.host = netloc
        self.path = path
        import httplib2

        # Create Http class with support for Digest HTTP Authentication, if necessary
        self.h = httplib2.Http(timeout = timeout)

        self.h.follow_all_redirects = False
        if username and password:
            self.h.add_credentials(username, password)

    def request_get(self, resource, args = None, headers={}):
        return self.request(resource, "get", args, headers=headers)

    def request_delete(self, resource, args = None, headers={}):
        return self.request(resource, "delete", args, headers=headers)

    def request_head(self, resource, args = None, headers={}):
        return self.request(resource, "head", args, headers=headers)

    def request_post(self, resource, args = None, body = None, parts=None, headers={}):
        return self.request(resource, "post", args , body = body, parts=parts, headers=headers)

    def rpc_request_post(self, body = None, headers={}):
        resp, content = self.h.request(self.base_url, 'POST', body=body, headers=headers)
        return {r'headers':resp, r'body':content}

    def request_put(self, resource, args = None, body = None, parts=None, headers={}):
        return self.request(resource, "put", args , body = body, parts=parts, headers=headers)

    def get_content_type(self, filename):
        extension = filename.split('.')[-1]
        guessed_mimetype = self.mimetypes.get(extension, mimetypes.guess_type(filename)[0])
        return guessed_mimetype or 'application/octet-stream'

    def request(self, resource, method = "get", args = None, body = None, parts=None, headers={}):
        params = None
        path = resource
        headers['User-Agent'] = 'Basic Agent'

        BOUNDARY = r'00hoYUXOnLD5RQ8SKGYVgLLt64jejnMwtO7q8XE1'
        CRLF = r'\r\n'

        if parts:
            # Attempt to find the Mimetype
            headers['Content-Type']='multipart/form-data; boundary='+BOUNDARY
            encode_string = StringIO()
            for part in parts:
                if part.type != 'file':
                    continue
                encode_string.write(r'--' + BOUNDARY)
                encode_string.write(CRLF)

                body = None
                if part.type == 'file':
                    encode_string.write(r'Content-Disposition: form-data; name="%s"; filename="%s"' % (part.key, os.path.basename(part.text)))
                    encode_string.write(CRLF)
                    content_type = self.get_content_type(part.text)
                    encode_string.write(r'Content-Type: %s' % content_type)
                    encode_string.write(CRLF)
                    encode_string.write(r'Content-Transfer-Encoding: base64')
                    encode_string.write(CRLF)
                    encode_string.write(CRLF)
                    with open(part.text, "rb") as file:
                        body = base64.b64encode(file.read()).decode()
                        #body=str(file.read())
                else:
                    encode_string.write(r'Content-Disposition: form-data; name="%s"' % (part.key))
                    encode_string.write(CRLF)
                    encode_string.write(r'Content-Type: %s' % part.contentType)
                    encode_string.write(CRLF)
                    encode_string.write(CRLF)
                    body = part.text
                encode_string.write(body)
                encode_string.write(CRLF)

            encode_string.write(r'--' + BOUNDARY + r'--' + CRLF)

            body = encode_string.getvalue()
            headers['Content-Length'] = str(len(body))
        elif body:
            if not headers.get('Content-Type', None):
                headers['Content-Type']='text/xml'
            headers['Content-Length'] = str(len(body))
        else:
             if not headers.get('Content-Type', None):
                 headers['Content-Type']='text/xml'

        domain=self.base_url.split("//")[1].split("/")[0]
        if args:
            if utils.getPythonVersion() == '2':
                path += r"?" + urllib.urlencode(args)
            else:
                path += r"?" + urlparse.urlencode(args)

        request_path = []
        if self.path != "/":
            if self.path.endswith('/'):
                request_path.append(self.path[:-1])
            else:
                request_path.append(self.path)
            if path.startswith('/'):
                request_path.append(path[1:])
            else:
                request_path.append(path)
        # if self.host=='211.136.86.203':# kuan chang com IP
        #     url = r"%s://%s%s" % (self.scheme, self.host, ''.join(request_path))
        # else:# normal flow
        url = r"%s://%s%s" % (self.scheme, self.host, ''.join(request_path))
        url = url.rstrip('/')
        logger.info('request: %s' % url)
        resp, content = self.h.request(url, method.upper(), body=body, headers=headers )

        encoding = 'UTF-8'
        if 'content-type' in resp and 'charset' in resp['content-type']:
            items = resp['content-type'].split('=')
            encoding = items[1]
        if 'content-type' in resp and 'application' in resp['content-type'] and 'json' not in resp['content-type']:
            encoding = None
        if 'content-type' in resp and 'image' in resp['content-type']:
            encoding = None
        if encoding is not None:
            return {r'headers':resp, r'body':content.decode(encoding)}
        else:
            # not return binary data
            return {r'headers':resp, r'body':''}

    def encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self.get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join([element.decode('string_escape') for element in L])
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body


def parse_curl_error(lines):
    for l in lines:
        if l.startswith('curl: ('):
            return l
    return None

def check_curl_error(lines):
    l = parse_curl_error(lines)
    if l:
        raise Exception('curl error is found with [%s]' % l.strip())

def try_decode(lines):
    try:
        ret = [l.decode('gbk') for l in lines]
    except UnicodeDecodeError as msg:
        ret = [l.decode('utf-8') for l in lines]
    return ret

def parse_headers(lines):
    headers = {}
    for l in lines:
        if '< ' in l:
            messages = l.split('<')
            for m in messages:
                m = m[1:]
                if m.startswith('HTTP/1.1'):
                    items = m.split(' ')
                    headers['status']=items[1].strip()
                    headers['message']=items[2].strip()
                else:
                    items = m.strip().split(':')
                    if len(items) == 2:
                        headers[items[0].strip().lower()] = items[1].strip()
                    else:
                        pass
    return headers

def parse_body(file):
    lines = open(file, 'r+', encoding='utf-8').readlines()
    return lines

def execute_curl(cmd):
    import tempfile, shutil, os
    fd, path = tempfile.mkstemp()
    os.close(fd)
    resp = {}
    try:
        final_cmd = cmd + ' -o %s' % path
        logger.debug(final_cmd)
        lines = utils.run_cmd2(final_cmd)
        lines = try_decode(lines)
        print(lines)
        check_curl_error(lines)
        print(lines)
        headers = parse_headers(lines)
        body = ''.join(parse_body(path))
        resp['headers'] = headers
        resp['body'] = body
        return resp
    except Exception as msg:
        os.remove(path)
        raise msg
    return None

def get(resource, sso_cookie = None, args = None, headers={}, timeout = 10):
    conn = Connection(resource, timeout = timeout)
    if sso_cookie is not None:
        headers['Cookie'] = sso_cookie
    return conn.request_get('', args, headers)

def build_cmd(resource, sso_cookie, parts):
    items = ['curl', '--verbose']
    if sso_cookie is not None:
        items.extend(['--cookie', '"%s"' % sso_cookie])
    for p in parts:
        if p.type == 'file':
            items.extend(['-F', '"%s=@%s"' % (p.key, p.text)])
            if p.contentType=='multipart/form-data':
                items.extend(['-H','"Content-Type:%s"' %(p.contentType)])
        else:
            value = p.text.replace('"', '\\"')
            if p.contentType is not None:
                items.extend(['-F', '"%s=%s;type=%s"' % (p.key, value, p.contentType)])
            else:
                items.extend(['-F', '"%s=%s"' % (p.key, value)])
    items.extend([resource])
    cmd = ' '.join(items)
    return cmd

def post(resource, sso_cookie, args = None, body = None, parts=None, headers={}):
    if parts:
        cmd = build_cmd(resource, sso_cookie, parts)
        resp = execute_curl(cmd)
        return resp
    else:
        if sso_cookie is not None:
            headers['Cookie'] = sso_cookie
        conn = Connection(resource)
        return conn.request_post('/', args, body = body, parts=parts, headers=headers)

def rpc_post(case, sso_cookie, body = None):
    headers = {}
    logger.info('use application/octet-stream content type')
    headers['Content-Type'] = 'application/octet-stream'

    if sso_cookie is not None:
        headers['Cookie'] = sso_cookie
    pbJSON = build_pb_json(case)

    module = case.module
    requestType = case.requestType
    responseType = case.responseType
    module_meta = __import__('protos.%s' % module, globals(), locals(), [requestType])
    request_class_meta = getattr(module_meta, requestType)
    resp_class_meta = getattr(module_meta, responseType)
    jsonData = protobuf_json.json2pb(request_class_meta(), pbJSON)

    conn = Connection(case.url)
    resp = conn.rpc_request_post(jsonData.SerializeToString(), headers)

    #req = urllib2.Request(case.url, jsonData.SerializeToString(), headers)
    #urlResp = urllib2.urlopen(req)
    #resp = urlResp.read()
    if resp['headers'].status==200:  #rpc return 200
        pbResp = resp_class_meta()
        try:
            pbResp.ParseFromString(resp['body'])
        except Exception as msg:
            if isinstance(resp['body'],bytes):
                logger.info(resp['body'].decode('utf-8'))
            else:
                logger.info(resp['body'])
            raise msg
        resp['body'] = json.dumps(protobuf_json.pb2json(pbResp))
        resp['headers']['content-type'] = 'application/json'
        return resp
    else:
        resp['body']=resp['body'].decode('utf-8')
        return resp


def build_pb_json(case):
    jsonObj = json.loads(case.bodyText)
    baseRequestObj = {}
    baseRequestObj['ngLabel'] = case.ngLabel
    baseRequestObj['ngVersion'] = case.labelVersion
    baseRequestObj['action'] = case.action
    baseRequestObj['actVersion'] = case.actVersion
    jsonObj['baseRequest'] = baseRequestObj

    return jsonObj

def put(resource, sso_cookie, args = None, body = None, parts=None, headers={}):
    conn = Connection(resource)
    if sso_cookie is not None:
        headers['Cookie'] = sso_cookie
    return conn.request_put('/', args, body = body, parts=parts, headers=headers)

def delete(resource, sso_cookie, args = None, headers={}):
    conn = Connection(resource)
    if sso_cookie is not None:
        headers['Cookie'] = sso_cookie
    return conn.request_delete('/', args, headers=headers)
