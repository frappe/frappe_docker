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

from __future__ import division, unicode_literals
from . import lang_EU

class Num2Word_EN(lang_EU.Num2Word_EU):
    def set_high_numwords(self, high):
        max = 3 + 3*len(high)
        for word, n in zip(high, range(max, 3, -3)):
            self.cards[10**n] = word + "illion"

    def setup(self):
        self.negword = "minus "
        self.pointword = "point"
        self.errmsg_nornum = "Only numbers may be converted to words."
        self.exclude_title = ["and", "point", "minus"]

        self.mid_numwords = [(1000, "thousand"), (100, "hundred"),
                             (90, "ninety"), (80, "eighty"), (70, "seventy"),
                             (60, "sixty"), (50, "fifty"), (40, "forty"),
                             (30, "thirty")]
        self.low_numwords = ["twenty", "nineteen", "eighteen", "seventeen",
                             "sixteen", "fifteen", "fourteen", "thirteen",
                             "twelve", "eleven", "ten", "nine", "eight",
                             "seven", "six", "five", "four", "three", "two",
                             "one", "zero"]
        self.ords = { "one"    : "first",
                      "two"    : "second",
                      "three"  : "third",
                      "five"   : "fifth",
                      "eight"  : "eighth",
                      "nine"   : "ninth",
                      "twelve" : "twelfth" }


    def merge(self, (ltext, lnum), (rtext, rnum)):
        if lnum == 1 and rnum < 100:
            return (rtext, rnum)
        elif 100 > lnum > rnum :
            return ("%s-%s"%(ltext, rtext), lnum + rnum)
        elif lnum >= 100 > rnum:
            return ("%s and %s"%(ltext, rtext), lnum + rnum)
        elif rnum > lnum:
            return ("%s %s"%(ltext, rtext), lnum * rnum)
        return ("%s, %s"%(ltext, rtext), lnum + rnum)


    def to_ordinal(self, value):
        self.verify_ordinal(value)
        outwords = self.to_cardinal(value).split(" ")
        lastwords = outwords[-1].split("-")
        lastword = lastwords[-1].lower()
        try:
            lastword = self.ords[lastword]
        except KeyError:
            if lastword[-1] == "y":
                lastword = lastword[:-1] + "ie" 
            lastword += "th"
        lastwords[-1] = self.title(lastword) 
        outwords[-1] = "-".join(lastwords)
        return " ".join(outwords)


    def to_ordinal_num(self, value):
        self.verify_ordinal(value)
        return "%s%s"%(value, self.to_ordinal(value)[-2:])


    def to_year(self, val, longval=True):
        if not (val//100)%10:
            return self.to_cardinal(val)
        return self.to_splitnum(val, hightxt="hundred", jointxt="and",
                                longval=longval)

    def to_currency(self, val, longval=True):
        return self.to_splitnum(val, hightxt="dollar/s", lowtxt="cent/s",
                                jointxt="and", longval=longval, cents = True)


n2w = Num2Word_EN()
to_card = n2w.to_cardinal
to_ord = n2w.to_ordinal
to_ordnum = n2w.to_ordinal_num
to_year = n2w.to_year

def main():
    for val in [ 1, 11, 12, 21, 31, 33, 71, 80, 81, 91, 99, 100, 101, 102, 155,
             180, 300, 308, 832, 1000, 1001, 1061, 1100, 1500, 1701, 3000,
             8280, 8291, 150000, 500000, 1000000, 2000000, 2000001,
             -21212121211221211111, -2.121212, -1.0000100]:
        n2w.test(val)
    n2w.test(1325325436067876801768700107601001012212132143210473207540327057320957032975032975093275093275093270957329057320975093272950730)
    for val in [1,120,1000,1120,1800, 1976,2000,2010,2099,2171]:
        print val, "is", n2w.to_currency(val)
        print val, "is", n2w.to_year(val)
    

if __name__ == "__main__":
    main()
