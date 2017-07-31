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
nulle viens divi trīs četri pieci seši septiņi astoņi deviņi

>>> print(fill(' '.join([n2w(i+10) for i in range(10)])))
desmit vienpadsmit divpadsmit trīspadsmit četrpadsmit piecpadsmit
sešpadsmit septiņpadsmit astoņpadsmit deviņpadsmit

>>> print(fill(' '.join([n2w(i*10) for i in range(10)])))
nulle desmit divdesmit trīsdesmit četrdesmit piecdesmit sešdesmit
septiņdesmit astoņdesmit deviņdesmit

>>> print(n2w(100))
simts
>>> print(n2w(101))
simtu viens
>>> print(n2w(110))
simts desmit
>>> print(n2w(115))
simts piecpadsmit
>>> print(n2w(123))
simts divdesmit trīs
>>> print(n2w(1000))
tūkstotis
>>> print(n2w(1001))
tūkstotis viens
>>> print(n2w(2012))
divi tūkstoši divpadsmit

>>> print(fill(n2w(1234567890)))
miljards divi simti trīsdesmit četri miljoni pieci simti sešdesmit
septiņi tūkstoši astoņi simti deviņdesmit

>>> print(fill(n2w(215461407892039002157189883901676)))
divi simti piecpadsmit nontiljoni četri simti sešdesmit viens
oktiljons četri simti septiņi septiljoni astoņi simti deviņdesmit divi
sikstiljoni trīsdesmit deviņi kvintiljoni divi kvadriljoni simts
piecdesmit septiņi triljoni simts astoņdesmit deviņi miljardi astoņi
simti astoņdesmit trīs miljoni deviņi simti viens tūkstotis seši simti
septiņdesmit seši

>>> print(fill(n2w(719094234693663034822824384220291)))
septiņi simti deviņpadsmit nontiljoni deviņdesmit četri oktiljoni divi
simti trīsdesmit četri septiljoni seši simti deviņdesmit trīs
sikstiljoni seši simti sešdesmit trīs kvintiljoni trīsdesmit četri
kvadriljoni astoņi simti divdesmit divi triljoni astoņi simti
divdesmit četri miljardi trīs simti astoņdesmit četri miljoni divi
simti divdesmit tūkstoši divi simti deviņdesmit viens

# TODO: fix this:
# >>> print(fill(n2w(1000000000000000000000000000000)))
# nontiljons

>>> print(to_currency(1.0, 'EUR'))
viens eiro, nulle centu

>>> print(to_currency(1.0, 'LVL'))
viens lats, nulle santīmu

>>> print(to_currency(1234.56, 'EUR'))
tūkstotis divi simti trīsdesmit četri eiro, piecdesmit seši centi

>>> print(to_currency(1234.56, 'LVL'))
tūkstotis divi simti trīsdesmit četri lati, piecdesmit seši santīmi

>>> print(to_currency(10111, 'EUR', seperator=' un'))
simtu viens eiro un vienpadsmit centi

>>> print(to_currency(10121, 'LVL', seperator=' un'))
simtu viens lats un divdesmit viens santīms

>>> print(to_currency(-1251985, cents = False))
mīnus divpadsmit tūkstoši pieci simti deviņpadsmit eiro, 85 centi
"""
from __future__ import unicode_literals

ZERO = (u'nulle',)

ONES = {
    1: (u'viens',),
    2: (u'divi',),
    3: (u'trīs',),
    4: (u'četri',),
    5: (u'pieci',),
    6: (u'seši',),
    7: (u'septiņi',),
    8: (u'astoņi',),
    9: (u'deviņi',),
}

TENS = {
    0: (u'desmit',),
    1: (u'vienpadsmit',),
    2: (u'divpadsmit',),
    3: (u'trīspadsmit',),
    4: (u'četrpadsmit',),
    5: (u'piecpadsmit',),
    6: (u'sešpadsmit',),
    7: (u'septiņpadsmit',),
    8: (u'astoņpadsmit',),
    9: (u'deviņpadsmit',),
}

TWENTIES = {
    2: (u'divdesmit',),
    3: (u'trīsdesmit',),
    4: (u'četrdesmit',),
    5: (u'piecdesmit',),
    6: (u'sešdesmit',),
    7: (u'septiņdesmit',),
    8: (u'astoņdesmit',),
    9: (u'deviņdesmit',),
}

HUNDRED = (u'simts', u'simti', u'simtu')

THOUSANDS = {
    1: (u'tūkstotis', u'tūkstoši', u'tūkstošu'),
    2: (u'miljons', u'miljoni', u'miljonu'),
    3: (u'miljards', u'miljardi', u'miljardu'),
    4: (u'triljons', u'triljoni', u'triljonu'),
    5: (u'kvadriljons', u'kvadriljoni', u'kvadriljonu'),
    6: (u'kvintiljons', u'kvintiljoni', u'kvintiljonu'),
    7: (u'sikstiljons', u'sikstiljoni', u'sikstiljonu'),
    8: (u'septiljons', u'septiljoni', u'septiljonu'),
    9: (u'oktiljons', u'oktiljoni', u'oktiljonu'),
    10: (u'nontiljons', u'nontiljoni', u'nontiljonu'),
}

CURRENCIES = {
    'LVL': (
        (u'lats', u'lati', u'latu'), (u'santīms', u'santīmi', u'santīmu')
    ),
    'EUR': (
        (u'eiro', u'eiro', u'eiro'), (u'cents', u'centi', u'centu')
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
    # gettext implementation:
    # (n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2)

    form = 0 if (n % 10 == 1 and n % 100 != 11) else 1 if n != 0 else 2

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
            if n3 == 1 and n2 == 0 and n1 > 0:
                words.append(HUNDRED[2])
            elif n3 > 1:
                words.append(ONES[n3][0])
                words.append(HUNDRED[1])
            else:
                words.append(HUNDRED[0])

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
        return u'%s kablelis %s' % (int2word(int(left)), int2word(int(right)))
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
        minus_str = "mīnus "
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


class Num2Word_LV(object):
    def to_cardinal(self, number):
        return n2w(number)

    def to_ordinal(self, number):
        raise NotImplementedError()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
