"""Integration tests for Typer CLI `clean` command, safety guards, and action execution."""

import json
from pathlib import Path
from unittest.mock import patch

import respx
from typer.testing import CliRunner

from arr_oldies.cli import app

runner = CliRunner(env={"COLUMNS": "160"})


def mock_radarr_sonarr_instances() -> None:
    """Helper to mock standard Radarr and Sonarr instance library & history endpoints."""
    # Radarr movies & files & history
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
                "dateAdded": "2022-01-01T00:00:00Z",
                "mediaInfo": {
                    "audioLanguages": "Japanese",
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
                    "date": "2022-01-01T02:00:00Z",
                    "data": {"fileId": "101"},
                }
            ],
        }
    )

    # Sonarr series & files & episodes & history
    respx.get("https://sonarr.local:8989/api/v3/series").respond(
        json=[
            {
                "id": 2,
                "title": "Attack on Titan",
                "path": "/tv/Attack on Titan",
                "monitored": True,
            }
        ]
    )
    respx.get("https://sonarr.local:8989/api/v3/episodefile", params={"seriesId": 2}).respond(
        json=[
            {
                "id": 201,
                "seriesId": 2,
                "relativePath": "Season 01/S01E01.mkv",
                "path": "/tv/Attack on Titan/Season 01/S01E01.mkv",
                "size": 2_000_000_000,
                "dateAdded": "2023-01-01T00:00:00Z",
                "mediaInfo": {
                    "audioLanguages": "Japanese",
                    "videoCodec": "x265",
                    "resolution": "1080p",
                },
            }
        ]
    )
    respx.get("https://sonarr.local:8989/api/v3/episode", params={"episodeFileId": 201}).respond(
        json=[
            {
                "id": 2001,
                "seriesId": 2,
                "episodeFileId": 201,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "To You, in 2000 Years",
                "monitored": True,
            }
        ]
    )
    respx.get(
        "https://sonarr.local:8989/api/v3/history",
        params={
            "page": 1,
            "pageSize": 1000,
            "sortKey": "date",
            "sortDirection": "descending",
            "includeSeries": "true",
            "includeEpisode": "true",
        },
    ).respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 20001,
                    "seriesId": 2,
                    "episodeId": 2001,
                    "sourceTitle": "Attack.on.Titan.S01E01",
                    "eventType": "downloadFolderImported",
                    "date": "2023-01-01T03:00:00Z",
                    "data": {"fileId": "201"},
                }
            ],
        }
    )


def test_cli_clean_missing_action_flag(config_file_path: Path) -> None:
    """Verify clean command errors with exit code 2 when no action flag is specified."""
    result = runner.invoke(app, ["clean", "--config", str(config_file_path)])
    assert result.exit_code == 2
    assert "No action specified" in result.output


@respx.mock
def test_cli_clean_dry_run_default_table(config_file_path: Path) -> None:
    """Verify clean defaults to dry-run simulation mode without issuing mutation requests."""
    mock_radarr_sonarr_instances()
    delete_route = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )

    result = runner.invoke(
        app, ["clean", "--delete", "--radarr", "--config", str(config_file_path)]
    )
    assert result.exit_code == 0
    assert "Arr-Oldies Dry-Run Action Simulation" in result.output
    assert "The Matrix" in result.output
    assert "DRY-RUN MODE: No changes were made." in result.output
    assert not delete_route.called


@respx.mock
def test_cli_clean_dry_run_json_output(config_file_path: Path) -> None:
    """Verify clean --format json in dry-run outputs parseable JSON plan."""
    mock_radarr_sonarr_instances()

    result = runner.invoke(
        app,
        ["clean", "--delete", "--radarr", "--format", "json", "--config", str(config_file_path)],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["metadata"]["mode"] == "dry-run"
    assert parsed["metadata"]["dry_run"] is True
    assert parsed["summary"]["total_items"] == 1
    assert len(parsed["items"]) == 1


@respx.mock
def test_cli_clean_execute_non_interactive_without_yes_fails(config_file_path: Path) -> None:
    """Verify clean --execute in non-interactive mode without --yes fails fast with exit code 1."""
    mock_radarr_sonarr_instances()

    with patch("sys.stdin.isatty", return_value=False):
        result = runner.invoke(
            app,
            ["clean", "--delete", "--execute", "--radarr", "--config", str(config_file_path)],
        )
        assert result.exit_code == 1
        assert "Interactive confirmation required in execute mode" in result.output


@respx.mock
def test_cli_clean_execute_interactive_declined(config_file_path: Path) -> None:
    """Verify clean --execute with interactive confirmation 'n' aborts cleanly."""
    mock_radarr_sonarr_instances()
    delete_route = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )

    with (
        patch("typer.testing._NamedTextIOWrapper.isatty", return_value=True),
        patch("typer.confirm", return_value=False),
    ):
        result = runner.invoke(
            app,
            ["clean", "--delete", "--execute", "--radarr", "--config", str(config_file_path)],
        )
        assert result.exit_code == 0
        assert "Operation aborted by user" in result.output
        assert not delete_route.called


@respx.mock
def test_cli_clean_execute_interactive_confirmed(config_file_path: Path) -> None:
    """Verify clean --execute with interactive confirmation 'y' executes mutations."""
    mock_radarr_sonarr_instances()
    delete_route = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )

    with (
        patch("typer.testing._NamedTextIOWrapper.isatty", return_value=True),
        patch("typer.confirm", return_value=True),
    ):
        result = runner.invoke(
            app,
            ["clean", "--delete", "--execute", "--radarr", "--config", str(config_file_path)],
        )
        assert result.exit_code == 0
        assert "Arr-Oldies Execution Report" in result.output
        assert "SUCCESS" in result.output
        assert delete_route.called


