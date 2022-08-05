"""Console script for toshi_hazard_utils."""

import csv
import io
import logging
import sys

import click
import toml

try:
    import pandas as pd
except ImportError:
    print("WARNING: export to json (pandas dataframe) required uses the optional dependency - pandas.")

from nzshm_common.location import CodedLocation
from toshi_hazard_store import model, query_v3

from toshi_hazard_utils.hazard import hazard_report

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logging.getLogger('nshm_toshi_client.toshi_client_base').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('pynamodb').setLevel(logging.INFO)
logging.getLogger('toshi_hazard_post').setLevel(logging.DEBUG)
logging.getLogger('toshi_hazard_store').setLevel(logging.INFO)
logging.getLogger('gql.transport.requests').setLevel(logging.WARN)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)


@click.group()
def thu():
    pass


@thu.command(name='report')
@click.option('-H', '--hazard_model_ids', help='comma-delimted list of hazard model ids.')
@click.option('-S', '--sites', help='comma-delimited list of location codes.')
@click.option('-c', '--config', type=click.Path(exists=True))  # help="path to a valid THU configuration file."
@click.option('-rs', '--resample', type=click.Choice(choices=['0.1', '0.2']), default=None)
@click.option('-v', '--verbose', is_flag=True)
def cli_hazard_report(hazard_model_ids, sites, config, resample, verbose):
    """Gather information on available hazard curves for a given site or sites."""

    if config:
        conf = toml.load(config)
        if verbose:
            click.echo(f"using settings in {config} for report")
        sites = sites or conf.get('sites')
        hazard_model_ids = hazard_model_ids or conf['report'].get('hazard_model_ids')

    # parse sites into locations
    locations = []
    for site in sites.split(','):
        loc = CodedLocation(*[float(s) for s in site.split('~')], resolution=0.001)
        loc = loc.resample(float(resample)) if resample else loc
        locations.append(loc.resample(0.001).code)

    # parse hazard_model_ids from option
    hmids = []
    for hmid in hazard_model_ids.split(','):
        hmids.append(hmid.strip())

    if verbose:
        click.echo(f"locations {locations}")

    # Crazy - need to wrap generator in list() until we've squashed all the stray 'print' statements
    myhazards = list(hazard_report(hazard_model_ids=hmids, locations=locations))

    DESC = "Hazard Aggregation report"
    # INFO = "Gather information on available hazard curves for a given site or sites."
    click.echo("")
    click.echo(DESC)
    click.echo("=" * len(DESC))
    for haz in myhazards:
        click.echo(haz)


@thu.command(name='export')
@click.option('-H', '--hazard_model_ids', help='comma-delimted list of hazard model ids.')
@click.option('-S', '--sites', help='comma-delimited list of location codes.')
@click.option('-I', '--imts', help='comma-delimited list of imts.')
@click.option('-A', '--aggs', help='comma-delimited list of aggs.')
@click.option('-V', '--vs30s', help='comma-delimited list of vs30s.')
@click.option('-c', '--config', type=click.Path(exists=True))  # help="path to a valid THU configuration file."
@click.option('-rs', '--resample', type=click.Choice(choices=['0.1', '0.2']), default=None)
@click.option('-v', '--verbose', is_flag=True)
@click.option('-o', '--output', type=click.File('w'), default='-')
@click.option('-f', '--format', type=click.Choice(choices=['csv', 'json']), default='csv')
def cli_hazard_export(hazard_model_ids, sites, imts, aggs, vs30s, config, resample, verbose, output, format):
    """Export hazard curves for a given set of arguments."""

    sites = sites.split(',') if sites else None
    hazard_model_ids = hazard_model_ids.split(',') if hazard_model_ids else None
    imts = imts.split(',') if imts else None
    vs30s = vs30s.split(',') if vs30s else None
    aggs = aggs.split(',') if aggs else None

    if config:
        conf = toml.load(config)
        if verbose:
            click.echo(f"using settings in {config} for export")
        sites = sites or conf.get('sites').split(',')
        hazard_model_ids = hazard_model_ids or conf.get('hazard_model_ids')
        imts = imts or conf.get('imts')
        vs30s = vs30s or conf.get('vs30s')
        aggs = aggs or conf.get('aggs')

    # parse sites into locations
    locations = []
    for site in sites:
        loc = CodedLocation(*[float(s) for s in site.split('~')], resolution=0.001)
        loc = loc.resample(float(resample)) if resample else loc
        locations.append(loc.resample(0.001).code)

    if verbose:
        click.echo(f"{sites} {hazard_model_ids} {imts} {vs30s} {format}")
    if verbose:
        click.echo(output)

    haggs = query_v3.get_hazard_curves(locations, vs30s, hazard_model_ids, imts=imts, aggs=aggs)

    if format == 'csv':
        model_writer = csv.writer(output)
        model_writer.writerows(list(model.HazardAggregation.to_csv(haggs)))
        return

    if format == 'json':
        # first write to an in memory csv
        tmpcsv = io.StringIO()
        model_writer = csv.writer(tmpcsv)
        model_writer.writerows(list(model.HazardAggregation.to_csv(haggs)))
        tmpcsv.seek(0)
        # now build a dataframe
        df = pd.read_csv(tmpcsv)
        if verbose:
            click.echo(df)
        df.to_json(output)
        return


if __name__ == "__main__":
    thu()  # pragma: no cover
