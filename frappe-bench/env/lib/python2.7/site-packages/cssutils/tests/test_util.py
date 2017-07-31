# -*- coding: utf-8 -*-
"""Testcases for cssutils.util"""
from __future__ import with_statement

import cgi
from email import message_from_string, message_from_file
import StringIO
import re
import sys
import urllib2
import xml.dom

try:
    import mock
except ImportError:
    mock = None
    print "install mock library to run all tests"

import basetest
import encutils

from cssutils.util import Base, ListSeq, _readUrl, _defaultFetcher, LazyRegex

class ListSeqTestCase(basetest.BaseTestCase):

    def test_all(self):
        "util.ListSeq"
        ls = ListSeq()
        self.assertEqual(0, len(ls))
        # append()
        self.assertRaises(NotImplementedError, ls.append, 1)
        # set
        self.assertRaises(NotImplementedError, ls.__setitem__, 0, 1)

        # hack:
        ls.seq.append(1)
        ls.seq.append(2)

        # len
        self.assertEqual(2, len(ls))
        # __contains__
        self.assertEqual(True, 1 in ls)
        # get
        self.assertEqual(1, ls[0])
        self.assertEqual(2, ls[1])
        # del
        del ls[0]
        self.assertEqual(1, len(ls))
        self.assertEqual(False, 1 in ls)
        # for in
        for x in ls:
            self.assertEqual(2, x)


class BaseTestCase(basetest.BaseTestCase):

    def test_normalize(self):
        "Base._normalize()"
        b = Base()
        tests = {u'abcdefg ABCDEFG äöüß€ AÖÜ': u'abcdefg abcdefg äöüß€ aöü',
                 ur'\ga\Ga\\\ ': ur'gaga\ ',
                 ur'0123456789': u'0123456789',
                 # unicode escape seqs should have been done by
                 # the tokenizer...
                 }
        for test, exp in tests.items():
            self.assertEqual(b._normalize(test), exp)
            # static too
            self.assertEqual(Base._normalize(test), exp)

    def test_tokenupto(self):
        "Base._tokensupto2()"

        # tests nested blocks of {} [] or ()
        b = Base()

        tests = [
            ('default', u'a[{1}]({2}) { } NOT', u'a[{1}]({2}) { }', False),
            ('default', u'a[{1}]({2}) { } NOT', u'a[{1}]func({2}) { }', True),
            ('blockstartonly', u'a[{1}]({2}) { NOT', u'a[{1}]({2}) {', False),
            ('blockstartonly', u'a[{1}]({2}) { NOT', u'a[{1}]func({2}) {', True),
            ('propertynameendonly', u'a[(2)1] { }2 : a;', u'a[(2)1] { }2 :', False),
            ('propertynameendonly', u'a[(2)1] { }2 : a;', u'a[func(2)1] { }2 :', True),
            ('propertyvalueendonly', u'a{;{;}[;](;)}[;{;}[;](;)](;{;}[;](;)) 1; NOT',
                u'a{;{;}[;](;)}[;{;}[;](;)](;{;}[;](;)) 1;', False),
            ('propertyvalueendonly', u'a{;{;}[;](;)}[;{;}[;](;)](;{;}[;](;)) 1; NOT',
                u'a{;{;}[;]func(;)}[;{;}[;]func(;)]func(;{;}[;]func(;)) 1;', True),
            ('funcendonly', u'a{[1]}([3])[{[1]}[2]([3])]) NOT',
                u'a{[1]}([3])[{[1]}[2]([3])])', False),
            ('funcendonly', u'a{[1]}([3])[{[1]}[2]([3])]) NOT',
                u'a{[1]}func([3])[{[1]}[2]func([3])])', True),
            ('selectorattendonly', u'[a[()]{()}([()]{()}())] NOT',
                u'[a[()]{()}([()]{()}())]', False),
            ('selectorattendonly', u'[a[()]{()}([()]{()}())] NOT',
                u'[a[func()]{func()}func([func()]{func()}func())]', True),
            # issue 50
            ('withstarttoken [', u'a];x', u'[a];', False)
            ]

        for typ, values, exp, paransasfunc in tests:

            def maketokens(valuelist):
                # returns list of tuples
                return [('TYPE', v, 0, 0) for v in valuelist]

            tokens = maketokens(list(values))
            if paransasfunc:
                for i, t in enumerate(tokens):
                    if u'(' == t[1]:
                        tokens[i] = ('FUNCTION', u'func(', t[2], t[3])

            if 'default' == typ:
                restokens = b._tokensupto2(tokens)
            elif 'blockstartonly' == typ:
                restokens = b._tokensupto2(
                    tokens, blockstartonly=True)
            elif 'propertynameendonly' == typ:
                restokens = b._tokensupto2(
                    tokens, propertynameendonly=True)
            elif 'propertyvalueendonly' == typ:
                restokens = b._tokensupto2(
                    tokens, propertyvalueendonly=True)
            elif 'funcendonly' == typ:
                restokens = b._tokensupto2(
                    tokens, funcendonly=True)
            elif 'selectorattendonly' == typ:
                restokens = b._tokensupto2(
                    tokens, selectorattendonly=True)
            elif 'withstarttoken [' == typ:
                restokens = b._tokensupto2(tokens, ('CHAR', '[', 0, 0))

            res = u''.join([t[1] for t in restokens])
            self.assertEqual(exp, res)


