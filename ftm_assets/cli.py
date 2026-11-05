from io import BytesIO
from typing import Annotated, Optional

import orjson
import typer
from anystore.cli import ErrorHandler
from anystore.io import smart_open, smart_stream
from anystore.logging import configure_logging
from ftmq.io import smart_read_proxies
from rich import print

from ftm_assets import __version__, logic
from ftm_assets.model import Image
from ftm_assets.settings import Settings

settings = Settings()

cli = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=settings.debug)


def write_obj(obj: Image, out: BytesIO) -> None:
    line = orjson.dumps(obj.model_dump(mode="json"), option=orjson.OPT_APPEND_NEWLINE)
    out.write(line)


@cli.callback(invoke_without_command=True)
def cli_ftm_assets(
    version: Annotated[Optional[bool], typer.Option(..., help="Show version")] = False,
):
    if version:
        print(__version__)
        raise typer.Exit()
    configure_logging()


@cli.command()
def load_entities(
    input_uri: Annotated[
        str, typer.Option("-i", help="Input uri, default stdin")
    ] = "-",
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
):
    """
    Resolve and build images for FollowTheMoney entities with a Wikidata id
    """
    with ErrorHandler():
        with smart_open(output_uri, "wb") as out:
            for proxy in smart_read_proxies(input_uri):
                res = logic.lookup_proxy(proxy)
                if res is not None:
                    write_obj(res, out)


@cli.command()
def load_ids(
    input_uri: Annotated[
        str, typer.Option("-i", help="Input uri, default stdin")
    ] = "-",
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
):
    """
    Resolve and build images for Wikidata ids (one per line)
    """
    with ErrorHandler():
        with smart_open(output_uri, "wb") as out:
            for id in smart_stream(input_uri, mode="r"):
                res = logic.lookup(id.strip())
                if res is not None:
                    write_obj(res, out)
