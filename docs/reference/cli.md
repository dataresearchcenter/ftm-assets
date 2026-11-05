# ftm-assets

Resolve and build images for FollowTheMoney entities.

**Usage**:

```console
$ ftm-assets [OPTIONS] COMMAND [ARGS]...
```

**Options**:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `--version` / `--no-version` | bool | Show version | `no-version` |
| `--install-completion` |  | Install completion for the current shell. |  |
| `--show-completion` |  | Show completion for the current shell, to copy it or customize the installation. |  |
| `--help` |  | Show this message and exit. |  |

**Commands**:

| Name | Description |
| --- | --- |
| `load-entities` | Resolve and build images for FollowTheMoney entities with a Wikidata id |
| `load-ids` | Resolve and build images for Wikidata ids (one per line) |

## `ftm-assets load-entities`

Resolve and build images for FollowTheMoney entities with a Wikidata id.

**Example**:

```bash
cat entities.ftm.json | ftm-assets load-entities > images.json
```

**Usage**:

```console
$ ftm-assets load-entities [OPTIONS]
```

**Options**:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `-i` | TEXT | Input uri, default stdin | `-` |
| `-o` | TEXT | Output uri, default stdout | `-` |
| `--help` |  | Show this message and exit. |  |

## `ftm-assets load-ids`

Resolve and build images for Wikidata ids (one per line).

**Example**:

```bash
echo "Q567" | ftm-assets load-ids
```

**Usage**:

```console
$ ftm-assets load-ids [OPTIONS]
```

**Options**:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `-i` | TEXT | Input uri, default stdin | `-` |
| `-o` | TEXT | Output uri, default stdout | `-` |
| `--help` |  | Show this message and exit. |  |
