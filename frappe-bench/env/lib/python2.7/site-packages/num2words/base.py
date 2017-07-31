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

from __future__ import unicode_literals
from .orderedmapping import OrderedMapping


class Num2Word_Base(object):
    def __init__(self):
        self.cards = OrderedMapping()
        self.is_title = False
        self.precision = 2
        self.exclude_title = []
        self.negword = "(-) "
        self.pointword = "(.)"
        self.errmsg_nonnum = "type(%s) not in [long, int, float]"
        self.errmsg_floatord = "Cannot treat float %s as ordinal."
        self.errmsg_negord = "Cannot treat negative num %s as ordinal."
        self.errmsg_toobig = "abs(%s) must be less than %s."

        self.base_setup()
        self.setup()
        self.set_numwords()

        self.MAXVAL = 1000 * self.cards.order[0]


    def set_numwords(self):
        self.set_high_numwords(self.high_numwords)
        self.set_mid_numwords(self.mid_numwords)
        self.set_low_numwords(self.low_numwords)


    def gen_high_numwords(self, units, tens, lows):
        out = [u + t for t in tens for u in units]
        out.reverse()
        return out + lows


    def set_mid_numwords(self, mid):
        for key, val in mid:
            self.cards[key] = val


    def set_low_numwords(self, numwords):
        for word, n in zip(numwords, range(len(numwords) - 1, -1, -1)):
            self.cards[n] = word


    def splitnum(self, value):
        for elem in self.cards:
            if elem > value:
                continue

            out = []
            if value == 0:
                div, mod = 1, 0
            else:
                div, mod = divmod(value, elem)

            if div == 1:
                out.append((self.cards[1], 1))
            else:
                if div == value:  # The system tallies, eg Roman Numerals
                    return [(div * self.cards[elem], div*elem)]
                out.append(self.splitnum(div))

            out.append((self.cards[elem], elem))

            if mod:
                out.append(self.splitnum(mod))

            return out


    def to_cardinal(self, value):
        try:
            assert long(value) == value
        except (ValueError, TypeError, AssertionError):
            return self.to_cardinal_float(value)

        self.verify_num(value)

        out = ""
        if value < 0:
            value = abs(value)
            out = self.negword

        if value >= self.MAXVAL:
            raise OverflowError(self.errmsg_toobig % (value, self.MAXVAL))

        val = self.splitnum(value)
        words, num = self.clean(val)
        return self.title(out + words)


    def to_cardinal_float(self, value):
        try:
            float(value) == value
        except (ValueError, TypeError, AssertionError):
            raise TypeError(self.errmsg_nonnum % value)

        pre = int(value)
        post = str(abs(value - pre) * 10**self.precision)
        post = '0' * (self.precision - len(post.split('.')[0])) + post

        out = [self.to_cardinal(pre)]
        if self.precision:
            out.append(self.title(self.pointword))

        for i in range(self.precision):
            curr = int(post[i])
            out.append(unicode(self.to_cardinal(curr)))

        return " ".join(out)


    def merge(self, curr, next):
        raise NotImplementedError


    def clean(self, val):
        out = val
        while len(val) != 1:
            out = []
            left, right = val[:2]
            if isinstance(left, tuple) and isinstance(right, tuple):
                out.append(self.merge(left, right))
                if val[2:]:
                    out.append(val[2:])
            else:
                for elem in val:
                    if isinstance(elem, list):
                        if len(elem) == 1:
                            out.append(elem[0])
                        else:
                            out.append(self.clean(elem))
                    else:
                        out.append(elem)
            val = out
        return out[0]


    def title(self, value):
        if self.is_title:
            out = []
            value = value.split()
            for word in value:
                if word in self.exclude_title:
                    out.append(word)
                else:
                    out.append(word[0].upper() + word[1:])
            value = " ".join(out)
        return value


    def verify_ordinal(self, value):
        if not value == long(value):
            raise TypeError, self.errmsg_floatord %(value)
        if not abs(value) == value:
            raise TypeError, self.errmsg_negord %(value)


    def verify_num(self, value):
        return 1


    def set_wordnums(self):
        pass

            
    def to_ordinal(self, value):
        return self.to_cardinal(value)


    def to_ordinal_num(self, value):
        return value


    # Trivial version
    def inflect(self, value, text):
        text = text.split("/")
        if value == 1:
            return text[0]
        return "".join(text)


    #//CHECK: generalise? Any others like pounds/shillings/pence?
    def to_splitnum(self, val, hightxt="", lowtxt="", jointxt="",
                    divisor=100, longval=True, cents = True):
        out = []
        try:
            high, low = val
        except TypeError:
            high, low = divmod(val, divisor)
        if high:
            hightxt = self.title(self.inflect(high, hightxt))
            out.append(self.to_cardinal(high))
            if low:
                if longval:
                    if hightxt:
                        out.append(hightxt)
                    if jointxt:
                        out.append(self.title(jointxt))
            elif hightxt:
                out.append(hightxt)
        if low:
            if cents:
                out.append(self.to_cardinal(low))
            else:
                out.append("%02d" % low)
            if lowtxt and longval:
                out.append(self.title(self.inflect(low, lowtxt)))
        return " ".join(out)


    def to_year(self, value, **kwargs):
        return self.to_cardinal(value)


    def to_currency(self, value, **kwargs):
        return self.to_cardinal(value)


    def base_setup(self):
        pass


    def setup(self):
        pass


    def test(self, value):
        try:
            _card = self.to_cardinal(value)
        except:
            _card = "invalid"

        try:
            _ord = self.to_ordinal(value)
        except:
            _ord = "invalid"

        try:
            _ordnum = self.to_ordinal_num(value)
        except:
            _ordnum = "invalid"

        print ("For %s, card is %s;\n\tord is %s; and\n\tordnum is %s." %
                    (value, _card, _ord, _ordnum))
