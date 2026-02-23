from typer.testing import CliRunner

from ftm_assets import __version__, repository
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


def test_register(tmp_path):
    """Test the register CLI command."""
    # Create a temporary image file
    image_file = tmp_path / "test_image.jpg"
    image_file.write_bytes(b"fake image data")

    res = runner.invoke(
        cli, ["register", "--id", "CLI_TEST1", "--uri", str(image_file)]
    )
    assert res.exit_code == 0

    # Verify image was stored
    storage = repository.get_storage()
    key = repository.make_key("CLI_TEST1", "test_image.jpg")
    assert storage.exists(key)

    # Verify metadata was stored
    meta_key = repository.make_meta_key("CLI_TEST1")
    assert storage.exists(meta_key)

    # Verify we can look it up
    loaded = repository.get_image("CLI_TEST1")
    assert loaded is not None
    assert loaded.id == "CLI_TEST1"
    assert loaded.name == "test_image.jpg"


def test_register_with_meta(tmp_path):
    """Test the register CLI command with metadata JSON."""
    image_file = tmp_path / "test_image2.jpg"
    image_file.write_bytes(b"fake image data")

    meta_file = tmp_path / "meta.json"
    meta_file.write_text(
        '{"id": "CLI_TEST2", "name": "test_image2.jpg",'
        ' "url": "https://example.org/test_image2.jpg"}'
    )

    res = runner.invoke(
        cli,
        [
            "register",
            "--id",
            "CLI_TEST2",
            "--uri",
            str(image_file),
            "--meta",
            str(meta_file),
        ],
    )
    assert res.exit_code == 0

    loaded = repository.get_image("CLI_TEST2")
    assert loaded is not None
    assert str(loaded.url) == "https://example.org/test_image2.jpg"
