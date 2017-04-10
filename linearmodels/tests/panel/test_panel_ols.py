from itertools import product

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from linearmodels.iv.model import IV2SLS
from linearmodels.panel.data import PanelData
from linearmodels.panel.model import PanelOLS, PooledOLS
from linearmodels.tests.panel._utility import assert_results_equal, generate_data
from linearmodels.utility import AttrDict

missing = [0.0, 0.02, 0.20]
datatypes = ['numpy', 'pandas', 'xarray']
has_const = [True, False]
perms = list(product(missing, datatypes, has_const))
ids = list(map(lambda s: '-'.join(map(str, s)), perms))


@pytest.fixture(params=perms, ids=ids)
def data(request):
    missing, datatype, const = request.param
    return generate_data(missing, datatype, const=const, ntk=(91, 7, 5), other_effects=2)


perms = list(product(missing, datatypes))
ids = list(map(lambda s: '-'.join(map(str, s)), perms))


@pytest.fixture(params=perms, ids=ids)
def const_data(request):
    missing, datatype = request.param
    data = generate_data(missing, datatype, ntk=(91, 7, 1))
    y = PanelData(data.y).dataframe
    x = y.copy()
    x.iloc[:, :] = 1
    x.columns = ['Const']
    return AttrDict(y=y, x=x, w=PanelData(data.w).dataframe)


def test_const_data_only(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x)
    res = mod.fit()
    res2 = IV2SLS(y, x, None, None).fit()
    assert_allclose(res.params, res2.params)


def test_const_data_only_weights(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, weights=const_data.w)
    res = mod.fit()
    res2 = IV2SLS(y, x, None, None, weights=const_data.w).fit()
    assert_allclose(res.params, res2.params)


def test_const_data_entity(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, entity_effect=True)
    res = mod.fit()

    x = mod.exog.dataframe
    d = mod.dependent.dummies('entity', drop_first=True)
    d.iloc[:, :] = d.values - x.values @ np.linalg.lstsq(x.values, d.values)[0]

    xd = np.c_[x.values, d.values]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d.columns))

    res2 = IV2SLS(mod.dependent.dataframe, xd, None, None).fit()
    assert_allclose(res.params, res2.params.iloc[:1])


def test_const_data_entity_weights(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, entity_effect=True, weights=const_data.w)
    res = mod.fit()

    y = mod.dependent.dataframe
    w = mod.weights.dataframe
    x = mod.exog.dataframe
    d = mod.dependent.dummies('entity', drop_first=True)
    d_columns = list(d.columns)

    root_w = np.sqrt(w.values)
    z = np.ones_like(x)
    wd = root_w * d.values
    wz = root_w
    d = d - z @ np.linalg.lstsq(wz, wd)[0]

    xd = np.c_[x.values, d.values]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + d_columns)

    res2 = IV2SLS(y, xd, None, None, weights=w).fit()
    assert_allclose(res.params, res2.params.iloc[:1])


def test_const_data_time(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, time_effect=True)
    res = mod.fit()

    x = mod.exog.dataframe
    d = mod.dependent.dummies('time', drop_first=True)
    d.iloc[:, :] = d.values - x.values @ np.linalg.lstsq(x.values, d.values)[0]

    xd = np.c_[x.values, d.values]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d.columns))

    res2 = IV2SLS(mod.dependent.dataframe, xd, None, None).fit()
    assert_allclose(res.params, res2.params.iloc[:1])


def test_const_data_time_weights(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, time_effect=True, weights=const_data.w)
    res = mod.fit()

    y = mod.dependent.dataframe
    w = mod.weights.dataframe
    x = mod.exog.dataframe
    d = mod.dependent.dummies('time', drop_first=True)
    d_columns = list(d.columns)

    root_w = np.sqrt(w.values)
    z = np.ones_like(x)
    wd = root_w * d.values
    wz = root_w
    d = d - z @ np.linalg.lstsq(wz, wd)[0]

    xd = np.c_[x.values, d.values]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + d_columns)

    res2 = IV2SLS(y, xd, None, None, weights=w).fit()
    assert_allclose(res.params, res2.params.iloc[:1])


