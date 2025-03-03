#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zheng et al (2022) Dataset Tutorial
============

This tutorial demonstrates how we use Pynapple on various publicly available datasets in systems neuroscience to streamline analysis. In this tutorial, we will examine the dataset from [Zheng et al (2022)](https://www.nature.com/articles/s41593-022-01020-w), which was used to generate Figure 4c in the [publication](https://elifesciences.org/reviewed-preprints/85786).

The NWB file for the example used here is provided in [this](https://github.com/PeyracheLab/pynacollada/tree/main/pynacollada/Pynapple%20Paper%20Figures/Zheng%202022/000207/sub-4) repository. The entire dataset can be downloaded [here](https://dandiarchive.org/dandiset/000207/0.220216.0323).

See the [documentation](https://pynapple-org.github.io/pynapple/) of Pynapple for instructions on installing the package.

This tutorial was made by Dhruv Mehrotra.

First, import the necessary libraries:

"""

# %%
# !!! warning
#     This tutorial uses seaborn and matplotlib for displaying the figure as well as the dandi package
#
#     You can install all with `pip install matplotlib seaborn dandi dandischema`
#
# Now, import the necessary libraries:

import matplotlib.pyplot as plt
import numpy as np
import pynapple as nap
import seaborn as sns

# %%
# ***
# Stream the data from DANDI
# ------------------

from pynwb import NWBHDF5IO

from dandi.dandiapi import DandiAPIClient
import fsspec
from fsspec.implementations.cached import CachingFileSystem
import h5py

# Enter the session ID and path to the file
dandiset_id, filepath = ("000207", "sub-4/sub-4_ses-4_ecephys.nwb")

with DandiAPIClient() as client:
    asset = client.get_dandiset(dandiset_id, "draft").get_asset_by_path(filepath)
    s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

# first, create a virtual filesystem based on the http protocol
fs = fsspec.filesystem("http")

# create a cache to save downloaded data to disk (optional)
fs = CachingFileSystem(
    fs=fs,
    cache_storage="nwb-cache",  # Local folder for the cache
)

# next, open the file
file = h5py.File(fs.open(s3_url, "rb"))
io = NWBHDF5IO(file=file, load_namespaces=True)

# %%
# ***
# Parsing the data
# ------------------
#
# The first step is to load the data from the Neurodata Without Borders (NWB) file. This is done as follows:
#

custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", palette="colorblind", font_scale=1.5, rc=custom_params)

data = nap.NWBFile(io.read())  # Load the NWB file for this dataset

# What does this look like?
print(data)

# %%
# Get spike timings
spikes = data["units"]

# %%
# What does this look like?
print(spikes)

# %%
# This TsGroup has, among other information, the mean firing rate of the unit, the X, Y and Z coordinates, the brain region the unit was recorded from, and the channel number on which the unit was located.

# %%
# Next, let's get the encoding table of all stimulus times, as shown below:

encoding_table = data["encoding_table"]

# What does this look like?
print(encoding_table)

# %%
# This table has, among other things, the scene boundary times for which we will plot the peri-event time histogram (PETH).
#
# There are 3 types of scene boundaries in this data. For the purposes of demonstration, we will use only the "No boundary" (NB) and the "Hard boundary" (HB conditions). The encoding table has a stimCategory field, which tells us the type of boundary corresponding to a given trial.

stimCategory = np.array(
    encoding_table.stimCategory
)  # Get the scene boundary type for all trials

# What does this look like?
print(stimCategory)

# %%
# Trials marked 0 correspond to NB, while trials marked 2 correspond to HB. Let's extract the trial numbers for NB and HB trials, as shown below:

indxNB = np.where(stimCategory == 0)  # NB trial indices
indxHB = np.where(stimCategory == 2)  # HB trial indices

# %%
# The encoding table also has 3 types of boundary times. For the purposes of our demonstration, we will focus on boundary1 times, and extract them as shown below:

boundary1_time = np.array(encoding_table.boundary1_time)  # Get timings of Boundary1

# What does this look like?
print(boundary1_time)

# %%
# This contains the timings of all boundaries in this block of trials. Note that we also have the type of boundary for each trial. Let's store the NB and HB boundary timings in separate variables, as Pynapple Ts objects:

NB = nap.Ts(boundary1_time[indxNB])  # NB timings
HB = nap.Ts(boundary1_time[indxHB])  # HB timings


# %%
# ***
# Peri-Event Time Histogram (PETH)
# ------------------
#
# A PETH is a plot where we align a variable of interest (for example, spikes) to an external event (in this case, to boundary times). This visualization helps us infer relationships between the two.
#
# For our demonstration, we will align the spikes of the first unit, which is located in the hippocampus, to the times of NB and HB. You can do a quick check to verify that the first unit is indeed located in the hippocampus, we leave it to you.
#
# With Pynapple, PETHs can be computed with a single line of code!

NB_peth = nap.compute_perievent(
    spikes[0], NB, minmax=(-0.5, 1)
)  # Compute PETH of unit aligned to NB, for -0.5 to 1s windows
HB_peth = nap.compute_perievent(
    spikes[0], HB, minmax=(-0.5, 1)
)  # Compute PETH of unit aligned to HB, for -0.5 to 1s windows

# %%
# Let's plot the PETH

plt.figure(figsize =(15,8))
plt.subplot(211)  # Plot the figures in 2 rows
for i, n in enumerate(NB_peth):
    plt.plot(
        NB_peth[n].as_units("s").fillna(i),
        "o",
        color=[102 / 255, 204 / 255, 0 / 255],
        markersize=4,
    )  # Plot PETH
plt.axvline(0, linewidth=2, color="k", linestyle="--")  # Plot a line at t = 0
plt.yticks([0, 30])  # Set ticks on Y-axis
plt.gca().set_yticklabels(["1", "30"])  # Label the ticks
plt.xlabel("Time from NB (s)")  # Time from boundary in seconds, on X-axis
plt.ylabel("Trial Number")  # Trial number on Y-axis

plt.subplot(212)
for i, n in enumerate(HB_peth):
    plt.plot(
        HB_peth[n].as_units("s").fillna(i),
        "o",
        color=[255 / 255, 99 / 255, 71 / 255],
        markersize=4,
    )  # Plot PETH
plt.axvline(0, linewidth=2, color="k", linestyle="--")  # Plot a line at t = 0
plt.yticks([0, 30])  # Set ticks on Y-axis
plt.gca().set_yticklabels(["1", "30"])  # Label the ticks
plt.xlabel("Time from HB (s)")  # Time from boundary in seconds, on X-axis
plt.ylabel("Trial Number")  # Trial number on Y-axis
plt.subplots_adjust(wspace=0.2, hspace=0.5, top=0.85)

# %%
# Awesome! From the PETH, we can see that this neuron fires after boundary onset in HB trials. This is an example of what the authors describe [here](https://www.nature.com/articles/s41593-022-01020-w) as a boundary cell.

# %%
# ***
# PETH of firing rate for NB and HB cells
# ------------------
#
# Now that we have the PETH of spiking, we can go one step further. We will plot the mean firing rate of this cell aligned to the boundary for each trial type. Doing this in Pynapple is very simple!

bin_size = 0.2  # 200ms bin size
step_size = 0.01  # 10ms step size, to make overlapping bins
winsize = int(bin_size / step_size)  # Window size

# %%
# Use Pynapple to compute binned spike counts

counts_NB = NB_peth.count(step_size)  # Spike counts binned in 10ms steps, for NB trials
counts_HB = HB_peth.count(step_size)  # Spike counts binned in 10ms steps, for HB trials

# %%
# Smooth the binned spike counts using a window of size 20, for both trial types

counts_NB = (
    counts_NB.as_dataframe()
    .rolling(winsize, win_type="gaussian", min_periods=1, center=True, axis=0)
    .mean(std=0.2 * winsize)
)
counts_HB = (
    counts_HB.as_dataframe()
    .rolling(winsize, win_type="gaussian", min_periods=1, center=True, axis=0)
    .mean(std=0.2 * winsize)
)

# %%
# Compute firing rate for both trial types

fr_NB = counts_NB * winsize
fr_HB = counts_HB * winsize

# %%
# Compute the mean firing rate for both trial types

meanfr_NB = fr_NB.mean(axis=1)
meanfr_HB = fr_HB.mean(axis=1)

# %%
# Compute standard error of mean (SEM) of the firing rate for both trial types

error_NB = fr_NB.sem(axis=1)
error_HB = fr_HB.sem(axis=1)

# %%
# Plot the mean +/- SEM of firing rate for both trial types

plt.figure(figsize =(15,8))
plt.plot(
    meanfr_NB, color=[102 / 255, 204 / 255, 0 / 255], label="NB"
)  # Plot mean firing rate for NB trials

# Plot SEM for NB trials
plt.fill_between(
    meanfr_NB.index.values,
    meanfr_NB.values - error_NB,
    meanfr_NB.values + error_NB,
    color=[102 / 255, 204 / 255, 0 / 255],
    alpha=0.2,
)

plt.plot(
    meanfr_HB, color=[255 / 255, 99 / 255, 71 / 255], label="HB"
)  # Plot mean firing rate for HB trials

# Plot SEM for NB trials
plt.fill_between(
    meanfr_HB.index.values,
    meanfr_HB.values - error_HB,
    meanfr_HB.values + error_HB,
    color=[255 / 255, 99 / 255, 71 / 255],
    alpha=0.2,
)

plt.axvline(0, linewidth=2, color="k", linestyle="--")  # Plot a line at t = 0
plt.xlabel("Time from boundary (s)")  # Time from boundary in seconds, on X-axis
plt.ylabel("Firing rate (Hz)")  # Firing rate in Hz on Y-axis
plt.legend(loc="upper right")

# %%
# This plot verifies what we visualized in the PETH rasters above, that this cell responds to a hard boundary. Hence, it is a boundary cell. To learn more about these cells, please check out the original study [here](https://www.nature.com/articles/s41593-022-01020-w).
#
# I hope this tutorial was helpful. If you have any questions, comments or suggestions, please feel free to reach out to the Pynapple Team!
