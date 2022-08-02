#!/usr/bin/env python
"""Tests for `toshi_hazard_utils` package."""

# import pytest
import unittest
import random
import itertools
from moto import mock_dynamodb

from nzshm_common.grids.region_grid import load_grid
from nzshm_common.location.code_location import CodedLocation
from toshi_hazard_utils.hazard import hazard_report, ToshiHazardReport

from toshi_hazard_store import model

HAZARD_MODEL_ID = "MYHAZID"
GRID_02 = load_grid('NZ_0_2_NB_1_1')
VS30S = [250, 350, 450]
IMTS = ['PGA', 'SA(0.5)']
AGGS = ['mean', '0.10']
LOCS = [CodedLocation(*o, 0.001) for o in GRID_02[20:50]]
N_LVLS = 29


def build_hazard_aggregation_models():

    lvps = list(map(lambda x: model.LevelValuePairAttribute(lvl=x / 1e3, val=(x / 1e6)), range(1, N_LVLS)))
    for (loc, vs30, agg) in itertools.product(LOCS, VS30S, AGGS):
        for imt, val in enumerate(IMTS):
            yield model.HazardAggregation(
                values=lvps,
                vs30=vs30,
                agg=agg,
                imt=val,
                hazard_model_id=HAZARD_MODEL_ID,
            ).set_location(loc)


@mock_dynamodb
class HighLevelHazard(unittest.TestCase):
    def setUp(self):
        model.migrate()
        with model.HazardAggregation.batch_write() as batch:
            for item in build_hazard_aggregation_models():
                batch.save(item)

    def test_list_hazard_data_available_for_grid_location(self):
        loc = LOCS[0]
        myhazards = list(hazard_report([HAZARD_MODEL_ID], locations=[loc.code]))
        print(myhazards)

        result = myhazards[0]
        self.assertTrue(isinstance(result, ToshiHazardReport))
        self.assertEqual(len(myhazards), 1)
        self.assertEqual(result.loc, loc)
        self.assertEqual(set(IMTS), result.imts)
        self.assertEqual(set(AGGS), result.aggs)
        self.assertEqual(set(VS30S), result.vs30s)
        self.assertEqual(set(lvl / 1e3 for lvl in range(1, N_LVLS)), result.levels)

    def test_get_nearest_hazard_for_an_arbitrary_location(self):
        gridloc = random.choice(LOCS)
        print(f'gridloc {gridloc}')

        off_lat = round(gridloc.lat + random.randint(0, 9) * 0.01, 3)
        off_lon = round(gridloc.lon + random.randint(0, 9) * 0.01, 3)
        somewhere_off_grid = CodedLocation(off_lat, off_lon, 0.001)
        nearest_grid = somewhere_off_grid.downsample(0.2)

        print(f'somewhere_off_grid {somewhere_off_grid}')
        print(f'nearest_grid {nearest_grid}')

        self.assertEqual(gridloc, CodedLocation(nearest_grid.lat, nearest_grid.lon, 0.001))
        self.assertTrue(CodedLocation(nearest_grid.lat, nearest_grid.lon, 0.001) in LOCS)


@unittest.skip("not implemented")
class HighLevelRealizations(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_the_realisations_for_hazard_location_from_hazard_set(self):
        assert 0


@unittest.skip("not implemented")
class HighLevelDeAggregations(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_the_realisations_for_hazard_location_from_hazard_set(self):
        assert 0
