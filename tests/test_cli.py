from typer.testing import CliRunner

from ftm_assets import __version__
from ftm_assets.cli import cli

runner = CliRunner()


def test_cli(fixtures_path, tmp_path):
    res = runner.invoke(cli, "--help")
    assert res.exit_code == 0

    res = runner.invoke(cli, "--version")
    assert res.exit_code == 0
    assert res.stdout.strip() == __version__

    res = runner.invoke(cli, ["load-ids", "-i", str(fixtures_path / "ids.txt")])
    assert res.exit_code == 0
    res = runner.invoke(
        cli, ["load-entities", "-i", str(fixtures_path / "entities.ftm.json")]
    )
    assert res.exit_code == 0

    results = str(tmp_path / "results.json")
    res = runner.invoke(
        cli, ["load-ids", "-i", str(fixtures_path / "ids.txt"), "-o", results]
    )
    assert res.exit_code == 0

    res = runner.invoke(cli, ["make-thumbnails", "-i", results])
    assert res.exit_code == 0

    res = runner.invoke(cli, ["mirror", "-i", results])
    assert res.exit_code == 0
