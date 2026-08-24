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
                "seasonNumber": 1,
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
    assert "--unmonitor-season" in result.output


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
    """Verify --unmonitor triggers movie unmonitoring for Radarr and episode unmonitoring for Sonarr."""
    mock_radarr_sonarr_instances()
    route_radarr_unmonitor = respx.put("http://localhost:7878/api/v3/movie/editor").respond(
        status_code=202
    )
    route_sonarr_unmonitor_episodes = respx.put(
        "https://sonarr.local:8989/api/v3/episode/monitor"
    ).respond(status_code=200)

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
    assert route_sonarr_unmonitor_episodes.called


@respx.mock
def test_cli_clean_unmonitor_series_action(config_file_path: Path) -> None:
    """Verify --unmonitor-series triggers series unmonitoring for Sonarr."""
    mock_radarr_sonarr_instances()
    route_series = respx.put("https://sonarr.local:8989/api/v3/series/editor").respond(
        status_code=202
    )

    result = runner.invoke(
        app,
        [
            "clean",
            "--unmonitor-series",
            "--execute",
            "--yes",
            "--sonarr",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    assert route_series.called


@respx.mock
def test_cli_clean_unmonitor_season_action(config_file_path: Path) -> None:
    """Verify --unmonitor-season triggers season unmonitoring for Sonarr."""
    mock_radarr_sonarr_instances()
    series_data = {
        "id": 2,
        "title": "Attack on Titan",
        "monitored": True,
        "seasons": [
            {"seasonNumber": 1, "monitored": True},
        ],
    }
    route_get_series = respx.get("https://sonarr.local:8989/api/v3/series/2").respond(
        json=series_data
    )
    route_put_series = respx.put("https://sonarr.local:8989/api/v3/series/2").respond(
        status_code=200
    )

    result = runner.invoke(
        app,
        [
            "clean",
            "--unmonitor-season",
            "--execute",
            "--yes",
            "--sonarr",
            "--config",
            str(config_file_path),
        ],
    )
    assert result.exit_code == 0
    assert route_get_series.called
    assert route_put_series.called
    updated_payload = json.loads(route_put_series.calls.last.request.content)
    assert updated_payload["seasons"][0]["seasonNumber"] == 1
    assert updated_payload["seasons"][0]["monitored"] is False


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


@respx.mock
def test_cli_clean_composite_age_filters(config_file_path: Path) -> None:
    """Verify clean filters items correctly using composite duration strings in dry-run and execution modes."""
    mock_radarr_sonarr_instances()
    route_delete = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )

    # Dry-run with --older-than 1y1m1d (396 days) matches The Matrix (imported in 2022)
    res_match = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--radarr",
            "--older-than",
            "1y1m1d",
            "--newer-than",
            "10y",
            "--format",
            "json",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_match.exit_code == 0
    parsed = json.loads(res_match.stdout)
    assert parsed["summary"]["total_items"] == 1
    assert parsed["items"][0]["item"]["title"] == "The Matrix"
    assert not route_delete.called

    # Execution with --older-than 1y1m1d --execute --yes
    res_exec = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--radarr",
            "--older-than",
            "1y1m1d",
            "--execute",
            "--yes",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_exec.exit_code == 0
    assert "Arr-Oldies Execution Report" in res_exec.output
    assert route_delete.called

    # Filter with older-than 50y matches nothing
    res_empty = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--radarr",
            "--older-than",
            "50y",
            "--format",
            "json",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_empty.exit_code == 0
    parsed_empty = json.loads(res_empty.stdout)
    assert parsed_empty["summary"]["total_items"] == 0
    assert parsed_empty["items"] == []


@respx.mock
def test_cli_clean_monitored_and_unmonitored_filters(config_file_path: Path) -> None:
    """Verify clean --monitored (and aliases) and --unmonitored filters and mutual exclusion."""
    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Monitored Film",
                "year": 2020,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 2,
                "title": "Unmonitored Film",
                "year": 2021,
                "path": "/m/2",
                "monitored": False,
                "hasFile": True,
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 101,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-01T00:00:00Z",
            },
            {
                "id": 102,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 2_000_000_000,
                "dateAdded": "2021-01-01T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )

    route_unmonitor = respx.put("http://localhost:7878/api/v3/movie/editor").respond(
        status_code=202
    )
    route_delete_101 = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )
    route_delete_102 = respx.delete("http://localhost:7878/api/v3/moviefile/102").respond(
        status_code=200
    )

    # 1. Test clean --unmonitor --only-monitored dry-run
    res_unmon_dry = runner.invoke(
        app,
        [
            "clean",
            "--unmonitor",
            "--only-monitored",
            "-i",
            "radarr-main",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_unmon_dry.exit_code == 0
    assert "Monitored Film" in res_unmon_dry.output
    assert "Unmonitored Film" not in res_unmon_dry.output
    assert not route_unmonitor.called

    # 1b. Test clean --unmonitor --only-monitored execution
    res_unmon_exec = runner.invoke(
        app,
        [
            "clean",
            "--unmonitor",
            "--only-monitored",
            "--execute",
            "--yes",
            "-i",
            "radarr-main",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_unmon_exec.exit_code == 0
    assert "radarr-main:101" in res_unmon_exec.output
    assert "radarr-main:102" not in res_unmon_exec.output
    assert route_unmonitor.called
    assert not route_delete_101.called
    assert not route_delete_102.called

    # 2. Test clean --delete --unmonitored dry-run
    res_del_dry = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--unmonitored",
            "-i",
            "radarr-main",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_del_dry.exit_code == 0
    assert "Unmonitored Film" in res_del_dry.output
    assert "Monitored Film" not in res_del_dry.output

    # 2b. Test clean --delete --only-unmonitored in JSON mode
    res_del_json = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--only-unmonitored",
            "-i",
            "radarr-main",
            "--format",
            "json",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_del_json.exit_code == 0
    parsed_json = json.loads(res_del_json.stdout)
    assert len(parsed_json["items"]) == 1
    assert parsed_json["items"][0]["item"]["title"] == "Unmonitored Film"

    # 2c. Test clean --delete --unmonitored execution
    res_del_exec = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--unmonitored",
            "--execute",
            "--yes",
            "-i",
            "radarr-main",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_del_exec.exit_code == 0
    assert "radarr-main:102" in res_del_exec.output
    assert "radarr-main:101" not in res_del_exec.output
    assert route_delete_102.called
    assert not route_delete_101.called

    # 3. Test mutual exclusion check
    res_mutex = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--monitored",
            "--unmonitored",
            "-i",
            "radarr-main",
            "--config",
            str(config_file_path),
        ],
    )
    assert res_mutex.exit_code == 2
    assert "Cannot specify both --monitored and --unmonitored filter flags." in res_mutex.output


@respx.mock
def test_cli_clean_with_negative_language_and_tag_flags(config_file_path: Path) -> None:
    """Verify clean command dry-run action planning with --!l, --title, --tag, and --!tag flags."""
    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Star Wars: A New Hope",
                "year": 1977,
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
                "tags": [1],
            },
            {
                "id": 2,
                "title": "Star Wars: The Empire Strikes Back",
                "year": 1980,
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
                "tags": [1, 2],
            },
            {
                "id": 3,
                "title": "Star Trek",
                "year": 2009,
                "path": "/m/3",
                "monitored": True,
                "hasFile": True,
                "tags": [1],
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 101,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-01T00:00:00Z",
                "mediaInfo": {"audioLanguages": "English"},
            },
            {
                "id": 102,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-02T00:00:00Z",
                "mediaInfo": {"audioLanguages": "Portuguese, English"},
            },
            {
                "id": 103,
                "movieId": 3,
                "relativePath": "3.mkv",
                "path": "/m/3/3.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-03T00:00:00Z",
                "mediaInfo": {"audioLanguages": "English"},
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )
    respx.get("http://localhost:7878/api/v3/tag").respond(
        json=[
            {"id": 1, "label": "4k"},
            {"id": 2, "label": "archive"},
        ]
    )

    # Clean with --title "star wars" --!l "pt-br" --tag "4k"
    res = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--title",
            "star wars",
            "--!l",
            "pt-br",
            "--tag",
            "4k",
            "-i",
            "radarr-main",
            "--format",
            "json",
            "--config",
            str(config_file_path),
        ],
    )
    assert res.exit_code == 0
    parsed = json.loads(res.stdout)
    assert parsed["summary"]["total_items"] == 1
    assert parsed["items"][0]["item"]["title"] == "Star Wars: A New Hope"


