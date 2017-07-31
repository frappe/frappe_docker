from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.styles.colors import Color, BLACK, WHITE

from openpyxl.utils.units import (
    pixels_to_EMU,
    EMU_to_pixels,
    short_color,
)

from openpyxl.compat import deprecated
from openpyxl.xml.functions import Element, SubElement, tostring
from openpyxl.xml.constants import (
    DRAWING_NS,
    SHEET_DRAWING_NS,
    CHART_NS,
    CHART_DRAWING_NS,
    PKG_REL_NS
)
from openpyxl.compat.strings import safe_string


class Shape(object):
    """ a drawing inside a chart
        coordiantes are specified by the user in the axis units
    """

    MARGIN_LEFT = 6 + 13 + 1
    MARGIN_BOTTOM = 17 + 11

    FONT_WIDTH = 7
    FONT_HEIGHT = 8

    ROUND_RECT = 'roundRect'
    RECT = 'rect'

    # other shapes to define :
    '''
    "line"
    "lineInv"
    "triangle"
    "rtTriangle"
    "diamond"
    "parallelogram"
    "trapezoid"
    "nonIsoscelesTrapezoid"
    "pentagon"
    "hexagon"
    "heptagon"
    "octagon"
    "decagon"
    "dodecagon"
    "star4"
    "star5"
    "star6"
    "star7"
    "star8"
    "star10"
    "star12"
    "star16"
    "star24"
    "star32"
    "roundRect"
    "round1Rect"
    "round2SameRect"
    "round2DiagRect"
    "snipRoundRect"
    "snip1Rect"
    "snip2SameRect"
    "snip2DiagRect"
    "plaque"
    "ellipse"
    "teardrop"
    "homePlate"
    "chevron"
    "pieWedge"
    "pie"
    "blockArc"
    "donut"
    "noSmoking"
    "rightArrow"
    "leftArrow"
    "upArrow"
    "downArrow"
    "stripedRightArrow"
    "notchedRightArrow"
    "bentUpArrow"
    "leftRightArrow"
    "upDownArrow"
    "leftUpArrow"
    "leftRightUpArrow"
    "quadArrow"
    "leftArrowCallout"
    "rightArrowCallout"
    "upArrowCallout"
    "downArrowCallout"
    "leftRightArrowCallout"
    "upDownArrowCallout"
    "quadArrowCallout"
    "bentArrow"
    "uturnArrow"
    "circularArrow"
    "leftCircularArrow"
    "leftRightCircularArrow"
    "curvedRightArrow"
    "curvedLeftArrow"
    "curvedUpArrow"
    "curvedDownArrow"
    "swooshArrow"
    "cube"
    "can"
    "lightningBolt"
    "heart"
    "sun"
    "moon"
    "smileyFace"
    "irregularSeal1"
    "irregularSeal2"
    "foldedCorner"
    "bevel"
    "frame"
    "halfFrame"
    "corner"
    "diagStripe"
    "chord"
    "arc"
    "leftBracket"
    "rightBracket"
    "leftBrace"
    "rightBrace"
    "bracketPair"
    "bracePair"
    "straightConnector1"
    "bentConnector2"
    "bentConnector3"
    "bentConnector4"
    "bentConnector5"
    "curvedConnector2"
    "curvedConnector3"
    "curvedConnector4"
    "curvedConnector5"
    "callout1"
    "callout2"
    "callout3"
    "accentCallout1"
    "accentCallout2"
    "accentCallout3"
    "borderCallout1"
    "borderCallout2"
    "borderCallout3"
    "accentBorderCallout1"
    "accentBorderCallout2"
    "accentBorderCallout3"
    "wedgeRectCallout"
    "wedgeRoundRectCallout"
    "wedgeEllipseCallout"
    "cloudCallout"
    "cloud"
    "ribbon"
    "ribbon2"
    "ellipseRibbon"
    "ellipseRibbon2"
    "leftRightRibbon"
    "verticalScroll"
    "horizontalScroll"
    "wave"
    "doubleWave"
    "plus"
    "flowChartProcess"
    "flowChartDecision"
    "flowChartInputOutput"
    "flowChartPredefinedProcess"
    "flowChartInternalStorage"
    "flowChartDocument"
    "flowChartMultidocument"
    "flowChartTerminator"
    "flowChartPreparation"
    "flowChartManualInput"
    "flowChartManualOperation"
    "flowChartConnector"
    "flowChartPunchedCard"
    "flowChartPunchedTape"
    "flowChartSummingJunction"
    "flowChartOr"
    "flowChartCollate"
    "flowChartSort"
    "flowChartExtract"
    "flowChartMerge"
    "flowChartOfflineStorage"
    "flowChartOnlineStorage"
    "flowChartMagneticTape"
    "flowChartMagneticDisk"
    "flowChartMagneticDrum"
    "flowChartDisplay"
    "flowChartDelay"
    "flowChartAlternateProcess"
    "flowChartOffpageConnector"
    "actionButtonBlank"
    "actionButtonHome"
    "actionButtonHelp"
    "actionButtonInformation"
    "actionButtonForwardNext"
    "actionButtonBackPrevious"
    "actionButtonEnd"
    "actionButtonBeginning"
    "actionButtonReturn"
    "actionButtonDocument"
    "actionButtonSound"
    "actionButtonMovie"
    "gear6"
    "gear9"
    "funnel"
    "mathPlus"
    "mathMinus"
    "mathMultiply"
    "mathDivide"
    "mathEqual"
    "mathNotEqual"
    "cornerTabs"
    "squareTabs"
    "plaqueTabs"
    "chartX"
    "chartStar"
    "chartPlus"
    '''

    @deprecated("Chart Drawings need a complete rewrite")
    def __init__(self,
                 chart,
                 coordinates=((0, 0), (1, 1)),
                 text=None,
                 scheme="accent1"):
        self.chart = chart
        self.coordinates = coordinates  # in axis units
        self.text = text
        self.scheme = scheme
        self.style = Shape.RECT
        self.border_width = 0
        self.border_color = BLACK  # "F3B3C5"
        self.color = WHITE
        self.text_color = BLACK

    @property
    def border_color(self):
        return self._border_color

    @border_color.setter
    def border_color(self, color):
        self._border_color = short_color(color)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = short_color(color)

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, color):
        self._text_color = short_color(color)

    @property
    def border_width(self):
        return self._border_width

    @border_width.setter
    def border_width(self, w):
        self._border_width = w

    @property
    def coordinates(self):
        """Return coordindates in axis units"""
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coords):
        """ set shape coordinates in percentages (left, top, right, bottom)
        """
        # this needs refactoring to reflect changes in charts
        self.axis_coordinates = coords
        (x1, y1), (x2, y2) = coords # bottom left, top right
        drawing_width = pixels_to_EMU(self.chart.drawing.width)
        drawing_height = pixels_to_EMU(self.chart.drawing.height)
        plot_width = drawing_width * self.chart.width
        plot_height = drawing_height * self.chart.height

        margin_left = self.chart._get_margin_left() * drawing_width
        xunit = plot_width / self.chart.get_x_units()

        margin_top = self.chart._get_margin_top() * drawing_height
        yunit = self.chart.get_y_units()

        x_start = (margin_left + (float(x1) * xunit)) / drawing_width
        y_start = ((margin_top
                    + plot_height
                    - (float(y1) * yunit))
                    / drawing_height)

        x_end = (margin_left + (float(x2) * xunit)) / drawing_width
        y_end = ((margin_top
                  + plot_height
                  - (float(y2) * yunit))
                  / drawing_height)

        # allow user to specify y's in whatever order
        # excel expect y_end to be lower
        if y_end < y_start:
            y_end, y_start = y_start, y_end

        self._coordinates = (
            self._norm_pct(x_start), self._norm_pct(y_start),
            self._norm_pct(x_end), self._norm_pct(y_end)
        )

    @staticmethod
    def _norm_pct(pct):
        """ force shapes to appear by truncating too large sizes """
        if pct > 1:
            return 1
        elif pct < 0:
            return 0
        return pct