def test_const_data_both(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, entity_effect=True, time_effect=True)
    res = mod.fit()

    x = mod.exog.dataframe
    d1 = mod.dependent.dummies('entity', drop_first=True)
    d2 = mod.dependent.dummies('time', drop_first=True)
    d = np.c_[d1.values, d2.values]
    d = pd.DataFrame(d, index=x.index, columns=list(d1.columns) + list(d2.columns))
    d.iloc[:, :] = d.values - x.values @ np.linalg.lstsq(x.values, d.values)[0]

    xd = np.c_[x.values, d.values]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d.columns))

    res2 = IV2SLS(mod.dependent.dataframe, xd, None, None).fit()
    assert_allclose(res.params, res2.params.iloc[:1])


def test_const_data_both_weights(const_data):
    y, x = const_data.y, const_data.x
    mod = PanelOLS(y, x, entity_effect=True, time_effect=True, weights=const_data.w)
    res = mod.fit()

    w = mod.weights.dataframe
    x = mod.exog.dataframe

    d1 = mod.dependent.dummies('entity', drop_first=True)
    d2 = mod.dependent.dummies('time', drop_first=True)
    d = np.c_[d1.values, d2.values]
    root_w = np.sqrt(w.values)
    z = np.ones_like(x)
    wd = root_w * d
    wz = root_w
    d = d - z @ np.linalg.lstsq(wz, wd)[0]
    d = pd.DataFrame(d, index=x.index, columns=list(d1.columns) + list(d2.columns))

    xd = np.c_[x.values, d.values]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d.columns))

    res2 = IV2SLS(mod.dependent.dataframe, xd, None, None, weights=w).fit()
    assert_allclose(res.params, res2.params.iloc[:1])


def test_panel_no_effects(data):
    res = PanelOLS(data.y, data.x).fit()
    res2 = PooledOLS(data.y, data.x).fit()
    assert_results_equal(res, res2)


def test_panel_no_effects_weighted(data):
    res = PanelOLS(data.y, data.x, weights=data.w).fit()
    res2 = PooledOLS(data.y, data.x, weights=data.w).fit()
    assert_results_equal(res, res2)


