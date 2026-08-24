"""Integration tests for the Typer CLI `scan` command."""

import json
from pathlib import Path

import respx
from typer.testing import CliRunner

from arr_oldies.cli import app

runner = CliRunner(env={"COLUMNS": "160"})


@respx.mock
def test_cli_scan_default_table_output(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify scan command with default options fetches instances, displays table and summary, and exits 0."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    # Mock radarr-main
    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "The Matrix",
                "year": 1999,
                "path": "/movies/The Matrix (1999)",
                "monitored": True,
                "hasFile": True,
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 101,
                "movieId": 1,
                "relativePath": "The Matrix (1999).mkv",
                "path": "/movies/The Matrix (1999)/The Matrix (1999).mkv",
                "size": 15_000_000_000,
                "dateAdded": "2023-01-01T00:00:00Z",
                "mediaInfo": {
                    "audioLanguages": "English/Japanese",
                    "videoCodec": "x264",
                    "resolution": "1080p",
                },
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 1001,
                    "movieId": 1,
                    "sourceTitle": "The.Matrix.1999.1080p",
                    "eventType": "downloadFolderImported",
                    "date": "2023-01-01T12:00:00Z",
                    "data": {"fileId": "101"},
                }
            ],
        }
    )

    # Mock sonarr-tv
    respx.get("https://sonarr.local:8989/api/v3/series").respond(
        json=[
            {
                "id": 2,
                "title": "Attack on Titan",
                "year": 2013,
                "path": "/tv/Attack on Titan",
                "monitored": True,
                "seasons": [],
            }
        ]
    )
    respx.get("https://sonarr.local:8989/api/v3/episodefile").respond(
        json=[
            {
                "id": 201,
                "seriesId": 2,
                "seasonNumber": 1,
                "relativePath": "AOT.S01E01.mkv",
                "path": "/tv/Attack on Titan/AOT.S01E01.mkv",
                "size": 2_000_000_000,
                "dateAdded": "2023-06-01T00:00:00Z",
                "mediaInfo": {
                    "audioLanguages": "Japanese",
                    "videoCodec": "x265",
                    "resolution": "1080p",
                },
            }
        ]
    )
    respx.get("https://sonarr.local:8989/api/v3/episode").respond(
        json=[
            {
                "id": 2001,
                "seriesId": 2,
                "episodeFileId": 201,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "To You",
            }
        ]
    )
    respx.get("https://sonarr.local:8989/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 20001,
                    "seriesId": 2,
                    "episodeId": 2001,
                    "sourceTitle": "AOT.S01E01",
                    "eventType": "downloadFolderImported",
                    "date": "2023-06-01T12:00:00Z",
                    "data": {"fileId": "201"},
                }
            ],
        }
    )

    # Mock radarr-4k
    respx.get("http://192.168.1.100:7878/api/v3/movie").respond(json=[])
    respx.get("http://192.168.1.100:7878/api/v3/moviefile").respond(json=[])
    respx.get("http://192.168.1.100:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )

    result = runner.invoke(app, ["--config", str(cfg), "scan"])
    assert result.exit_code == 0
    assert "Arr-Oldies Media Inventory" in result.output
    assert "The Matrix" in result.output
    assert "Attack on Titan" in result.output
    assert "Scan Summary & Storage Metrics" in result.output
    assert "2 (1 movies, 1 eps)" in result.output


@respx.mock
def test_cli_scan_format_json_pure_stdout(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify scan --format json outputs pure, valid JSON on stdout parseable by json.loads()."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Inception",
                "year": 2010,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 10_000_000_000,
                "dateAdded": "2022-01-01T00:00:00Z",
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "Inc",
                    "eventType": "downloadFolderImported",
                    "date": "2022-01-01T10:00:00Z",
                    "data": {"fileId": "10"},
                }
            ],
        }
    )

    result = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "--format", "json"]
    )
    assert result.exit_code == 0

    parsed = json.loads(result.stdout)
    assert parsed["metadata"]["total_matched_items"] == 1
    assert parsed["metadata"]["target_instances"] == ["radarr-main"]
    assert parsed["summary"]["movie_count"] == 1
    assert len(parsed["items"]) == 1
    assert parsed["items"][0]["title"] == "Inception"
    assert parsed["items"][0]["size_human"] == "9.31 GiB"
    assert "\x1b[" not in result.stdout


