from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

import numpy
from pandas import Timestamp


def dataframe_to_rows(df, index=True, header=True):
    """
    Convert a Pandas dataframe into something suitable for passing into a worksheet
    """
    blocks = df._data.blocks
    ncols = sum(b.shape[0] for b in blocks)
    data = [None] * ncols

    for b in blocks:
        values = b.values

        if b.dtype.type == numpy.datetime64:
            values = numpy.array([Timestamp(v) for v in values.ravel()])
            values = values.reshape(b.shape)

        result = values.tolist()

        for col_loc, col in zip(b.mgr_locs, result):
            data[col_loc] = col

    if header:
        values = list(df.columns.values)
        if df.columns.dtype.type == numpy.datetime64:
            values = [Timestamp(v) for v in values]
        yield [None]*index + values

    for idx, v in enumerate(df.index):
        yield [v]*index + [data[j][idx] for j in range(ncols)]
