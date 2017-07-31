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

from __future__ import division, unicode_literals
import re

from . import lang_EU


class Num2Word_PT_BR(lang_EU.Num2Word_EU):
    def set_high_numwords(self, high):
        max = 3 + 3*len(high)
        for word, n in zip(high, range(max, 3, -3)):
            self.cards[10**n] = word + "ilhão"

    def setup(self):
        self.negword = "menos "
        self.pointword = "vírgula"
        self.errmsg_nornum = "Somente números podem ser convertidos para palavras"
        self.exclude_title = ["e", "vírgula", "menos"]

        self.mid_numwords = [
            (1000, "mil"), (100, "cem"), (90, "noventa"),
            (80, "oitenta"), (70, "setenta"), (60, "sessenta"), (50, "cinquenta"),
            (40, "quarenta"), (30, "trinta")
        ]
        self.low_numwords = [
            "vinte", "dezenove", "dezoito", "dezessete", "dezesseis",
            "quinze", "catorze", "treze", "doze", "onze", "dez",
            "nove", "oito", "sete", "seis", "cinco", "quatro", "três", "dois",
            "um", "zero"
        ]
        self.ords = [
            {
                0: "",
                1: "primeiro",
                2: "segundo",
                3: "terceiro",
                4: "quarto",
                5: "quinto",
                6: "sexto",
                7: "sétimo",
                8: "oitavo",
                9: "nono",
            },
            {
                0: "",
                1: "décimo",
                2: "vigésimo",
                3: "trigésimo",
                4: "quadragésimo",
                5: "quinquagésimo",
                6: "sexagésimo",
                7: "septuagésimo",
                8: "octogésimo",
                9: "nonagésimo",
            },
            {
                0: "",
                1: "centésimo",
                2: "ducentésimo",
                3: "tricentésimo",
                4: "quadrigentésimo",
                5: "quingentésimo",
                6: "seiscentésimo",
                7: "septigentésimo",
                8: "octigentésimo",
                9: "nongentésimo",
            },
        ]
        self.thousand_separators = {
            3: "milésimo",
            6: "milionésimo",
            9: "bilionésimo",
            12: "trilionésimo",
            15: "quadrilionésimo"
        }
        self.hundreds = {
            1: "cento",
            2: "duzentos",
            3: "trezentos",
            4: "quatrocentos",
            5: "quinhentos",
            6: "seiscentos",
            7: "setecentos",
            8: "oitocentos",
            9: "novecentos",
        }

    def merge(self, curr, next):
        ctext, cnum, ntext, nnum = curr + next

        if cnum == 1:
            if nnum < 1000000:
                return next
            ctext = "um"
        elif cnum == 100 and not nnum == 1000:
            ctext = "cento"

        if nnum < cnum:
            if cnum < 100:
                return ("%s e %s" % (ctext, ntext), cnum + nnum)
            return ("%s e %s" % (ctext, ntext), cnum + nnum)

        elif (not nnum % 1000000) and cnum > 1:
            ntext = ntext[:-4] + "lhões"

        if nnum == 100:
            ctext = self.hundreds[cnum]
            ntext = ""

        else:
            ntext = " " + ntext

        return (ctext + ntext, cnum * nnum)

    def to_cardinal(self, value):
        result = super(Num2Word_PT_BR, self).to_cardinal(value)

        # Transforms "mil E cento e catorze reais" into "mil, cento e catorze reais"
        for ext in (
                'mil', 'milhão', 'milhões', 'bilhão', 'bilhões',
                'trilhão', 'trilhões', 'quatrilhão', 'quatrilhões'):
            if re.match('.*{} e \w*ento'.format(ext), result):
                result = result.replace('{} e'.format(ext), '{},'.format(ext), 1)

        return result

    def to_ordinal(self, value):
        self.verify_ordinal(value)

        result = []
        value = str(value)
        thousand_separator = ''

        for idx, char in enumerate(value[::-1]):
            if idx and idx % 3 == 0:
                thousand_separator = self.thousand_separators[idx]

            if char != '0' and thousand_separator:
                # avoiding "segundo milionésimo milésimo" for 6000000, for instance
                result.append(thousand_separator)
                thousand_separator = ''

            result.append(self.ords[idx % 3][int(char)])

        result = ' '.join(result[::-1])
        result = result.strip()
        result = re.sub('\s+', ' ', result)

        if result.startswith('primeiro') and value != '1':
            # avoiding "primeiro milésimo", "primeiro milionésimo" and so on
            result = result[9:]

        return result

    def to_ordinal_num(self, value):
        self.verify_ordinal(value)
        return "%sº" % (value)

    def to_year(self, val, longval=True):
        if val < 0:
            return self.to_cardinal(abs(val)) + ' antes de Cristo'
        return self.to_cardinal(val)

    def to_currency(self, val, longval=True):
        integer_part, decimal_part = ('%.2f' % val).split('.')

        result = self.to_cardinal(int(integer_part))

        appended_currency = False
        for ext in (
                'milhão', 'milhões', 'bilhão', 'bilhões',
                'trilhão', 'trilhões', 'quatrilhão', 'quatrilhões'):
            if result.endswith(ext):
                result += ' de reais'
                appended_currency = True

        if result in ['um', 'menos um']:
            result += ' real'
            appended_currency = True
        if not appended_currency:
            result += ' reais'

        if int(decimal_part):
            cents = self.to_cardinal(int(decimal_part))
            result += ' e ' + cents

            if cents == 'um':
                result += ' centavo'
            else:
                result += ' centavos'

        return result