@respx.mock
def test_cli_scan_limit_flag(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify --limit n restricts output items while summary displays total matched counts."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Movie 1",
                "year": 2020,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "Movie 2",
                "year": 2021,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 3,
                "title": "Movie 3",
                "year": 2022,
                "path": "/m/3",
                "monitored": True,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2021-01-01T00:00:00Z",
            },
            {
                "id": 20,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 2_000_000_000,
                "dateAdded": "2022-01-01T00:00:00Z",
            },
            {
                "id": 30,
                "movieId": 3,
                "relativePath": "3.mkv",
                "path": "/m/3/3.mkv",
                "size": 3_000_000_000,
                "dateAdded": "2023-01-01T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 3,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M1",
                    "eventType": "downloadFolderImported",
                    "date": "2021-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                },
                {
                    "id": 2,
                    "movieId": 2,
                    "sourceTitle": "M2",
                    "eventType": "downloadFolderImported",
                    "date": "2022-01-01T00:00:00Z",
                    "data": {"fileId": "20"},
                },
                {
                    "id": 3,
                    "movieId": 3,
                    "sourceTitle": "M3",
                    "eventType": "downloadFolderImported",
                    "date": "2023-01-01T00:00:00Z",
                    "data": {"fileId": "30"},
                },
            ],
        }
    )

    # Test limit=1 in table mode
    result_table = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "--limit", "1"]
    )
    assert result_table.exit_code == 0
    assert "Showing top 1 of 3 items" in result_table.output
    assert "Movie 1" in result_table.output

    # Test limit=2 in JSON mode
    result_json = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "--limit", "2", "--format", "json"]
    )
    assert result_json.exit_code == 0
    parsed = json.loads(result_json.stdout)
    assert parsed["metadata"]["total_matched_items"] == 3
    assert parsed["metadata"]["displayed_items"] == 2
    assert len(parsed["items"]) == 2


@respx.mock
def test_cli_scan_filtering_options(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify various filter flags: --type, --audio-lang, --min-size, --older-than, --no-summary."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Old Large Japanese Movie",
                "year": 2015,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "New Small English Movie",
                "year": 2024,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 10_000_000_000,
                "dateAdded": "2018-01-01T00:00:00Z",
                "mediaInfo": {"audioLanguages": "Japanese"},
            },
            {
                "id": 20,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 500_000_000,
                "dateAdded": "2026-08-01T00:00:00Z",
                "mediaInfo": {"audioLanguages": "English"},
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 2,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M1",
                    "eventType": "downloadFolderImported",
                    "date": "2018-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                },
                {
                    "id": 2,
                    "movieId": 2,
                    "sourceTitle": "M2",
                    "eventType": "downloadFolderImported",
                    "date": "2026-08-01T00:00:00Z",
                    "data": {"fileId": "20"},
                },
            ],
        }
    )

    # Filter by audio-lang ja
    res_ja = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "-l", "ja", "--no-summary"]
    )
    assert res_ja.exit_code == 0
    assert "Old Large Japanese Movie" in res_ja.output
    assert "New Small English Movie" not in res_ja.output
    assert "Scan Summary & Storage Metrics" not in res_ja.output

    # Filter by min-size 5GB
    res_size = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "--min-size", "5GB"]
    )
    assert res_size.exit_code == 0
    assert "Old Large Japanese Movie" in res_size.output
    assert "New Small English Movie" not in res_size.output

    # Filter by older-than 1y
    res_age = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "--older-than", "1y"]
    )
    assert res_age.exit_code == 0
    assert "Old Large Japanese Movie" in res_age.output
    assert "New Small English Movie" not in res_age.output


def test_cli_scan_invalid_inputs_exit_2(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify CLI argument errors (unknown instance, invalid size string, invalid age) exit with code 2."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    # Unknown instance
    res_inst = runner.invoke(app, ["--config", str(cfg), "scan", "-i", "nonexistent"])
    assert res_inst.exit_code == 2
    assert "Instance 'nonexistent' not found" in res_inst.output

    # Invalid size
    res_size = runner.invoke(app, ["--config", str(cfg), "scan", "--min-size", "invalid_size"])
    assert res_size.exit_code == 2
    assert "Error:" in res_size.output

    # Invalid age
    res_age = runner.invoke(app, ["--config", str(cfg), "scan", "--older-than", "invalid_age"])
    assert res_age.exit_code == 2
    assert "Error:" in res_age.output


@respx.mock
def test_cli_scan_all_instances_fail_exits_1(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify scan exits with code 1 when all target instances fail."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(status_code=500, text="Server Error")

    result = runner.invoke(app, ["--config", str(cfg), "scan", "-i", "radarr-main"])
    assert result.exit_code == 1
    assert "All target instances failed to fetch data" in result.output


@respx.mock
def test_cli_scan_partial_failure_continues(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify partial failure displays available data from healthy instances and warns about failed ones."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    # radarr-main succeeds
    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Survivor Movie",
                "year": 2020,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-01T00:00:00Z",
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "S",
                    "eventType": "downloadFolderImported",
                    "date": "2020-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                }
            ],
        }
    )

    # radarr-4k fails
    respx.get("http://192.168.1.100:7878/api/v3/movie").respond(
        status_code=503, text="Service Unavailable"
    )

    result = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "-i", "radarr-4k"]
    )
    assert result.exit_code == 0
    assert "Survivor Movie" in result.output
    assert "Warning:" in result.output
    assert "radarr-4k" in result.output