@respx.mock
def test_cli_clean_execute_yes_bypass(config_file_path: Path) -> None:
    """Verify clean --execute --yes bypasses interactive prompt and executes mutations immediately."""
    mock_radarr_sonarr_instances()
    delete_route = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )

    result = runner.invoke(
        app,
        ["clean", "--delete", "--execute", "--yes", "--radarr", "--config", str(config_file_path)],
    )
    assert result.exit_code == 0
    assert "Arr-Oldies Execution Report" in result.output
    assert "SUCCESS" in result.output
    assert delete_route.called


@respx.mock
def test_cli_clean_unmonitor_actions(config_file_path: Path) -> None:
    """Verify --unmonitor triggers movie and series unmonitoring."""
    mock_radarr_sonarr_instances()
    route_radarr_unmonitor = respx.put("http://localhost:7878/api/v3/movie/editor").respond(
        status_code=202
    )
    route_sonarr_unmonitor = respx.put("https://sonarr.local:8989/api/v3/series/editor").respond(
        status_code=202
    )

    result = runner.invoke(
        app,
        [
            "clean",
            "--unmonitor",
            "--execute",
            "--yes",
            "-i",
            "radarr-main",
            "-i",
            "sonarr-tv",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    assert route_radarr_unmonitor.called
    assert route_sonarr_unmonitor.called


@respx.mock
def test_cli_clean_unmonitor_episode_action(config_file_path: Path) -> None:
    """Verify --unmonitor-episode triggers episode unmonitoring for Sonarr."""
    mock_radarr_sonarr_instances()
    route_episodes = respx.put("https://sonarr.local:8989/api/v3/episode/monitor").respond(
        status_code=200
    )

    result = runner.invoke(
        app,
        [
            "clean",
            "--unmonitor-episode",
            "--execute",
            "--yes",
            "--sonarr",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    assert route_episodes.called


@respx.mock
def test_cli_clean_remove_action(config_file_path: Path) -> None:
    """Verify --remove triggers library deletion for movie/series."""
    mock_radarr_sonarr_instances()
    route_radarr_remove = respx.delete(
        "http://localhost:7878/api/v3/movie/1",
        params={"deleteFiles": "false", "addImportExclusion": "false"},
    ).respond(status_code=200)

    result = runner.invoke(
        app,
        ["clean", "--remove", "--execute", "--yes", "--radarr", "--config", str(config_file_path)],
    )
    assert result.exit_code == 0
    assert route_radarr_remove.called


@respx.mock
def test_cli_clean_json_output_purity_execute(config_file_path: Path) -> None:
    """Verify --format json outputs pure JSON to stdout during execution."""
    mock_radarr_sonarr_instances()
    respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(status_code=200)

    result = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--execute",
            "--yes",
            "--radarr",
            "--format",
            "json",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["metadata"]["mode"] == "execute"
    assert parsed["summary"]["successful_count"] == 1
    assert parsed["summary"]["failed_count"] == 0
    assert len(parsed["results"]) == 1


@respx.mock
def test_cli_clean_partial_failure_handling(config_file_path: Path) -> None:
    """Verify partial failure during execution logs failed status but finishes cleanly."""
    mock_radarr_sonarr_instances()
    # Radarr delete fails with 500
    respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=500, text="Internal Error"
    )
    # Sonarr delete succeeds with 204
    respx.delete("https://sonarr.local:8989/api/v3/episodefile/201").respond(status_code=204)

    result = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--execute",
            "--yes",
            "-i",
            "radarr-main",
            "-i",
            "sonarr-tv",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    assert "SUCCESS" in result.output
    assert "FAILED" in result.output
    assert "Summary: 1 succeeded, 1 failed" in result.output


@respx.mock
def test_cli_clean_no_matching_items(config_file_path: Path) -> None:
    """Verify clean command when no items match filters produces an empty plan and exits 0."""
    mock_radarr_sonarr_instances()

    result = runner.invoke(
        app,
        ["clean", "--delete", "--audio-lang", "fr", "--config", str(config_file_path)],
    )
    assert result.exit_code == 0
    assert "Arr-Oldies Dry-Run Action Simulation" in result.output


@respx.mock
def test_cli_clean_combined_actions_with_filtering_and_sorting(config_file_path: Path) -> None:
    """Verify combined --delete --unmonitor with language filter, age cutoff, and sorting."""
    mock_radarr_sonarr_instances()
    route_radarr_unmonitor = respx.put("http://localhost:7878/api/v3/movie/editor").respond(
        status_code=202
    )
    route_radarr_delete = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )

    result = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--unmonitor",
            "--execute",
            "--yes",
            "--audio-lang",
            "ja",
            "--older-than",
            "1y",
            "--sort",
            "age",
            "--sort-dir",
            "desc",
            "--limit",
            "1",
            "--radarr",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    assert "Arr-Oldies Execution Report" in result.output
    assert route_radarr_unmonitor.called
    assert route_radarr_delete.called


@respx.mock
def test_cli_clean_all_instances_fetch_failure(config_file_path: Path) -> None:
    """Verify clean exits with code 1 when all target instances fail to fetch."""
    respx.get("http://localhost:7878/api/v3/movie").respond(status_code=500, text="Server Down")

    result = runner.invoke(
        app,
        ["clean", "--delete", "--radarr", "--config", str(config_file_path)],
    )
    assert result.exit_code == 1
    assert "All target instances failed to fetch data" in result.output
