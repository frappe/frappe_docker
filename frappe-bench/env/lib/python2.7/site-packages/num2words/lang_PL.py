# -*- encoding: utf-8 -*-
# Copyright (c) 2003, Taro Ogawa.  All Rights Reserved.
# Copyright (c) 2013, Savoir-faire Linux inc.  All Rights Reserved.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA
u"""
>>> from textwrap import fill

>>> ' '.join([str(i) for i in splitby3('1')])
u'1'
>>> ' '.join([str(i) for i in splitby3('1123')])
u'1 123'
>>> ' '.join([str(i) for i in splitby3('1234567890')])
u'1 234 567 890'

>>> print(' '.join([n2w(i) for i in range(10)]))
zero jeden dwa trzy cztery pięć sześć siedem osiem dziewięć

>>> print(fill(' '.join([n2w(i+10) for i in range(10)])))
dziesięć jedenaście dwanaście trzynaście czternaście piętnaście
szesnaście siedemnaście osiemnaście dziewiętnaście

>>> print(fill(' '.join([n2w(i*10) for i in range(10)])))
zero dziesięć dwadzieścia trzydzieści czterdzieści pięćdziesiąt
sześćdziesiąt siedemdziesiąt osiemdziesiąt dziewięćdzisiąt

>>> print(n2w(100))
sto
>>> print(n2w(101))
sto jeden
>>> print(n2w(110))
sto dziesięć
>>> print(n2w(115))
sto piętnaście
>>> print(n2w(123))
sto dwadzieścia trzy
>>> print(n2w(1000))
tysiąc
>>> print(n2w(1001))
tysiąc jeden
>>> print(n2w(2012))
dwa tysiące dwanaście

>>> print(n2w(12519.85))
dwanaście tysięcy pięćset dziewiętnaście przecinek osiemdziesiąt pięć

>>> print(fill(n2w(1234567890)))
miliard dwieście trzydzieści cztery miliony pięćset sześćdziesiąt
siedem tysięcy osiemset dziewięćdzisiąt

>>> print(fill(n2w(215461407892039002157189883901676)))
dwieście piętnaście kwintylionów czterysta sześćdziesiąt jeden
kwadryliardów czterysta siedem kwadrylionów osiemset dziewięćdzisiąt
dwa tryliardy trzydzieści dziewięć trylionów dwa biliardy sto
pięćdziesiąt siedem bilionów sto osiemdziesiąt dziewięć miliardów
osiemset osiemdziesiąt trzy miliony dziewęćset jeden tysięcy sześćset
siedemdziesiąt sześć

>>> print(fill(n2w(719094234693663034822824384220291)))
siedemset dziewiętnaście kwintylionów dziewięćdzisiąt cztery
kwadryliardy dwieście trzydzieści cztery kwadryliony sześćset
dziewięćdzisiąt trzy tryliardy sześćset sześćdziesiąt trzy tryliony
trzydzieści cztery biliardy osiemset dwadzieścia dwa biliony osiemset
dwadzieścia cztery miliardy trzysta osiemdziesiąt cztery miliony
dwieście dwadzieścia tysięcy dwieście dziewięćdzisiąt jeden

>>> print(to_currency(1.0, 'EUR'))
jeden euro, zero centów

>>> print(to_currency(1.0, 'PLN'))
jeden złoty, zero groszy

>>> print(to_currency(1234.56, 'EUR'))
tysiąc dwieście trzydzieści cztery euro, pięćdziesiąt sześć centów

>>> print(to_currency(1234.56, 'PLN'))
tysiąc dwieście trzydzieści cztery złote, pięćdziesiąt sześć groszy

>>> print(to_currency(10111, 'EUR', seperator=' i'))
sto jeden euro i jedenaście centów

>>> print(to_currency(10121, 'PLN', seperator=' i'))
sto jeden złotych i dwadzieścia jeden groszy

>>> print(to_currency(-1251985, cents = False))
minus dwanaście tysięcy pięćset dziewiętnaście euro, 85 centów
"""
from __future__ import unicode_literals

ZERO = (u'zero',)

ONES = {
    1: (u'jeden',),
    2: (u'dwa',),
    3: (u'trzy',),
    4: (u'cztery',),
    5: (u'pięć',),
    6: (u'sześć',),
    7: (u'siedem',),
    8: (u'osiem',),
    9: (u'dziewięć',),
}

