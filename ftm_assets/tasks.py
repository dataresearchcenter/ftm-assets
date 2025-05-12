"""
Task queue adapter for OpenAleph

For deferring jobs:
    queue: ftm-assets
    task: ftm_assets.tasks.resolve_image
"""

from openaleph_procrastinate.app import make_app
from openaleph_procrastinate.model import DatasetJob
from openaleph_procrastinate.tasks import task

from ftm_assets.logic import lookup_proxy

app = make_app(__loader__.name)


@task(app=app)
def resolve_image(job: DatasetJob) -> DatasetJob:
    lookup_proxy(job.entity)
    return job