@respx.mock
def test_cli_scan_empty_match(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify scan behavior when 0 items match filter criteria."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Movie 1",
                "year": 2020,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-01T00:00:00Z",
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M",
                    "eventType": "downloadFolderImported",
                    "date": "2020-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                }
            ],
        }
    )

    # Filter with non-matching language
    res_table = runner.invoke(
        app, ["--config", str(cfg), "scan", "-i", "radarr-main", "-l", "klingon"]
    )
    assert res_table.exit_code == 0
    assert "No media items matched the specified criteria." in res_table.output

    # JSON mode empty match
    res_json = runner.invoke(
        app,
        ["--config", str(cfg), "scan", "-i", "radarr-main", "-l", "klingon", "--format", "json"],
    )
    assert res_json.exit_code == 0
    parsed = json.loads(res_json.stdout)
    assert parsed["metadata"]["total_matched_items"] == 0
    assert parsed["summary"]["total_items"] == 0
    assert parsed["items"] == []


@respx.mock
def test_cli_scan_sorting_options(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify --sort and --sort-dir flags control ordering."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "B Movie",
                "year": 2020,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "A Movie",
                "year": 2021,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 3,
                "title": "C Movie",
                "year": 2022,
                "path": "/m/3",
                "monitored": True,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 3_000_000_000,
                "dateAdded": "2021-01-01T00:00:00Z",
            },
            {
                "id": 20,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2022-01-01T00:00:00Z",
            },
            {
                "id": 30,
                "movieId": 3,
                "relativePath": "3.mkv",
                "path": "/m/3/3.mkv",
                "size": 5_000_000_000,
                "dateAdded": "2023-01-01T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 3,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M1",
                    "eventType": "downloadFolderImported",
                    "date": "2021-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                },
                {
                    "id": 2,
                    "movieId": 2,
                    "sourceTitle": "M2",
                    "eventType": "downloadFolderImported",
                    "date": "2022-01-01T00:00:00Z",
                    "data": {"fileId": "20"},
                },
                {
                    "id": 3,
                    "movieId": 3,
                    "sourceTitle": "M3",
                    "eventType": "downloadFolderImported",
                    "date": "2023-01-01T00:00:00Z",
                    "data": {"fileId": "30"},
                },
            ],
        }
    )

    # Sort by size descending
    res_size = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "-i",
            "radarr-main",
            "--sort",
            "size",
            "--sort-dir",
            "desc",
            "--format",
            "json",
        ],
    )
    assert res_size.exit_code == 0
    parsed_size = json.loads(res_size.stdout)
    assert [item["title"] for item in parsed_size["items"]] == ["C Movie", "B Movie", "A Movie"]

    # Sort by title ascending
    res_title = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "-i",
            "radarr-main",
            "--sort",
            "title",
            "--sort-dir",
            "asc",
            "--format",
            "json",
        ],
    )
    assert res_title.exit_code == 0
    parsed_title = json.loads(res_title.stdout)
    assert [item["title"] for item in parsed_title["items"]] == ["A Movie", "B Movie", "C Movie"]


