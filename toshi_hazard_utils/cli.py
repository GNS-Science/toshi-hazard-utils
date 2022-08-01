"""Console script for toshi_hazard_utils."""

import click


@click.command()
def main():
    """Main entrypoint."""
    click.echo("toshi-hazard-utils")
    click.echo("=" * len("toshi-hazard-utils"))
    click.echo("Helpers for the toshi-hazard-store")


if __name__ == "__main__":
    main()  # pragma: no cover
