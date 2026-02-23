from io import BytesIO
from pathlib import Path
from typing import Annotated, Optional

import orjson
import typer
from anystore.cli import ErrorHandler
from anystore.io import smart_open, smart_read, smart_stream, smart_stream_json_models
from anystore.util import join_uri
from ftmq.io import smart_read_proxies
from pydantic import HttpUrl
from rich import print

from ftm_assets import __version__, logic, repository
from ftm_assets.logging import configure_logging
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
    with ErrorHandler():
        with smart_open(output_uri, "wb") as out:
            for id in smart_stream(input_uri, mode="r"):
                res = logic.lookup(id.strip())
                if res is not None:
                    write_obj(res, out)


@cli.command()
def mirror(
    input_uri: Annotated[
        str, typer.Option("-i", help="Input uri, default stdin")
    ] = "-",
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
):
    """
    Mirror images to configured storage
    """
    with ErrorHandler():
        with smart_open(output_uri, "wb") as out:
            for image in smart_stream_json_models(input_uri, Image):
                logic.mirror(image)
                write_obj(image, out)


@cli.command()
def make_thumbnails(
    input_uri: Annotated[
        str, typer.Option("-i", help="Input uri, default stdin")
    ] = "-",
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
    size: Annotated[int, typer.Option(help="Size in pixels")] = settings.thumbnail_size,
):
    """
    Generate thumbnails for given input results
    """
    with ErrorHandler():
        with smart_open(output_uri, "wb") as out:
            for image in smart_stream_json_models(input_uri, Image):
                logic.generate_thumbnail(image, size)
                write_obj(image, out)


@cli.command()
def register(
    id: Annotated[str, typer.Option(help="Entity ID")],
    uri: Annotated[str, typer.Option(help="URI to image file (local path or remote)")],
    name: Annotated[Optional[str], typer.Option(help="Image filename")] = None,
    meta: Annotated[Optional[str], typer.Option(help="URI to metadata JSON")] = None,
):
    """Register a manually placed image for an entity."""
    image_name = name or Path(uri).name
    data = smart_read(uri)
    repository.save_data(repository.make_key(id, image_name), data)
    if meta:
        meta_text = smart_read(meta, mode="r")
        image = Image.model_validate_json(meta_text)
        repository.save_metadata(image)
    else:
        key = repository.make_key(id, image_name)
        image = Image(
            id=id,
            name=image_name,
            url=HttpUrl(join_uri(settings.public_cdn_prefix, key)),
        )
        repository.save_metadata(image)