class _readUrl_TestCase(basetest.BaseTestCase):
    """needs mock"""

    def test_readUrl(self):
        """util._readUrl()"""
        # for additional tests see test_parse.py
        url = 'http://example.com/test.css'

        def make_fetcher(r):
            # normally r == encoding, content
            def fetcher(url):
                return r
            return fetcher

        tests = {
            # defaultFetcher returns: readUrl returns
            None: (None, None, None),
            (None, ''): ('utf-8', 5, u''),
            (None, u'€'.encode('utf-8')): ('utf-8', 5, u'€'),
            ('utf-8', u'€'.encode('utf-8')): ('utf-8', 1, u'€'),
            ('ISO-8859-1', u'ä'.encode('iso-8859-1')): ('ISO-8859-1', 1, u'ä'),
            ('ASCII', u'a'.encode('ascii')): ('ASCII', 1, u'a')
        }

        for r, exp in tests.items():
            self.assertEqual(_readUrl(url, fetcher=make_fetcher(r)), exp)

        tests = {
            # (overrideEncoding, parentEncoding, (httpencoding, content)):
            #                        readUrl returns

            # ===== 0. OVERRIDE WINS =====
            # override + parent + http
            ('latin1', 'ascii', ('utf-16', u''.encode())): ('latin1', 0, u''),
            ('latin1', 'ascii', ('utf-16', u'123'.encode())): ('latin1', 0, u'123'),
            ('latin1', 'ascii', ('utf-16', u'ä'.encode('iso-8859-1'))):
                ('latin1', 0, u'ä'),
            ('latin1', 'ascii', ('utf-16', u'a'.encode('ascii'))):
                ('latin1',0,  u'a'),
            # + @charset
            ('latin1', 'ascii', ('utf-16', u'@charset "ascii";'.encode())):
                ('latin1', 0, u'@charset "latin1";'),
            ('latin1', 'ascii', ('utf-16', u'@charset "utf-8";ä'.encode('latin1'))):
                ('latin1', 0, u'@charset "latin1";ä'),
            ('latin1', 'ascii', ('utf-16', u'@charset "utf-8";ä'.encode('utf-8'))):
                ('latin1', 0, u'@charset "latin1";\xc3\xa4'), # read as latin1!

            # override only
            ('latin1', None, None): (None, None, None),
            ('latin1', None, (None, u''.encode())): ('latin1', 0, u''),
            ('latin1', None, (None, u'123'.encode())): ('latin1', 0, u'123'),
            ('latin1', None, (None, u'ä'.encode('iso-8859-1'))):
                ('latin1', 0, u'ä'),
            ('latin1', None, (None, u'a'.encode('ascii'))):
                ('latin1', 0, u'a'),
            # + @charset
            ('latin1', None, (None, u'@charset "ascii";'.encode())):
                ('latin1', 0, u'@charset "latin1";'),
            ('latin1', None, (None, u'@charset "utf-8";ä'.encode('latin1'))):
                ('latin1', 0, u'@charset "latin1";ä'),
            ('latin1', None, (None, u'@charset "utf-8";ä'.encode('utf-8'))):
                ('latin1', 0, u'@charset "latin1";\xc3\xa4'), # read as latin1!

            # override + parent
            ('latin1', 'ascii', None): (None, None, None),
            ('latin1', 'ascii', (None, u''.encode())): ('latin1', 0, u''),
            ('latin1', 'ascii', (None, u'123'.encode())): ('latin1', 0, u'123'),
            ('latin1', 'ascii', (None, u'ä'.encode('iso-8859-1'))):
                ('latin1', 0, u'ä'),
            ('latin1', 'ascii', (None, u'a'.encode('ascii'))):
                ('latin1', 0, u'a'),
            # + @charset
            ('latin1', 'ascii', (None, u'@charset "ascii";'.encode())):
                ('latin1', 0, u'@charset "latin1";'),
            ('latin1', 'ascii', (None, u'@charset "utf-8";ä'.encode('latin1'))):
                ('latin1', 0, u'@charset "latin1";ä'),
            ('latin1', 'ascii', (None, u'@charset "utf-8";ä'.encode('utf-8'))):
                ('latin1', 0, u'@charset "latin1";\xc3\xa4'), # read as latin1!

            # override + http
            ('latin1', None, ('utf-16', u''.encode())): ('latin1', 0, u''),
            ('latin1', None, ('utf-16', u'123'.encode())): ('latin1', 0, u'123'),
            ('latin1', None, ('utf-16', u'ä'.encode('iso-8859-1'))):
                ('latin1', 0, u'ä'),
            ('latin1', None, ('utf-16', u'a'.encode('ascii'))):
                ('latin1', 0, u'a'),
            # + @charset
            ('latin1', None, ('utf-16', u'@charset "ascii";'.encode())):
                ('latin1', 0, u'@charset "latin1";'),
            ('latin1', None, ('utf-16', u'@charset "utf-8";ä'.encode('latin1'))):
                ('latin1', 0, u'@charset "latin1";ä'),
            ('latin1', None, ('utf-16', u'@charset "utf-8";ä'.encode('utf-8'))):
                ('latin1', 0, u'@charset "latin1";\xc3\xa4'), # read as latin1!

            # override ü @charset
            ('latin1', None, (None, u'@charset "ascii";'.encode())):
                ('latin1', 0, u'@charset "latin1";'),
            ('latin1', None, (None, u'@charset "utf-8";ä'.encode('latin1'))):
                ('latin1', 0, u'@charset "latin1";ä'),
            ('latin1', None, (None, u'@charset "utf-8";ä'.encode('utf-8'))):
                ('latin1', 0, u'@charset "latin1";\xc3\xa4'), # read as latin1!


            # ===== 1. HTTP WINS =====
            (None, 'ascii', ('latin1', u''.encode())): ('latin1', 1, u''),
            (None, 'ascii', ('latin1', u'123'.encode())): ('latin1', 1, u'123'),
            (None, 'ascii', ('latin1', u'ä'.encode('iso-8859-1'))):
                ('latin1', 1, u'ä'),
            (None, 'ascii', ('latin1', u'a'.encode('ascii'))):
                ('latin1', 1, u'a'),
            # + @charset
            (None, 'ascii', ('latin1', u'@charset "ascii";'.encode())):
                ('latin1', 1, u'@charset "latin1";'),
            (None, 'ascii', ('latin1', u'@charset "utf-8";ä'.encode('latin1'))):
                ('latin1', 1, u'@charset "latin1";ä'),
            (None, 'ascii', ('latin1', u'@charset "utf-8";ä'.encode('utf-8'))):
                ('latin1', 1, u'@charset "latin1";\xc3\xa4'), # read as latin1!


            # ===== 2. @charset WINS =====
            (None, 'ascii', (None, u'@charset "latin1";'.encode())):
                ('latin1', 2, u'@charset "latin1";'),
            (None, 'ascii', (None, u'@charset "latin1";ä'.encode('latin1'))):
                ('latin1', 2, u'@charset "latin1";ä'),
            (None, 'ascii', (None, u'@charset "latin1";ä'.encode('utf-8'))):
                ('latin1', 2, u'@charset "latin1";\xc3\xa4'), # read as latin1!

            # ===== 2. BOM WINS =====
            (None, 'ascii', (None, u'ä'.encode('utf-8-sig'))):
                ('utf-8-sig', 2, u'\xe4'), # read as latin1!
            (None, 'ascii', (None, u'@charset "utf-8";ä'.encode('utf-8-sig'))):
                ('utf-8-sig', 2, u'@charset "utf-8";\xe4'), # read as latin1!
            (None, 'ascii', (None, u'@charset "latin1";ä'.encode('utf-8-sig'))):
                ('utf-8-sig', 2, u'@charset "utf-8";\xe4'), # read as latin1!


            # ===== 4. parentEncoding WINS =====
            (None, 'latin1', (None, u''.encode())): ('latin1', 4, u''),
            (None, 'latin1', (None, u'123'.encode())): ('latin1', 4, u'123'),
            (None, 'latin1', (None, u'ä'.encode('iso-8859-1'))):
                ('latin1', 4, u'ä'),
            (None, 'latin1', (None, u'a'.encode('ascii'))):
                ('latin1', 4, u'a'),
            (None, 'latin1', (None, u'ä'.encode('utf-8'))):
                ('latin1', 4, u'\xc3\xa4'), # read as latin1!

            # ===== 5. default WINS which in this case is None! =====
            (None, None, (None, u''.encode())): ('utf-8', 5, u''),
            (None, None, (None, u'123'.encode())): ('utf-8', 5, u'123'),
            (None, None, (None, u'a'.encode('ascii'))):
                ('utf-8', 5, u'a'),
            (None, None, (None, u'ä'.encode('utf-8'))):
                ('utf-8', 5, u'ä'), # read as utf-8
            (None, None, (None, u'ä'.encode('iso-8859-1'))): # trigger UnicodeDecodeError!
                ('utf-8', 5, None),


        }
        for (override, parent, r), exp in tests.items():
            self.assertEqual(_readUrl(url,
                                       overrideEncoding=override,
                                       parentEncoding=parent,
                                       fetcher=make_fetcher(r)),
                              exp)

    def test_defaultFetcher(self):
        """util._defaultFetcher"""
        if mock:

            class Response(object):
                """urllib2.Reponse mock"""
                def __init__(self, url,
                             contenttype, content,
                             exception=None, args=None):
                    self.url = url

                    mt, params = cgi.parse_header(contenttype)
                    self.mimetype = mt
                    self.charset = params.get('charset', None)

                    self.text = content

                    self.exception = exception
                    self.args = args

                def geturl(self):
                    return self.url

                def info(self):
                    mimetype, charset = self.mimetype, self.charset
                    class Info(object):
                        
                        # py2x
                        def gettype(self):
                            return mimetype
                        def getparam(self, name=None):
                            return charset
                        
                        # py 3x
                        get_content_type = gettype
                        get_content_charset = getparam # here always charset!  
                        
                    return Info()

                def read(self):
                    # returns fake text or raises fake exception
                    if not self.exception:
                        return self.text
                    else:
                        raise self.exception(*self.args)

            def urlopen(url,
                        contenttype=None, content=None,
                        exception=None, args=None):
                # return an mock which returns parameterized Response
                def x(*ignored):
                    if exception:
                        raise exception(*args)
                    else:
                        return Response(url,
                                        contenttype, content,
                                        exception=exception, args=args)
                return x

            urlopenpatch = 'urllib2.urlopen' if basetest.PY2x else 'urllib.request.urlopen' 

            # positive tests
            tests = {
                # content-type, contentstr: encoding, contentstr
                ('text/css', u'€'.encode('utf-8')):
                        (None, u'€'.encode('utf-8')),
                ('text/css;charset=utf-8', u'€'.encode('utf-8')):
                        ('utf-8', u'€'.encode('utf-8')),
                ('text/css;charset=ascii', 'a'):
                        ('ascii', 'a')
            }
            url = 'http://example.com/test.css'
            for (contenttype, content), exp in tests.items():
                @mock.patch(urlopenpatch, new=urlopen(url, contenttype, content))
                def do(url):
                    return _defaultFetcher(url)
                
                self.assertEqual(exp, do(url))

            # wrong mimetype
            @mock.patch(urlopenpatch, new=urlopen(url, 'text/html', 'a'))
            def do(url):
                return _defaultFetcher(url)
            
            self.assertRaises(ValueError, do, url)
            
            # calling url results in fake exception
                            
            # py2 ~= py3 raises error earlier than urlopen!
            tests = {
                '1': (ValueError, ['invalid value for url']),
                #_readUrl('mailto:a.css')
                'mailto:e4': (urllib2.URLError, ['urlerror']),
                # cannot resolve x, IOError
                'http://x': (urllib2.URLError, ['ioerror']),
            }
            for url, (exception, args) in tests.items():
                @mock.patch(urlopenpatch, new=urlopen(url, exception=exception, args=args))
                def do(url):
                    return _defaultFetcher(url)
                
                self.assertRaises(exception, do, url)

            # py2 != py3 raises error earlier than urlopen!
            urlrequestpatch = 'urllib2.urlopen' if basetest.PY2x else 'urllib.request.Request' 
            tests = {
                #_readUrl('http://cthedot.de/__UNKNOWN__.css')
                'e2': (urllib2.HTTPError, ['u', 500, 'server error', {}, None]),
                'e3': (urllib2.HTTPError, ['u', 404, 'not found', {}, None]),
            }
            for url, (exception, args) in tests.items():
                @mock.patch(urlrequestpatch, new=urlopen(url, exception=exception, args=args))
                def do(url):
                    return _defaultFetcher(url)
                
                self.assertRaises(exception, do, url)

        else:
            self.assertEqual(False, u'Mock needed for this test')


