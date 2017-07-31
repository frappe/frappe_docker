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
ноль один два три четыре пять шесть семь восемь девять

>>> print(fill(' '.join([n2w(i+10) for i in range(10)])))
десять одиннадцать двенадцать тринадцать четырнадцать пятнадцать
шестнадцать семнадцать восемнадцать девятнадцать

>>> print(fill(' '.join([n2w(i*10) for i in range(10)])))
ноль десять двадцать тридцать сорок пятьдесят шестьдесят семьдесят
восемьдесят девяносто

>>> print(n2w(100))
сто
>>> print(n2w(101))
сто один
>>> print(n2w(110))
сто десять
>>> print(n2w(115))
сто пятнадцать
>>> print(n2w(123))
сто двадцать три
>>> print(n2w(1000))
тысяча
>>> print(n2w(1001))
тысяча один
>>> print(n2w(2012))
две тысячи двенадцать

>>> print(n2w(12519.85))
двенадцать тысяч пятьсот девятнадцать запятая восемьдесят пять

>>> print(fill(n2w(1234567890)))
миллиард двести тридцать четыре миллиона пятьсот шестьдесят семь тысяч
восемьсот девяносто

>>> print(fill(n2w(215461407892039002157189883901676)))
двести пятнадцать нониллионов четыреста шестьдесят один октиллион
четыреста семь септиллионов восемьсот девяносто два секстиллиона
тридцать девять квинтиллионов два квадриллиона сто пятьдесят семь
триллионов сто восемьдесят девять миллиардов восемьсот восемьдесят три
миллиона девятьсот одна тысяча шестьсот семьдесят шесть

>>> print(fill(n2w(719094234693663034822824384220291)))
семьсот девятнадцать нониллионов девяносто четыре октиллиона двести
тридцать четыре септиллиона шестьсот девяносто три секстиллиона
шестьсот шестьдесят три квинтиллиона тридцать четыре квадриллиона
восемьсот двадцать два триллиона восемьсот двадцать четыре миллиарда
триста восемьдесят четыре миллиона двести двадцать тысяч двести
девяносто один

>>> print(to_currency(1.0, 'EUR'))
один евро, ноль центов

>>> print(to_currency(1.0, 'RUB'))
один рубль, ноль копеек

>>> print(to_currency(1234.56, 'EUR'))
тысяча двести тридцать четыре евро, пятьдесят шесть центов

>>> print(to_currency(1234.56, 'RUB'))
тысяча двести тридцать четыре рубля, пятьдесят шесть копеек

>>> print(to_currency(10111, 'EUR', seperator=u' и'))
сто один евро и одиннадцать центов

>>> print(to_currency(10121, 'RUB', seperator=u' и'))
сто один рубль и двадцать одна копейка

>>> print(to_currency(10122, 'RUB', seperator=u' и'))
сто один рубль и двадцать две копейки

>>> print(to_currency(10121, 'EUR', seperator=u' и'))
сто один евро и двадцать один цент

>>> print(to_currency(-1251985, cents = False))
минус двенадцать тысяч пятьсот девятнадцать евро, 85 центов
"""
from __future__ import unicode_literals

ZERO = (u'ноль',)

ONES_FEMININE = {
    1: (u'одна',),
    2: (u'две',),
    3: (u'три',),
    4: (u'четыре',),
    5: (u'пять',),
    6: (u'шесть',),
    7: (u'семь',),
    8: (u'восемь',),
    9: (u'девять',),
}

ONES = {
    1: (u'один',),
    2: (u'два',),
    3: (u'три',),
    4: (u'четыре',),
    5: (u'пять',),
    6: (u'шесть',),
    7: (u'семь',),
    8: (u'восемь',),
    9: (u'девять',),
}

TENS = {
    0: (u'десять',),
    1: (u'одиннадцать',),
    2: (u'двенадцать',),
    3: (u'тринадцать',),
    4: (u'четырнадцать',),
    5: (u'пятнадцать',),
    6: (u'шестнадцать',),
    7: (u'семнадцать',),
    8: (u'восемнадцать',),
    9: (u'девятнадцать',),
}

TWENTIES = {
    2: (u'двадцать',),
    3: (u'тридцать',),
    4: (u'сорок',),
    5: (u'пятьдесят',),
    6: (u'шестьдесят',),
    7: (u'семьдесят',),
    8: (u'восемьдесят',),
    9: (u'девяносто',),
}

HUNDREDS = {
    1: (u'сто',),
    2: (u'двести',),
    3: (u'триста',),
    4: (u'четыреста',),
    5: (u'пятьсот',),
    6: (u'шестьсот',),
    7: (u'семьсот',),
    8: (u'восемьсот',),
    9: (u'девятьсот',),
}

THOUSANDS = {
    1: (u'тысяча', u'тысячи', u'тысяч'), # 10^3
    2: (u'миллион', u'миллиона', u'миллионов'), # 10^6
    3: (u'миллиард', u'миллиарда', u'миллиардов'), # 10^9
    4: (u'триллион', u'триллиона', u'триллионов'), # 10^12
    5: (u'квадриллион', u'квадриллиона', u'квадриллионов'), # 10^15
    6: (u'квинтиллион', u'квинтиллиона', u'квинтиллионов'), # 10^18
    7: (u'секстиллион', u'секстиллиона', u'секстиллионов'), # 10^21
    8: (u'септиллион', u'септиллиона', u'септиллионов'), # 10^24
    9: (u'октиллион', u'октиллиона', u'октиллионов'), #10^27
    10: (u'нониллион', u'нониллиона', u'нониллионов'), # 10^30
}

CURRENCIES = {
    'RUB': (
        (u'рубль', u'рубля', u'рублей'), (u'копейка', u'копейки', u'копеек')
    ),
    'EUR': (
        (u'евро', u'евро', u'евро'), (u'цент', u'цента', u'центов')
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
    if (n % 100 < 10 or n % 100 > 20):
        if n % 10 == 1:
            form = 0
        elif (n % 10 > 1 and n % 10 < 5):
            form = 1
        else:
            form = 2
    else:
        form = 2
    return forms[form]


def int2word(n, feminine=False):
    if n < 0:
        return ' '.join([u'минус', int2word(abs(n))])

    if n == 0:
        return ZERO[0]

    words = []
    chunks = list(splitby3(str(n)))
    i = len(chunks)
    for x in chunks:
        i -= 1
        n1, n2, n3 = get_digits(x)

        if n3 > 0:
            words.append(HUNDREDS[n3][0])
            
        if n2 > 1:
            words.append(TWENTIES[n2][0])

        if n2 == 1:
            words.append(TENS[n1][0])
        elif n1 > 0 and not (i > 0 and x == 1):
            ones = ONES_FEMININE if i == 1 or feminine and i == 0 else ONES
            words.append(ones[n1][0])

        if i > 0:
            words.append(pluralize(x, THOUSANDS[i]))

    return ' '.join(words)


def n2w(n):
    n = str(n).replace(',', '.')
    if '.' in n:
        left, right = n.split('.')
        return u'%s запятая %s' % (int2word(int(left)), int2word(int(right)))
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
        minus_str = "минус "
    else:
        minus_str = ""

    if cents:
        cents_feminine = currency == 'RUB'
        cents_str = int2word(right, cents_feminine)
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


class Num2Word_RU(object):
    def to_cardinal(self, number):
        return n2w(number)

    def to_ordinal(self, number):
        raise NotImplementedError()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
