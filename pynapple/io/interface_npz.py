#!/usr/bin/env python

# -*- coding: utf-8 -*-
# @Author: Guillaume Viejo
# @Date:   2023-07-05 16:03:25
# @Last Modified by:   Guillaume Viejo
# @Last Modified time: 2024-04-02 14:32:25

"""
File classes help to validate and load pynapple objects or NWB files.
Data are always lazy-loaded.
Both classes behaves like dictionnary.
"""

import os

import numpy as np

from .. import core as nap


class NPZFile(object):
    """Class that points to a NPZ file that can be loaded as a pynapple object.
    Objects have a save function in npz format as well as the Folder class.

    Examples
    --------
    >>> import pynapple as nap
    >>> tsd = nap.load_file("path/to/my_tsd.npz")
    >>> tsd
    Time (s)
    0.0    0
    0.1    1
    0.2    2
    dtype: int64

    """

    def __init__(self, path):
        """Initialization of the NPZ file

        Parameters
        ----------
        path : str
            Valid path to a NPZ file
        """
        self.path = path
        self.name = os.path.basename(path)
        self.file = np.load(self.path, allow_pickle=True)
        self.type = ""

        # First check if type is explicitely defined
        possible = ["Ts", "Tsd", "TsdFrame", "TsdTensor", "TsGroup", "IntervalSet"]
        if "type" in self.file.keys():
            if len(self.file["type"]) == 1:
                if isinstance(self.file["type"][0], np.str_):
                    if self.file["type"] in possible:
                        self.type = self.file["type"][0]

        # Second check manually
        if self.type == "":
            k = set(self.file.keys())
            if {"t", "start", "end", "index"}.issubset(k):
                self.type = "TsGroup"
            elif {"t", "d", "start", "end", "columns"}.issubset(k):
                self.type = "TsdFrame"
            elif {"t", "d", "start", "end"}.issubset(k):
                if self.file["d"].ndim == 1:
                    self.type = "Tsd"
                else:
                    self.type = "TsdTensor"
            elif {"t", "start", "end"}.issubset(k):
                self.type = "Ts"
            elif {"start", "end"}.issubset(k):
                self.type = "IntervalSet"
            else:
                self.type = "npz"

    def load(self):
        """Load the NPZ file

        Returns
        -------
        (Tsd, Ts, TsdFrame, TsdTensor, TsGroup, IntervalSet)
            A pynapple object
        """
        if self.type == "npz":
            return self.file
        else:
            time_support = nap.IntervalSet(self.file["start"], self.file["end"])
            if self.type == "TsGroup":

                times = self.file["t"]
                index = self.file["index"]
                has_data = False
                if "d" in self.file.keys():
                    data = self.file["data"]
                    has_data = True

                if "keys" in self.file.keys():
                    keys = self.file["keys"]
                else:
                    keys = np.unique(index)

                group = {}
                for k in keys:
                    if has_data:
                        group[k] = nap.Tsd(
                            t=times[index == k],
                            d=data[index == k],
                            time_support=time_support,
                        )
                    else:
                        group[k] = nap.Ts(
                            t=times[index == k], time_support=time_support
                        )

                tsgroup = nap.TsGroup(
                    group, time_support=time_support, bypass_check=True
                )

                metainfo = {}
                for k in set(self.file.keys()) - {
                    "start",
                    "end",
                    "t",
                    "index",
                    "d",
                    "rate",
                    "keys",
                }:
                    tmp = self.file[k]
                    if len(tmp) == len(tsgroup):
                        metainfo[k] = tmp
                tsgroup.set_info(**metainfo)
                return tsgroup

            elif self.type == "TsdFrame":
                return nap.TsdFrame(
                    t=self.file["t"],
                    d=self.file["d"],
                    time_support=time_support,
                    columns=self.file["columns"],
                )
            elif self.type == "TsdTensor":
                return nap.TsdTensor(
                    t=self.file["t"], d=self.file["d"], time_support=time_support
                )
            elif self.type == "Tsd":
                return nap.Tsd(
                    t=self.file["t"], d=self.file["d"], time_support=time_support
                )
            elif self.type == "Ts":
                return nap.Ts(t=self.file["t"], time_support=time_support)
            elif self.type == "IntervalSet":
                return time_support
            else:
                return self.file