@respx.mock
def test_cli_clean_execution_with_tag_filter(config_file_path: Path) -> None:
    """Verify clean execution with --delete --tag only mutates tagged items."""
    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Movie 4K",
                "path": "/m/1",
                "monitored": True,
                "hasFile": True,
                "tags": [1],
            },
            {
                "id": 2,
                "title": "Movie 1080p",
                "path": "/m/2",
                "monitored": True,
                "hasFile": True,
                "tags": [],
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 101,
                "movieId": 1,
                "relativePath": "1.mkv",
                "path": "/m/1/1.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-01T00:00:00Z",
            },
            {
                "id": 102,
                "movieId": 2,
                "relativePath": "2.mkv",
                "path": "/m/2/2.mkv",
                "size": 1_000_000_000,
                "dateAdded": "2020-01-02T00:00:00Z",
            },
        ]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )
    respx.get("http://localhost:7878/api/v3/tag").respond(json=[{"id": 1, "label": "4k"}])

    route_delete_101 = respx.delete("http://localhost:7878/api/v3/moviefile/101").respond(
        status_code=200
    )
    route_delete_102 = respx.delete("http://localhost:7878/api/v3/moviefile/102").respond(
        status_code=200
    )

    res = runner.invoke(
        app,
        [
            "clean",
            "--delete",
            "--tag",
            "4k",
            "--execute",
            "--yes",
            "-i",
            "radarr-main",
            "--config",
            str(config_file_path),
        ],
    )
    assert res.exit_code == 0
    assert "Arr-Oldies Execution Report" in res.output
    assert route_delete_101.called
    assert not route_delete_102.called