class TestLazyRegex(basetest.BaseTestCase):
    """Tests for cssutils.util.LazyRegex."""

    def setUp(self):
        self.lazyre = LazyRegex('f.o')

    def test_public_interface(self):
        methods = ['search', 'match', 'split', 'sub', 'subn', 'findall',
                   'finditer', 'pattern', 'flags', 'groups', 'groupindex',]
        for method in methods:
            self.assertTrue(hasattr(self.lazyre, method),
                            'expected %r public attribute' % method)

    def test_ensure(self):
        self.assertIsNone(self.lazyre.matcher)
        self.lazyre.ensure()
        self.assertIsNotNone(self.lazyre.matcher)

    def test_calling(self):
        self.assertIsNone(self.lazyre('bar'))
        match = self.lazyre('foobar')
        self.assertEquals(match.group(), 'foo')

    def test_matching(self):
        self.assertIsNone(self.lazyre.match('bar'))
        match = self.lazyre.match('foobar')
        self.assertEquals(match.group(), 'foo')

    def test_matching_with_position_parameters(self):
        self.assertIsNone(self.lazyre.match('foo', 1))
        self.assertIsNone(self.lazyre.match('foo', 0, 2))

    def test_searching(self):
        self.assertIsNone(self.lazyre.search('rafuubar'))
        match = self.lazyre.search('rafoobar')
        self.assertEquals(match.group(), 'foo')

    def test_searching_with_position_parameters(self):
        self.assertIsNone(self.lazyre.search('rafoobar', 3))
        self.assertIsNone(self.lazyre.search('rafoobar', 0, 4))
        match = self.lazyre.search('rafoofuobar', 4)
        self.assertEquals(match.group(), 'fuo')

    def test_split(self):
        self.assertEquals(self.lazyre.split('rafoobarfoobaz'),
                          ['ra', 'bar', 'baz'])
        self.assertEquals(self.lazyre.split('rafoobarfoobaz', 1),
                          ['ra', 'barfoobaz'])

    def test_findall(self):
        self.assertEquals(self.lazyre.findall('rafoobarfuobaz'),
                          ['foo', 'fuo'])

    def test_finditer(self):
        result = self.lazyre.finditer('rafoobarfuobaz')
        self.assertEquals([m.group() for m in result], ['foo', 'fuo'])

    def test_sub(self):
        self.assertEquals(self.lazyre.sub('bar', 'foofoo'), 'barbar')
        self.assertEquals(self.lazyre.sub(lambda x: 'baz', 'foofoo'), 'bazbaz')

    def test_subn(self):
        subbed = self.lazyre.subn('bar', 'foofoo')
        self.assertEquals(subbed, ('barbar', 2))
        subbed = self.lazyre.subn(lambda x: 'baz', 'foofoo')
        self.assertEquals(subbed, ('bazbaz', 2))

    def test_groups(self):
        lazyre = LazyRegex('(.)(.)')
        self.assertIsNone(lazyre.groups)
        lazyre.ensure()
        self.assertEquals(lazyre.groups, 2)

    def test_groupindex(self):
        lazyre = LazyRegex('(?P<foo>.)')
        self.assertIsNone(lazyre.groupindex)
        lazyre.ensure()
        self.assertEquals(lazyre.groupindex, {'foo': 1})

    def test_flags(self):
        self.lazyre.ensure()
        self.assertEquals(self.lazyre.flags, re.compile('.').flags)

    def test_pattern(self):
        self.assertEquals(self.lazyre.pattern, 'f.o')


if __name__ == '__main__':
    import unittest
    unittest.main()
