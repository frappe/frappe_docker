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
from num2words import lang_EU

class Num2Word_DK(lang_EU.Num2Word_EU):
    def set_high_numwords(self, high):
        max = 3 + 6*len(high)
        for word, n in zip(high, range(max, 3, -6)):
            self.cards[10**n] = word + "illarder"
            self.cards[10**(n-3)] = word + "illioner"

    def setup(self):
        self.negword = "minus "
        self.pointword = "komma"
        self.errmsg_nornum = "Kun tal kan blive konverteret til ord."
        self.exclude_title = ["og", "komma", "minus"]

        self.mid_numwords = [(1000, "tusind"), (100, "hundrede"),
                             (90, "halvfems"), (80, "firs"), (70, "halvfjerds"),
                             (60, "treds"), (50, "halvtreds"), (40, "fyrre"),
                             (30, "tredive")]
        self.low_numwords = ["tyve", "nitten", "atten", "sytten",
                             "seksten", "femten", "fjorten", "tretten",
                             "tolv", "elleve", "ti", "ni", "otte",
                             "syv", "seks", "fem", "fire", "tre", "to",
                             "et", "nul"]
        self.ords = { "nul"   : "nul",
                      "et"    : "f\xf8rste",
                      "to"    : "anden",
                      "tre"  : "tredje",
                      "fire" : "fjerde",
                      "fem"   : "femte",
                      "seks" : "sjette",
                      "syv" : "syvende",
                      "otte" : "ottende",
                      "ni" : "niende",
                      "ti" : "tiende",
                      "elleve" : "ellevte",
                      "tolv" : "tolvte",
                      "tretten" : "trett",
                      "fjorten" : "fjort",
                      "femten" : "femt",
                      "seksten" : "sekst",
                      "sytten"  : "sytt",
                      "atten" : "att",
                      "nitten" : "nitt",
                      "tyve" : "tyv"}

    def merge(self, curr, next):
        ctext, cnum, ntext, nnum = curr + next
        if next[1] == 100 or next[1] == 1000:
            lst = list(next)
            lst[0] = 'et' + lst[0]
            next = tuple(lst)

        if cnum == 1:
            if nnum < 10**6 or self.ordflag:
                return next
            ctext = "en"
        if nnum > cnum:
            if nnum >= 10**6:
                ctext += " "
            val = cnum * nnum
        else:
            if cnum >= 100 and cnum < 1000:
                ctext += " og "
            elif cnum >= 1000 and cnum <= 100000:
                ctext += "e og "
            if nnum < 10 < cnum < 100:
                if nnum == 1:
                    ntext = "en"
                ntext, ctext =  ctext, ntext + "og"
            elif cnum >= 10**6:
                ctext += " "
            val = cnum + nnum
        word = ctext + ntext
        return (word, val)


    def to_ordinal(self, value):
        self.verify_ordinal(value)
        self.ordflag = True
        outword = self.to_cardinal(value)
        self.ordflag = False
        for key in self.ords:
            if outword.endswith(key):
                outword = outword[:len(outword) - len(key)] + self.ords[key]
                break
        if value %100 >= 30 and value %100 <= 39 or value %100 == 0:
            outword += "te"
        elif value % 100 > 12 or value %100 == 0:
            outword += "ende"
        return outword

    def to_ordinal_num(self, value):
        self.verify_ordinal(value)
        vaerdte = (0,1,5,6,11,12)
        if value %100 >= 30 and value %100 <= 39 or value % 100 in vaerdte:
            return str(value) + "te"
        elif value % 100 == 2:
            return str(value) + "en"
        return str(value) + "ende"


    def to_currency(self, val, longval=True):
        if val//100 == 1 or val == 1:
             ret = self.to_splitnum(val, hightxt="kr", lowtxt="\xf8re",
                                    jointxt="og",longval=longval)
             return "en " + ret[3:]
        return self.to_splitnum(val, hightxt="kr", lowtxt="\xf8re",
                                    jointxt="og",longval=longval)

    def to_year(self, val, longval=True):
        if val == 1:
            return 'en'
        if not (val//100)%10:
            return self.to_cardinal(val)
        return self.to_splitnum(val, hightxt="hundrede", longval=longval)

n2w = Num2Word_DK()
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
    for val in [1,120, 160, 1000,1120,1800, 1976,2000,2010,2099,2171]:
        print val, "er", n2w.to_currency(val)
        print val, "er", n2w.to_year(val)
    n2w.test(65132)

if __name__ == "__main__":
    main()