TENS = {
    0: (u'dziesięć',),
    1: (u'jedenaście',),
    2: (u'dwanaście',),
    3: (u'trzynaście',),
    4: (u'czternaście',),
    5: (u'piętnaście',),
    6: (u'szesnaście',),
    7: (u'siedemnaście',),
    8: (u'osiemnaście',),
    9: (u'dziewiętnaście',),
}

TWENTIES = {
    2: (u'dwadzieścia',),
    3: (u'trzydzieści',),
    4: (u'czterdzieści',),
    5: (u'pięćdziesiąt',),
    6: (u'sześćdziesiąt',),
    7: (u'siedemdziesiąt',),
    8: (u'osiemdziesiąt',),
    9: (u'dziewięćdzisiąt',),
}

HUNDREDS = {
    1: (u'sto',),
    2: (u'dwieście',),
    3: (u'trzysta',),
    4: (u'czterysta',),
    5: (u'pięćset',),
    6: (u'sześćset',),
    7: (u'siedemset',),
    8: (u'osiemset',),
    9: (u'dziewęćset',),
}

THOUSANDS = {
    1: (u'tysiąc', u'tysiące', u'tysięcy'), # 10^3
    2: (u'milion', u'miliony', u'milionów'), # 10^6
    3: (u'miliard', u'miliardy', u'miliardów'), # 10^9
    4: (u'bilion', u'biliony', u'bilionów'), # 10^12
    5: (u'biliard', u'biliardy', u'biliardów'), # 10^15
    6: (u'trylion', u'tryliony', u'trylionów'), # 10^18
    7: (u'tryliard', u'tryliardy', u'tryliardów'), # 10^21
    8: (u'kwadrylion', u'kwadryliony', u'kwadrylionów'), # 10^24
    9: (u'kwaryliard', u'kwadryliardy', u'kwadryliardów'), #10^27
    10: (u'kwintylion', u'kwintyliony', u'kwintylionów'), # 10^30
}

CURRENCIES = {
    'PLN': (
        (u'złoty', u'złote', u'złotych'), (u'grosz', u'grosze', u'groszy')
    ),
    'EUR': (
        (u'euro', u'euro', u'euro'), (u'cent', u'centy', u'centów')
    ),
}


def splitby3(n):
    length = len(n)
    if length > 3:
        start = length % 3
        if start > 0:
            yield int(n[:start])
        for i in range(start, length, 3):
            yield int(n[i:i+3])
    else:
        yield int(n)


def get_digits(n):
    return [int(x) for x in reversed(list(('%03d' % n)[-3:]))]


def pluralize(n, forms):
    form = 0 if n==1 else 1 if (n % 10 > 1 and n % 10 < 5 and (n % 100 < 10 or n % 100 > 20)) else 2
    return forms[form]


def int2word(n):
    if n == 0:
        return ZERO[0]

    words = []
    chunks = list(splitby3(str(n)))
    i = len(chunks)
    for x in chunks:
        i -= 1
        n1, n2, n3 = get_digits(x)

        # print str(n3) + str(n2) + str(n1)

        if n3 > 0:
            words.append(HUNDREDS[n3][0])
            
        if n2 > 1:
            words.append(TWENTIES[n2][0])

        if n2 == 1:
            words.append(TENS[n1][0])
        elif n1 > 0 and not (i > 0 and x == 1):
            words.append(ONES[n1][0])

        if i > 0:
            words.append(pluralize(x, THOUSANDS[i]))

    return ' '.join(words)


def n2w(n):
    n = str(n).replace(',', '.')
    if '.' in n:
        left, right = n.split('.')
        return u'%s przecinek %s' % (int2word(int(left)), int2word(int(right)))
    else:
        return int2word(int(n))


def to_currency(n, currency='EUR', cents=True, seperator=','):
    if type(n) == int:
        if n < 0:
            minus = True
        else:
            minus = False

        n = abs(n)
        left = n / 100
        right = n % 100
    else:
        n = str(n).replace(',', '.')
        if '.' in n:
            left, right = n.split('.')
        else:
            left, right = n, 0
        left, right = int(left), int(right)
        minus = False
    cr1, cr2 = CURRENCIES[currency]

    if minus:
        minus_str = "minus "
    else:
        minus_str = ""

    if cents:
        cents_str = int2word(right)
    else:
        cents_str = "%02d" % right

    return u'%s%s %s%s %s %s' % (
        minus_str,
        int2word(left),
        pluralize(left, cr1),
        seperator,
        cents_str,
        pluralize(right, cr2)
    )


class Num2Word_PL(object):
    def to_cardinal(self, number):
        return n2w(number)

    def to_ordinal(self, number):
        raise NotImplementedError()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
