# ----------------------------------------------------------------------------
# Copyright (c) 2013--, scikit-bio development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function
from future.builtins import range

import warnings
from functools import partial

import numpy as np

from ._base import (_preprocess_input, _run_stat_method, _build_results,
                    CategoricalStats)


def permanova(distance_matrix, grouping, column=None, permutations=999):
    """Test for significant differences between groups using PERMANOVA.

    Permutational Multivariate Analysis of Variance (PERMANOVA) is a
    non-parametric method that tests whether two or more groups of objects are
    significantly different based on a categorical factor. It is conceptually
    similar to ANOVA except that it operates on a distance matrix, which allows
    for multivariate analysis. PERMANOVA computes a pseudo-F statistic.

    Statistical significance is assessed via a permutation test. The assignment
    of objects to groups (`grouping`) is randomly permuted a number of times
    (controlled via `permutations`). A pseudo-F statistic is computed for each
    permutation and the p-value is the proportion of permuted pseudo-F
    statisics that are equal to or greater than the original (unpermuted)
    pseudo-F statistic.

    Parameters
    ----------
    distance_matrix : DistanceMatrix
        Distance matrix containing distances between objects (e.g., distances
        between samples of microbial communities).
    grouping : 1-D array_like or pandas.DataFrame
        Vector indicating the assignment of objects to groups. For example,
        these could be strings or integers denoting which group an object
        belongs to. If `grouping` is 1-D ``array_like``, it must be the same
        length and in the same order as the objects in `distance_matrix`. If
        `grouping` is a ``DataFrame``, the column specified by `column` will be
        used as the grouping vector. The ``DataFrame`` must be indexed by the
        IDs in `distance_matrix` (i.e., the row labels must be distance matrix
        IDs), but the order of IDs between `distance_matrix` and the
        ``DataFrame`` need not be the same. All IDs in the distance matrix must
        be present in the ``DataFrame``. Extra IDs in the ``DataFrame`` are
        allowed (they are ignored in the calculations).
    column : str, optional
        Column name to use as the grouping vector if `grouping` is a
        ``DataFrame``. Must be provided if `grouping` is a ``DataFrame``.
        Cannot be provided if `grouping` is 1-D ``array_like``.
    permutations : int, optional
        Number of permutations to use when assessing statistical
        significance. Must be greater than or equal to zero. If zero,
        statistical significance calculations will be skipped and the p-value
        will be ``np.nan``.

    Returns
    -------
    pandas.Series
        Results of the statistical test, including ``test statistic`` and
        ``p-value``.

    See Also
    --------
    anosim

    Notes
    -----
    See [1]_ for the original method reference, as well as ``vegan::adonis``,
    available in R's vegan package [2]_.

    The p-value will be ``np.nan`` if `permutations` is zero.

    References
    ----------
    .. [1] Anderson, Marti J. "A new method for non-parametric multivariate
       analysis of variance." Austral Ecology 26.1 (2001): 32-46.

    .. [2] http://cran.r-project.org/web/packages/vegan/index.html

    Examples
    --------
    See :mod:`skbio.stats.distance.anosim` for usage examples (both functions
    provide similar interfaces).

    """
    sample_size, num_groups, grouping, tri_idxs, distances = _preprocess_input(
        distance_matrix, grouping, column)

    # Calculate number of objects in each group.
    group_sizes = np.bincount(grouping)
    s_T = (distances ** 2).sum() / sample_size

    test_stat_function = partial(_compute_f_stat, sample_size, num_groups,
                                 tri_idxs, distances, group_sizes, s_T)
    stat, p_value = _run_stat_method(test_stat_function, grouping,
                                     permutations)

    return _build_results('PERMANOVA', 'pseudo-F', sample_size, num_groups,
                          stat, p_value, permutations)


