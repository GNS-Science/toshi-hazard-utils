"""Helpers for obtaining hazard data from Toshi Hazard Store."""
from dataclasses import dataclass, field
from typing import Dict, Iterable, Set  # List, Set, Tuple

from nzshm_common.location.code_location import CodedLocation
from toshi_hazard_store import query_v3


@dataclass
class ToshiHazardReport:
    loc: CodedLocation
    model_id: str = field(default_factory=str)
    vs30s: Set[float] = field(default_factory=set)
    imts: Set[str] = field(default_factory=set)
    aggs: Set[str] = field(default_factory=set)
    levels: Set[Iterable[float]] = field(default_factory=set)


def hazard_report(hazard_model_ids: Iterable[str], locations: Iterable[CodedLocation]) -> Iterable[ToshiHazardReport]:
    """Get the availabe hazard attributes as ToshiHazardReport objects generator."""

    loc_reports: Dict[CodedLocation, ToshiHazardReport] = {}
    for res in query_v3.get_hazard_curves(locations, vs30s=[], hazard_model_ids=hazard_model_ids, imts=[]):
        loc_hmi = f'{CodedLocation(res.lat, res.lon, 0.001).code}:{res.hazard_model_id}'

        if loc_hmi not in loc_reports.keys():
            loc_reports[loc_hmi] = ToshiHazardReport(
                CodedLocation(res.lat, res.lon, 0.001)
            )  # , {[0]}, {[]}, {[]}, {[]})  # noqa

        report = loc_reports[loc_hmi]
        report.model_id = res.hazard_model_id
        report.imts.add(res.imt)
        report.vs30s.add(res.vs30)
        report.aggs.add(res.agg)
        for v in res.values:
            report.levels.add(v.lvl)

    for loc, report in loc_reports.items():
        yield report