def test_panel_entity_lvsd(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    if mod.has_constant:
        d = mod.dependent.dummies('entity', drop_first=True)
        z = np.ones_like(y)
        d_demean = d.values - z @ np.linalg.lstsq(z, d.values)[0]
    else:
        d = mod.dependent.dummies('entity', drop_first=False)
        d_demean = d.values

    xd = np.c_[x.values, d_demean]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d.columns))

    ols_mod = IV2SLS(y, xd, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(data.vc1)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(data.vc2)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_entity_fwl(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    if mod.has_constant:
        d = mod.dependent.dummies('entity', drop_first=True)
        z = np.ones_like(y)
        d_demean = d.values - z @ np.linalg.lstsq(z, d.values)[0]
    else:
        d = mod.dependent.dummies('entity', drop_first=False)
        d_demean = d.values

    x = x - d_demean @ np.linalg.lstsq(d_demean, x)[0]
    y = y - d_demean @ np.linalg.lstsq(d_demean, y)[0]

    ols_mod = IV2SLS(y, x, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_df=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_df=False)


def test_panel_time_lvsd(data):
    mod = PanelOLS(data.y, data.x, time_effect=True)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    d = mod.dependent.dummies('time', drop_first=mod.has_constant)
    d_cols = list(d.columns)
    d = d.values
    if mod.has_constant:
        z = np.ones_like(y)
        d = d - z @ np.linalg.lstsq(z, d)[0]

    xd = np.c_[x.values, d]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + d_cols)

    ols_mod = IV2SLS(y, xd, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_time_fwl(data):
    mod = PanelOLS(data.y, data.x, time_effect=True)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    d = mod.dependent.dummies('time', drop_first=mod.has_constant)
    d = d.values
    if mod.has_constant:
        z = np.ones_like(y)
        d = d - z @ np.linalg.lstsq(z, d)[0]

    x = x - d @ np.linalg.lstsq(d, x)[0]
    y = y - d @ np.linalg.lstsq(d, y)[0]

    ols_mod = IV2SLS(y, x, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_df=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_df=False)


def test_panel_both_lvsd(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True, time_effect=True)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    d1 = mod.dependent.dummies('entity', drop_first=mod.has_constant)
    d2 = mod.dependent.dummies('time', drop_first=True)
    d = np.c_[d1.values, d2.values]

    if mod.has_constant:
        z = np.ones_like(y)
        d = d - z @ np.linalg.lstsq(z, d)[0]

    xd = np.c_[x.values, d]
    xd = pd.DataFrame(xd,
                      index=x.index,
                      columns=list(x.columns) + list(d1.columns) + list(d2.columns))

    ols_mod = IV2SLS(y, xd, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_both_fwl(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True, time_effect=True)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    d1 = mod.dependent.dummies('entity', drop_first=mod.has_constant)
    d2 = mod.dependent.dummies('time', drop_first=True)
    d = np.c_[d1.values, d2.values]

    if mod.has_constant:
        z = np.ones_like(y)
        d = d - z @ np.linalg.lstsq(z, d)[0]

    x = x - d @ np.linalg.lstsq(d, x)[0]
    y = y - d @ np.linalg.lstsq(d, y)[0]

    ols_mod = IV2SLS(y, x, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_df=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_df=False)


def test_panel_entity_lvsd_weighted(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True, weights=data.w)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    w = mod.weights.dataframe
    d = mod.dependent.dummies('entity', drop_first=mod.has_constant)
    d_cols = d.columns
    d = d.values
    if mod.has_constant:
        z = np.ones_like(y)
        root_w = np.sqrt(w.values)
        wd = root_w * d
        wz = root_w * z
        d = d - z @ np.linalg.lstsq(wz, wd)[0]

    xd = np.c_[x.values, d]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d_cols))

    ols_mod = IV2SLS(y, xd, None, None, weights=w)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_time_lvsd_weighted(data):
    mod = PanelOLS(data.y, data.x, time_effect=True, weights=data.w)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    w = mod.weights.dataframe
    d = mod.dependent.dummies('time', drop_first=mod.has_constant)
    d_cols = d.columns
    d = d.values
    if mod.has_constant:
        z = np.ones_like(y)
        root_w = np.sqrt(w.values)
        wd = root_w * d
        wz = root_w * z
        d = d - z @ np.linalg.lstsq(wz, wd)[0]

    xd = np.c_[x.values, d]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d_cols))

    ols_mod = IV2SLS(y, xd, None, None, weights=w)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_both_lvsd_weighted(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True, time_effect=True, weights=data.w)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    w = mod.weights.dataframe
    d1 = mod.dependent.dummies('entity', drop_first=mod.has_constant)
    d2 = mod.dependent.dummies('time', drop_first=True)
    d = np.c_[d1.values, d2.values]

    if mod.has_constant:
        z = np.ones_like(y)
        root_w = np.sqrt(w.values)
        wd = root_w * d
        wz = root_w * z
        d = d - z @ np.linalg.lstsq(wz, wd)[0]

    xd = np.c_[x.values, d]
    xd = pd.DataFrame(xd,
                      index=x.index,
                      columns=list(x.columns) + list(d1.columns) + list(d2.columns))

    ols_mod = IV2SLS(y, xd, None, None, weights=w)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_entity_other_equivalence(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit()
    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    cats = pd.DataFrame(mod.dependent.entity_ids, index=mod.dependent.index)

    mod2 = PanelOLS(y, x, other_effects=cats)
    res2 = mod2.fit()
    assert_results_equal(res, res2)


def test_panel_time_other_equivalence(data):
    mod = PanelOLS(data.y, data.x, time_effect=True)
    res = mod.fit()
    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    cats = pd.DataFrame(mod.dependent.time_ids, index=mod.dependent.index)

    mod2 = PanelOLS(y, x, other_effects=cats)
    res2 = mod2.fit()
    assert_results_equal(res, res2)


def test_panel_entity_time_other_equivalence(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True, time_effect=True)
    res = mod.fit()
    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    c1 = mod.dependent.entity_ids
    c2 = mod.dependent.time_ids
    cats = np.c_[c1, c2]
    cats = pd.DataFrame(cats, index=mod.dependent.index)

    mod2 = PanelOLS(y, x, other_effects=cats)
    res2 = mod2.fit()
    assert_results_equal(res, res2)


def test_panel_other_lvsd(data):
    mod = PanelOLS(data.y, data.x, other_effects=data.c)
    res = mod.fit()

    y = mod.dependent.dataframe.copy()
    x = mod.exog.dataframe.copy()
    c = mod._other_effect_cats.dataframe.copy()
    d = []
    d_columns = []
    for i, col in enumerate(c):
        s = c[col].copy()
        dummies = pd.get_dummies(s.astype(np.int64), drop_first=(mod.has_constant or i > 0))
        dummies.columns = [s.name + '_val_' + str(c) for c in dummies.columns]
        d_columns.extend(list(dummies.columns))
        d.append(dummies.values)
    d = np.column_stack(d)

    if mod.has_constant:
        z = np.ones_like(y)
        d = d - z @ np.linalg.lstsq(z, d)[0]

    xd = np.c_[x.values, d]
    xd = pd.DataFrame(xd, index=x.index, columns=list(x.columns) + list(d_columns))

    ols_mod = IV2SLS(y, xd, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_fit=False)

    res3 = mod.fit(cov_type='unadjusted')
    assert_results_equal(res, res3)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc1
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    clusters = data.vc2
    ols_clusters = mod.reformat_clusters(clusters)
    res = mod.fit(cov_type='clustered', clusters=clusters)
    res2 = ols_mod.fit('clustered', clusters=ols_clusters.dataframe)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_time=True)
    clusters = pd.DataFrame(mod.dependent.time_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)

    res = mod.fit(cov_type='clustered', cluster_entity=True)
    clusters = pd.DataFrame(mod.dependent.entity_ids,
                            index=mod.dependent.index,
                            columns=['var.clust'])
    res2 = ols_mod.fit('clustered', clusters=clusters)
    assert_results_equal(res, res2, test_fit=False)


