from __future__ import absolute_import
from __future__ import division
# Copyright (c) 2010-2017 openpyxl

from io import BytesIO
from .drawing import Drawing
from openpyxl.compat import deprecated


def bounding_box(bw, bh, w, h):
    """
    Returns a tuple (new_width, new_height) which has the property
    that it fits within box_width and box_height and has (close to)
    the same aspect ratio as the original size
    """
    new_width, new_height = w, h
    if bw and new_width > bw:
        new_width = bw
        new_height = new_width / (w / h)
    if bh and new_height > bh:
        new_height = bh
        new_width = new_height * (w / h)
    return (new_width, new_height)


def _import_image(img):
    try:
        try:
            import Image as PILImage
        except ImportError:
            from PIL import Image as PILImage
    except ImportError:
        raise ImportError('You must install PIL to fetch image objects')

    if not isinstance(img, PILImage.Image):
        img = PILImage.open(img)

    return img


class Image(object):
    """ Raw Image class """

    _id = 1
    _path = "/xl/media/image{0}.{1}"

    def __init__(self, img, coordinates=((0, 0), (1, 1)), size=(None, None),
                 nochangeaspect=True, nochangearrowheads=True):

        self.ref = img

        # don't keep the image open
        image = _import_image(img)
        self.format = image.format.lower()
        self.nochangeaspect = nochangeaspect # deprecated
        self.nochangearrowheads = nochangearrowheads # deprecated

        newsize = bounding_box(
            size[0], size[1],
            image.size[0], image.size[1]
        )
        size = newsize

        # the containing drawing
        self.drawing = Drawing()
        self.drawing.coordinates = coordinates # deprecated
        self.drawing.width = size[0]
        self.drawing.height = size[1]


    @deprecated("Anchors can be passed in when an image is added to a worksheet")
    def anchor(self, cell, anchortype="absolute"):
        """ anchors the image to the given cell
            optional parameter anchortype supports 'absolute' or 'oneCell'"""
        self.drawing.anchortype = anchortype
        if anchortype == "absolute":
            self.drawing.left, self.drawing.top = cell.anchor
            return ((cell.column, cell.row),
                    cell.parent.point_pos(self.drawing.top + self.drawing.height,
                                          self.drawing.left + self.drawing.width))
        elif anchortype == "oneCell":
            self.drawing.anchorcol = cell.col_idx - 1
            self.drawing.anchorrow = cell.row - 1
            return ((self.drawing.anchorcol, self.drawing.anchorrow), None)
        else:
            raise ValueError("unknown anchortype %s" % anchortype)


    def _data(self):
        """
        Open image and write it to a buffer when saving the workbook
        """
        img = _import_image(self.ref)
        fp = None
        # don't convert these file formats
        if self.format in ['gif', 'jpeg', 'png']:
            if img.fp:
                img.fp.seek(0)
                fp = img.fp
        if not fp:
            fp = BytesIO()
            img.save(fp, format=self.format)

        return fp.read()


    @property
    def path(self):
        return self._path.format(self._id, self.format)