class ShapeWriter(object):
    """ one file per shape """

    def __init__(self, shapes):

        self._shapes = shapes

    def write(self, shape_id):

        root = Element('{%s}userShapes' % CHART_NS)

        for shape in self._shapes:
            anchor = SubElement(root, '{%s}relSizeAnchor' % CHART_DRAWING_NS)

            xstart, ystart, xend, yend = shape.coordinates

            _from = SubElement(anchor, '{%s}from' % CHART_DRAWING_NS)
            SubElement(_from, '{%s}x' % CHART_DRAWING_NS).text = str(xstart)
            SubElement(_from, '{%s}y' % CHART_DRAWING_NS).text = str(ystart)

            _to = SubElement(anchor, '{%s}to' % CHART_DRAWING_NS)
            SubElement(_to, '{%s}x' % CHART_DRAWING_NS).text = str(xend)
            SubElement(_to, '{%s}y' % CHART_DRAWING_NS).text = str(yend)

            sp = SubElement(anchor, '{%s}sp' % CHART_DRAWING_NS, {'macro':'', 'textlink':''})
            nvspr = SubElement(sp, '{%s}nvSpPr' % CHART_DRAWING_NS)
            SubElement(nvspr, '{%s}cNvPr' % CHART_DRAWING_NS, {'id':str(shape_id), 'name':'shape %s' % shape_id})
            SubElement(nvspr, '{%s}cNvSpPr' % CHART_DRAWING_NS)

            sppr = SubElement(sp, '{%s}spPr' % CHART_DRAWING_NS)
            frm = SubElement(sppr, '{%s}xfrm' % DRAWING_NS,)
            # no transformation
            SubElement(frm, '{%s}off' % DRAWING_NS, {'x':'0', 'y':'0'})
            SubElement(frm, '{%s}ext' % DRAWING_NS, {'cx':'0', 'cy':'0'})

            prstgeom = SubElement(sppr, '{%s}prstGeom' % DRAWING_NS, {'prst':str(shape.style)})
            SubElement(prstgeom, '{%s}avLst' % DRAWING_NS)

            fill = SubElement(sppr, '{%s}solidFill' % DRAWING_NS, )
            SubElement(fill, '{%s}srgbClr' % DRAWING_NS, {'val':shape.color})

            border = SubElement(sppr, '{%s}ln' % DRAWING_NS, {'w':str(shape._border_width)})
            sf = SubElement(border, '{%s}solidFill' % DRAWING_NS)
            SubElement(sf, '{%s}srgbClr' % DRAWING_NS, {'val':shape.border_color})

            self._write_style(sp)
            self._write_text(sp, shape)

            shape_id += 1

        return tostring(root)

    def _write_text(self, node, shape):
        """ write text in the shape """

        tx_body = SubElement(node, '{%s}txBody' % CHART_DRAWING_NS)
        SubElement(tx_body, '{%s}bodyPr' % DRAWING_NS, {'vertOverflow':'clip'})
        SubElement(tx_body, '{%s}lstStyle' % DRAWING_NS)
        p = SubElement(tx_body, '{%s}p' % DRAWING_NS)
        if shape.text:
            r = SubElement(p, '{%s}r' % DRAWING_NS)
            rpr = SubElement(r, '{%s}rPr' % DRAWING_NS, {'lang':'en-US'})
            fill = SubElement(rpr, '{%s}solidFill' % DRAWING_NS)
            SubElement(fill, '{%s}srgbClr' % DRAWING_NS, {'val':shape.text_color})

            SubElement(r, '{%s}t' % DRAWING_NS).text = shape.text
        else:
            SubElement(p, '{%s}endParaRPr' % DRAWING_NS, {'lang':'en-US'})

    def _write_style(self, node):
        """ write style theme """

        style = SubElement(node, '{%s}style' % CHART_DRAWING_NS)

        ln_ref = SubElement(style, '{%s}lnRef' % DRAWING_NS, {'idx':'2'})
        scheme_clr = SubElement(ln_ref, '{%s}schemeClr' % DRAWING_NS, {'val':'accent1'})
        SubElement(scheme_clr, '{%s}shade' % DRAWING_NS, {'val':'50000'})

        fill_ref = SubElement(style, '{%s}fillRef' % DRAWING_NS, {'idx':'1'})
        SubElement(fill_ref, '{%s}schemeClr' % DRAWING_NS, {'val':'accent1'})

        effect_ref = SubElement(style, '{%s}effectRef' % DRAWING_NS, {'idx':'0'})
        SubElement(effect_ref, '{%s}schemeClr' % DRAWING_NS, {'val':'accent1'})

        font_ref = SubElement(style, '{%s}fontRef' % DRAWING_NS, {'idx':'minor'})
        SubElement(font_ref, '{%s}schemeClr' % DRAWING_NS, {'val':'lt1'})
