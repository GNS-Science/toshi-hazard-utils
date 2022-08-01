"""Helpers for obtaining hazard data from Toshi Hazard Store."""
import dataclasses
from typing import Dict, Iterable, Set  # List, Set, Tuple

from nzshm_common.location.code_location import CodedLocation
from toshi_hazard_store import query_v3


@dataclasses.dataclass
class ToshiHazardReport:
    loc: CodedLocation
    vs30s: Set[float] = set()
    imts: Set[str] = set()
    aggs: Set[str] = set()
    levels: Set[Iterable[float]] = set()


def hazard_report(hazard_model_ids: Iterable[str], locations: Iterable[CodedLocation]) -> Iterable[ToshiHazardReport]:
    """Get the availabe hazard attributes as ToshiHazardReport objects generator."""

    loc_reports: Dict[CodedLocation, ToshiHazardReport] = {}
    for res in query_v3.get_hazard_curves(locations, vs30s=[], hazard_model_ids=hazard_model_ids, imts=[]):
        loc = CodedLocation(res.lat, res.lon)

        if loc not in loc_reports.keys():
            loc_reports[loc] = ToshiHazardReport(loc)  # , {[0]}, {[]}, {[]}, {[]})  # noqa

        report = loc_reports[loc]
        report.imts.add(res.imt)
        report.vs30s.add(res.vs30)
        report.aggs.add(res.agg)
        report.levels.add([v.lvl for v in res.values])

    for report in loc_reports:
        yield report
