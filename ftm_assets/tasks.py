"""
Task queue adapter for OpenAleph

For deferring jobs:
    queue: ftm-assets
    task: ftm_assets.tasks.resolve_image
"""

from openaleph_procrastinate.app import make_app
from openaleph_procrastinate.model import DatasetJob, Defers
from openaleph_procrastinate.tasks import task

from ftm_assets.logic import lookup_proxy

app = make_app(__loader__.name)


@task(app=app)
def resolve_image(job: DatasetJob) -> Defers:
    for entity in job.get_entities():
        lookup_proxy(entity)
