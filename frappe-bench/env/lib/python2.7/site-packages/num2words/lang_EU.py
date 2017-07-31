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
from .base import Num2Word_Base

class Num2Word_EU(Num2Word_Base):
    def set_high_numwords(self, high):
        max = 3 + 6*len(high)

        for word, n in zip(high, range(max, 3, -6)):
            self.cards[10**n] = word + "illiard"
            self.cards[10**(n-3)] = word + "illion"

        
    def base_setup(self):
        lows = ["non","oct","sept","sext","quint","quadr","tr","b","m"]
        units = ["", "un", "duo", "tre", "quattuor", "quin", "sex", "sept",
                 "octo", "novem"]
        tens = ["dec", "vigint", "trigint", "quadragint", "quinquagint",
                "sexagint", "septuagint", "octogint", "nonagint"]
        self.high_numwords = ["cent"]+self.gen_high_numwords(units, tens, lows)

    def to_currency(self, val, longval=True, jointxt=""):
        return self.to_splitnum(val, hightxt="Euro/s", lowtxt="Euro cent/s",
                                jointxt=jointxt, longval=longval)