def _compute_f_stat(sample_size, num_groups, tri_idxs, distances, group_sizes,
                    s_T, grouping):
    """Compute PERMANOVA pseudo-F statistic."""
    # Create a matrix where objects in the same group are marked with the group
    # index (e.g. 0, 1, 2, etc.). objects that are not in the same group are
    # marked with -1.
    grouping_matrix = -1 * np.ones((sample_size, sample_size), dtype=int)
    for group_idx in range(num_groups):
        within_indices = _index_combinations(
            np.where(grouping == group_idx)[0])
        grouping_matrix[within_indices] = group_idx

    # Extract upper triangle (in same order as distances were extracted
    # from full distance matrix).
    grouping_tri = grouping_matrix[tri_idxs]

    # Calculate s_W for each group, accounting for different group sizes.
    s_W = 0
    for i in range(num_groups):
        s_W += (distances[grouping_tri == i] ** 2).sum() / group_sizes[i]

    s_A = s_T - s_W
    return (s_A / (num_groups - 1)) / (s_W / (sample_size - num_groups))


def _index_combinations(indices):
    # Modified from http://stackoverflow.com/a/11144716
    return np.tile(indices, len(indices)), np.repeat(indices, len(indices))


class PERMANOVA(CategoricalStats):
    """PERMANOVA statistical method executor.

    .. note:: Deprecated in scikit-bio 0.2.1-dev
       ``PERMANOVA`` will be removed in scikit-bio 0.3.0. It is replaced by
       ``permanova``, which provides a simpler procedural interface to running
       this statistical method.

    Permutational Multivariate Analysis of Variance (PERMANOVA) is a
    non-parametric method that tests whether two or more groups of objects are
    significantly different based on a categorical factor. It is conceptually
    similar to ANOVA except that it operates on a distance matrix, which allows
    for multivariate analysis. PERMANOVA computes a pseudo-F statistic and
    tests the significance through permutations.

    Notes
    -----
    See [1]_ for the original PERMANOVA reference, as well as
    ``vegan::adonis``, available in R's vegan package [2]_.

    References
    ----------
    .. [1] Anderson, Marti J. "A new method for non-parametric multivariate
       analysis of variance." Austral Ecology 26.1 (2001): 32-46.

    .. [2] http://cran.r-project.org/web/packages/vegan/index.html

    """

    short_method_name = 'PERMANOVA'
    long_method_name = 'Permutational Multivariate Analysis of Variance'
    test_statistic_name = 'pseudo-F statistic'

    def __init__(self, distance_matrix, grouping, column=None):
        warnings.warn(
            "skbio.stats.distance.PERMANOVA is deprecated and will be removed "
            "in scikit-bio 0.3.0. Please update your code to use "
            "skbio.stats.distance.permanova.", UserWarning)

        super(PERMANOVA, self).__init__(distance_matrix, grouping,
                                        column=column)

        # Calculate number of objects in each group.
        self._group_sizes = np.bincount(self._grouping)
        self._num_groups = len(self._groups)
        self._distances = self._dm.condensed_form()
        self._s_T = (self._distances ** 2).sum() / self._dm.shape[0]

    def _run(self, grouping):
        """Compute PERMANOVA pseudo-F statistic."""
        # Create a matrix where objects in the same group are marked with the
        # group index (e.g. 0, 1, 2, etc.). objects that are not in the same
        # group are marked with -1.
        grouping_matrix = -1 * np.ones(self._dm.shape, dtype=int)
        for group_idx in range(len(self._groups)):
            within_indices = self._index_combinations(
                np.where(grouping == group_idx)[0])
            grouping_matrix[within_indices] = group_idx

        # Extract upper triangle (in same order as distances were extracted
        # from full distance matrix).
        grouping_tri = grouping_matrix[self._tri_idxs]

        return self._compute_f_stat(grouping_tri)

    def _index_combinations(self, indices):
        # Modified from http://stackoverflow.com/a/11144716
        return np.tile(indices, len(indices)), np.repeat(indices, len(indices))

    def _compute_f_stat(self, grouping_tri):
        a = self._num_groups
        N = self._dm.shape[0]

        # Calculate s_W for each group, accounting for different group sizes.
        s_W = 0
        for i in range(a):
            s_W += ((self._distances[grouping_tri == i] ** 2).sum() /
                    self._group_sizes[i])

        s_A = self._s_T - s_W
        return (s_A / (a - 1)) / (s_W / (N - a))
