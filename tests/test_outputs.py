import json
import re
from collections import Counter
from pathlib import Path

REPORT_PATH = Path("/app/report.json")
LOG_PATH = Path("/app/access.log")


def _load_report():
    assert REPORT_PATH.exists(), "no report.json found at /app/report.json"
    with open(REPORT_PATH) as f:
        return json.load(f)


def _ground_truth():
    """Independently recompute total_requests, unique_ips, and top_path
    straight from access.log, so tests don't just trust solve.py's own math."""
    total = 0
    ips = set()
    paths = Counter()
    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            ips.add(line.split()[0])
            m = re.search(r'"(?:GET|POST|PUT|DELETE|HEAD|PATCH) (\S+) ', line)
            if m:
                paths[m.group(1)] += 1
    top_path = paths.most_common(1)[0][0]
    return total, len(ips), top_path


def test_report_is_valid_json_with_required_keys():
    """Criterion 1: /app/report.json exists and is valid JSON containing
    exactly the keys total_requests, unique_ips, top_path."""
    report = _load_report()
    assert set(report.keys()) == {"total_requests", "unique_ips", "top_path"}, (
        f"expected exactly total_requests, unique_ips, top_path, got {sorted(report.keys())}"
    )


def test_total_requests_matches_log():
    """Criterion 2: total_requests equals the number of non-blank lines in access.log."""
    report = _load_report()
    expected_total, _, _ = _ground_truth()
    assert report["total_requests"] == expected_total, (
        f"expected total_requests={expected_total}, got {report['total_requests']}"
    )


def test_unique_ips_matches_log():
    """Criterion 3: unique_ips equals the number of distinct client IPs in access.log."""
    report = _load_report()
    _, expected_unique_ips, _ = _ground_truth()
    assert report["unique_ips"] == expected_unique_ips, (
        f"expected unique_ips={expected_unique_ips}, got {report['unique_ips']}"
    )


def test_top_path_matches_log():
    """Criterion 4: top_path equals the most frequently requested path in
    access.log, with ties broken by first appearance."""
    report = _load_report()
    _, _, expected_top_path = _ground_truth()
    assert report["top_path"] == expected_top_path, (
        f"expected top_path={expected_top_path!r}, got {report.get('top_path')!r}"
    )