@respx.mock
def test_cli_scan_date_cutoffs(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify --before and --after date filtering flags."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "2019 Film",
                "year": 2019,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "2021 Film",
                "year": 2021,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 3,
                "title": "2023 Film",
                "year": 2023,
                "path": "/m/3",
                "monitored": True,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2019-06-01T00:00:00Z",
            },
            {
                "id": 20,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2021-06-01T00:00:00Z",
            },
            {
                "id": 30,
                "movieId": 3,
                "relativePath": "3.mkv",
                "path": "/m/3/3.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2023-06-01T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 3,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M1",
                    "eventType": "downloadFolderImported",
                    "date": "2019-06-01T00:00:00Z",
                    "data": {"fileId": "10"},
                },
                {
                    "id": 2,
                    "movieId": 2,
                    "sourceTitle": "M2",
                    "eventType": "downloadFolderImported",
                    "date": "2021-06-01T00:00:00Z",
                    "data": {"fileId": "20"},
                },
                {
                    "id": 3,
                    "movieId": 3,
                    "sourceTitle": "M3",
                    "eventType": "downloadFolderImported",
                    "date": "2023-06-01T00:00:00Z",
                    "data": {"fileId": "30"},
                },
            ],
        }
    )

    # Before 2022-01-01
    res_before = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "-i",
            "radarr-main",
            "--before",
            "2022-01-01",
            "--format",
            "json",
        ],
    )
    assert res_before.exit_code == 0
    parsed_before = json.loads(res_before.stdout)
    assert [item["title"] for item in parsed_before["items"]] == ["2019 Film", "2021 Film"]

    # After 2020-01-01
    res_after = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "-i",
            "radarr-main",
            "--after",
            "2020-01-01",
            "--format",
            "json",
        ],
    )
    assert res_after.exit_code == 0
    parsed_after = json.loads(res_after.stdout)
    assert [item["title"] for item in parsed_after["items"]] == ["2021 Film", "2023 Film"]


@respx.mock
def test_cli_scan_complex_combined_query(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify complex combined filter/sort/limit query."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Match Film",
                "year": 2018,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "Small Film",
                "year": 2018,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 10_000_000_000,
                "dateAdded": "2018-01-01T00:00:00Z",
            },
            {
                "id": 20,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 500_000_000,
                "dateAdded": "2018-01-01T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 2,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M1",
                    "eventType": "downloadFolderImported",
                    "date": "2018-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                },
                {
                    "id": 2,
                    "movieId": 2,
                    "sourceTitle": "M2",
                    "eventType": "downloadFolderImported",
                    "date": "2018-01-01T00:00:00Z",
                    "data": {"fileId": "20"},
                },
            ],
        }
    )

    respx.get("http://192.168.1.100:7878/api/v3/movie").respond(json=[])
    respx.get("http://192.168.1.100:7878/api/v3/moviefile").respond(json=[])
    respx.get("http://192.168.1.100:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )

    res = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "--radarr",
            "--min-size",
            "5GB",
            "--older-than",
            "1y",
            "--limit",
            "10",
            "--format",
            "json",
        ],
    )
    assert res.exit_code == 0
    parsed = json.loads(res.stdout)
    assert parsed["metadata"]["total_matched_items"] == 1
    assert parsed["items"][0]["title"] == "Match Film"


@respx.mock
def test_cli_scan_composite_age_filters(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify scan filters correctly using composite time duration strings (e.g. 1y1m1d, 6m2w)."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Very Old Film",
                "year": 2015,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "Recent Film",
                "year": 2026,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 10_000_000_000,
                "dateAdded": "2018-01-01T00:00:00Z",
            },
            {
                "id": 20,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 5_000_000_000,
                "dateAdded": "2026-08-15T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 2,
            "records": [
                {
                    "id": 1,
                    "movieId": 1,
                    "sourceTitle": "M1",
                    "eventType": "downloadFolderImported",
                    "date": "2018-01-01T00:00:00Z",
                    "data": {"fileId": "10"},
                },
                {
                    "id": 2,
                    "movieId": 2,
                    "sourceTitle": "M2",
                    "eventType": "downloadFolderImported",
                    "date": "2026-08-15T00:00:00Z",
                    "data": {"fileId": "20"},
                },
            ],
        }
    )

    # Test --older-than 1y1m1d (396 days) -> only Very Old Film matches
    res_older = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "-i",
            "radarr-main",
            "--older-than",
            "1y1m1d",
            "--format",
            "json",
        ],
    )
    assert res_older.exit_code == 0
    parsed_older = json.loads(res_older.stdout)
    assert parsed_older["metadata"]["total_matched_items"] == 1
    assert parsed_older["items"][0]["title"] == "Very Old Film"

    # Test --newer-than 6m2w (194 days) -> only Recent Film matches
    res_newer = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "scan",
            "-i",
            "radarr-main",
            "--newer-than",
            "6m2w",
            "--format",
            "json",
        ],
    )
    assert res_newer.exit_code == 0
    parsed_newer = json.loads(res_newer.stdout)
    assert parsed_newer["metadata"]["total_matched_items"] == 1
    assert parsed_newer["items"][0]["title"] == "Recent Film"
