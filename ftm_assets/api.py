from anystore.io import smart_read
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from ftm_assets import __version__
from ftm_assets.logic import lookup
from ftm_assets.model import Image
from ftm_assets.settings import Settings

settings = Settings()


def get_description() -> str:
    return smart_read(settings.api.description_uri)


app = FastAPI(
    debug=settings.debug,
    title=settings.api.title,
    contact=settings.api.contact.model_dump(),
    description=get_description(),
    version=__version__,
    root_path=settings.api.path_prefix,
    redoc_url="/",
)
app.add_middleware(
    CORSMiddleware,
    allow_methods=["OPTIONS", "GET"],
)

if settings.debug:
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/img/{id}")
async def api_img_lookup(id: str) -> Image:
    """Get image metadata"""
    res = lookup(id)
    if res is None:
        raise HTTPException(status_code=404)
    return res


@app.get("/r/img/{id}")
async def api_img_redirect(id: str) -> RedirectResponse:
    """Get image redirect to public url"""
    res = lookup(id)
    if res is None:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=res.public_url)


@app.get("/r/img/{id}/thumb")
async def api_img_thumbnail_redirect(id: str) -> RedirectResponse:
    """Get image redirect to public url"""
    res = lookup(id)
    if res is None:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=res.thumbnail_url)
