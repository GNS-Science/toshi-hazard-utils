"""Console script for toshi_hazard_utils."""

import logging
import sys

import click
import toml
from nzshm_common.location import CodedLocation

from toshi_hazard_utils.hazard import hazard_report

# from toshi_hazard_store import model


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
@click.option('-h', '--hazard_model_ids', help='comma-delimted list of hazard model ids.')
@click.option('-s', '--sites', help='comma-delimited list of location codes.')
@click.option('-c', '--config', type=click.Path(exists=True))  # help="path to a valid THU configuration file."
@click.option('-rs', '--resample', type=click.Choice(choices=['0.1', '0.2']), default=None)
@click.option('-v', '--verbose', is_flag=True)
def cli_hazard_report(hazard_model_ids, sites, config, resample, verbose):
    """Gather information on available hazard curves for a given site or sites."""

    if config:
        conf = toml.load(config)
        if conf.get("report"):
            if verbose:
                click.echo(f"using settings in {config} for report")
            sites = sites or conf['report'].get('sites')
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

    #Crazy - need to wrap generator in list() until we've squashed all the stray 'print' statements
    myhazards = list(hazard_report(hazard_model_ids=hmids, locations=locations))

    DESC = "Hazard Aggregation report"
    # INFO = "Gather information on available hazard cruves for a given site or sites."
    click.echo("")
    click.echo(DESC)
    click.echo("=" * len(DESC))
    for haz in myhazards:
        click.echo(haz)


if __name__ == "__main__":
    thu()  # pragma: no cover