def test_panel_other_fwl(data):
    mod = PanelOLS(data.y, data.x, other_effects=data.c)
    res = mod.fit()

    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    c = mod._other_effect_cats.dataframe
    d = []
    d_columns = []
    for i, col in enumerate(c):
        s = c[col].copy()
        dummies = pd.get_dummies(s.astype(np.int64), drop_first=(mod.has_constant or i > 0))
        dummies.columns = [s.name + '_val_' + str(c) for c in dummies.columns]
        d_columns.extend(list(dummies.columns))
        d.append(dummies.values)
    d = np.column_stack(d)

    if mod.has_constant:
        z = np.ones_like(y)
        d = d - z @ np.linalg.lstsq(z, d)[0]

    x = x - d @ np.linalg.lstsq(d, x)[0]
    y = y - d @ np.linalg.lstsq(d, y)[0]

    ols_mod = IV2SLS(y, x, None, None)
    res2 = ols_mod.fit('unadjusted')
    assert_results_equal(res, res2, test_df=False)

    res = mod.fit(cov_type='robust')
    res2 = ols_mod.fit('robust')
    assert_results_equal(res, res2, test_df=False)


def test_panel_other_incorrect_size(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    y = mod.dependent.dataframe
    x = mod.exog.dataframe
    cats = pd.DataFrame(mod.dependent.entity_ids, index=mod.dependent.index)
    cats = PanelData(cats)
    cats = cats.panel.iloc[:, :, :cats.panel.shape[2] // 2]

    with pytest.raises(ValueError):
        PanelOLS(y, x, other_effects=cats)


def test_results_access(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit()
    d = dir(res)
    for key in d:
        if not key.startswith('_'):
            val = getattr(res, key)
            if callable(val):
                val()

    mod = PanelOLS(data.y, data.x, other_effects=data.c)
    res = mod.fit()
    d = dir(res)
    for key in d:
        if not key.startswith('_'):
            val = getattr(res, key)
            if callable(val):
                val()


def test_alt_rsquared(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit()
    assert_allclose(res.rsquared, res.rsquared_within)


def test_alt_rsquared_weighted(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True, weights=data.w)
    res = mod.fit()
    assert_allclose(res.rsquared, res.rsquared_within)


def test_too_many_effects(data):
    with pytest.raises(ValueError):
        PanelOLS(data.y, data.x, entity_effect=True, time_effect=True, other_effects=data.c)


def test_cov_equiv_cluster(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit(cov_type='clustered', cluster_entity=True)

    y = PanelData(data.y)
    clusters = pd.DataFrame(y.entity_ids, index=y.index)
    res2 = mod.fit(cov_type='clustered', clusters=clusters)
    assert_results_equal(res, res2)

    mod = PanelOLS(data.y, data.x, time_effect=True)
    res = mod.fit(cov_type='clustered', cluster_time=True)
    y = PanelData(data.y)
    clusters = pd.DataFrame(y.time_ids, index=y.index)
    res2 = mod.fit(cov_type='clustered', clusters=clusters)
    assert_results_equal(res, res2)


def test_cluster_smoke(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    mod.fit(cov_type='clustered', cluster_time=True)
    mod.fit(cov_type='clustered', cluster_entity=True)
    c2 = PanelData(data.vc2)
    c1 = PanelData(data.vc1)

    mod.fit(cov_type='clustered', clusters=c2)
    mod.fit(cov_type='clustered', cluster_entity=True, clusters=c1)
    mod.fit(cov_type='clustered', cluster_time=True, clusters=c1)
    with pytest.raises(ValueError):
        mod.fit(cov_type='clustered', cluster_time=True, clusters=c2)
    with pytest.raises(ValueError):
        mod.fit(cov_type='clustered', cluster_entity=True, clusters=c2)
    with pytest.raises(ValueError):
        mod.fit(cov_type='clustered', cluster_entity=True, cluster_time=True, clusters=c1)
    with pytest.raises(ValueError):
        clusters = c1.panel.iloc[:, :, :c1.panel.shape[2] // 2]
        mod.fit(cov_type='clustered', clusters=clusters)


def test_f_pooled(data):
    mod = PanelOLS(data.y, data.x, entity_effect=True)
    res = mod.fit()

    mod2 = PooledOLS(data.y, data.x)
    res2 = mod2.fit()

    eps = res.resids.values
    eps2 = res2.resids.values
    v1 = res.df_model - res2.df_model
    v2 = res.df_resid
    f_pool = (eps2.T @ eps2 - eps.T @ eps) / v1
    f_pool /= ((eps.T @ eps) / v2)
    f_pool = float(f_pool)
    assert_allclose(res.f_pooled.stat, f_pool)
    assert res.f_pooled.df == v1
    assert res.f_pooled.df_denom == v2

    mod = PanelOLS(data.y, data.x, time_effect=True)
    res = mod.fit()
    eps = res.resids.values
    eps2 = res2.resids.values
    v1 = res.df_model - res2.df_model
    v2 = res.df_resid
    f_pool = (eps2.T @ eps2 - eps.T @ eps) / v1
    f_pool /= ((eps.T @ eps) / v2)
    f_pool = float(f_pool)
    assert_allclose(res.f_pooled.stat, f_pool)
    assert res.f_pooled.df == v1
    assert res.f_pooled.df_denom == v2


    mod = PanelOLS(data.y, data.x, entity_effect=True, time_effect=True)
    res = mod.fit()
    eps = res.resids.values
    eps2 = res2.resids.values
    v1 = res.df_model - res2.df_model
    v2 = res.df_resid
    f_pool = (eps2.T @ eps2 - eps.T @ eps) / v1
    f_pool /= ((eps.T @ eps) / v2)
    f_pool = float(f_pool)
    assert_allclose(res.f_pooled.stat, f_pool)
    assert res.f_pooled.df == v1
    assert res.f_pooled.df_denom == v2