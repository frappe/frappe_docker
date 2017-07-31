# -*- coding: utf-8 -*-
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
from .lang_EU import Num2Word_EU

class Num2Word_DE(Num2Word_EU):
    def set_high_numwords(self, high):
        max = 3 + 6*len(high)

        for word, n in zip(high, range(max, 3, -6)):
            self.cards[10**n] = word + "illiarde"
            self.cards[10**(n-3)] = word + "illion"

    def setup(self):
        self.negword = "minus "
        self.pointword = "Komma"
        self.errmsg_floatord = "Die Gleitkommazahl %s kann nicht in eine Ordnungszahl konvertiert werden." # "Cannot treat float %s as ordinal."
        self.errmsg_nonnum = "Nur Zahlen (type(%s)) können in Wörter konvertiert werden." # "type(((type(%s)) ) not in [long, int, float]"
        self.errmsg_negord = "Die negative Zahl %s kann nicht in eine Ordnungszahl konvertiert werden." # "Cannot treat negative num %s as ordinal."
        self.errmsg_toobig = "Die Zahl %s muss kleiner als %s sein." # "abs(%s) must be less than %s."
        self.exclude_title = []

        lows = ["non", "okt", "sept", "sext", "quint", "quadr", "tr", "b", "m"]
        units = ["", "un", "duo", "tre", "quattuor", "quin", "sex", "sept",
                 "okto", "novem"]
        tens = ["dez", "vigint", "trigint", "quadragint", "quinquagint",
                "sexagint", "septuagint", "oktogint", "nonagint"]
        self.high_numwords = ["zent"]+self.gen_high_numwords(units, tens, lows)
        self.mid_numwords = [(1000, "tausend"), (100, "hundert"),
                             (90, "neunzig"), (80, "achtzig"), (70, "siebzig"),
                             (60, "sechzig"), (50, "f\xFCnfzig"), (40, "vierzig"),
                             (30, "drei\xDFig")]
        self.low_numwords = ["zwanzig", "neunzehn", "achtzehn", "siebzehn",
                             "sechzehn", "f\xFCnfzehn", "vierzehn", "dreizehn",
                             "zw\xF6lf", "elf", "zehn", "neun", "acht", "sieben",
                             "sechs", "f\xFCnf", "vier", "drei", "zwei", "eins",
                             "null"]
        self.ords = {"eins": "ers",
                     "drei": "drit",
                     "acht": "ach",
                     "sieben": "sieb",
                     "ig": "igs",
                     "ert": "erts",
                     "end": "ends",
                     "ion": "ions",
                     "nen": "nens",
                     "rde": "rdes",
                     "rden": "rdens"}

    def merge(self, curr, next):
        ctext, cnum, ntext, nnum = curr + next

        if cnum == 1:
            if nnum < 10**6:
                return next
            ctext = "eine"

        if nnum > cnum:
            if nnum >= 10**6:
                if cnum > 1:
                    if ntext.endswith("e"):
                        ntext += "n"
                    else:
                        ntext += "en"
                ctext += " "
            val = cnum * nnum
        else:
            if nnum < 10 < cnum < 100:
                if nnum == 1:
                    ntext = "ein"
                ntext, ctext = ctext, ntext + "und"
            elif cnum >= 10**6:
                ctext += " "
            val = cnum + nnum

        word = ctext + ntext
        return (word, val)

    def to_ordinal(self, value):
        self.verify_ordinal(value)
        outword = self.to_cardinal(value)
        for key in self.ords:
            if outword.endswith(key):
                outword = outword[:len(outword) - len(key)] + self.ords[key]
                break
        return outword + "te"

    def to_ordinal_num(self, value):
        self.verify_ordinal(value)
        return str(value) + "."

    def to_currency(self, val, longval=True, old=False):
        if old:
            return self.to_splitnum(val, hightxt="mark/s", lowtxt="pfennig/e",
                                    jointxt="und",longval=longval)
        return super(Num2Word_DE, self).to_currency(val, jointxt="und",
                                                    longval=longval)

    def to_year(self, val, longval=True):
        if not (val//100)%10:
            return self.to_cardinal(val)
        return self.to_splitnum(val, hightxt="hundert", longval=longval)

n2w = Num2Word_DE()
to_card = n2w.to_cardinal
to_ord = n2w.to_ordinal
to_ordnum = n2w.to_ordinal_num


def main():
    for val in [1, 7, 8, 12, 17, 81, 91, 99, 100, 101, 102, 155,
             180, 300, 308, 832, 1000, 1001, 1061, 1100, 1500, 1701, 3000,
             8280, 8291, 150000, 500000, 3000000, 1000000, 2000001, 1000000000, 2000000000,
             -21212121211221211111, -2.121212, -1.0000100]:
        n2w.test(val)

    # n2w.test(1325325436067876801768700107601001012212132143210473207540327057320957032975032975093275093275093270957329057320975093272950730)
    n2w.test(3000000)
    n2w.test(3000000000001)
    n2w.test(3000000324566)
    print n2w.to_currency(112121)
    print n2w.to_year(2000)
    print n2w.to_year(1820)
    print n2w.to_year(2001)

if __name__ == "__main__":
    main()

