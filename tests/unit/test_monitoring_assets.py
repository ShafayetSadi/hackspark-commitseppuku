import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_prometheus_config_self_scrapes_and_loads_rules():
    content = (ROOT / "monitoring" / "prometheus" / "prometheus.yml").read_text()

    assert "rule_files:" in content
    assert "/etc/prometheus/rules/hackspark-alerts.yml" in content
    assert "job_name: prometheus" in content
    assert 'targets: ["localhost:9090"]' in content


def test_prometheus_rules_define_baseline_alerts():
    content = (ROOT / "monitoring" / "prometheus" / "rules" / "hackspark-alerts.yml").read_text()

    assert "alert: HacksparkTargetDown" in content
    assert "alert: HacksparkHigh5xxRate" in content
    assert (
        'job=~"prometheus|api-gateway|user-service|rental-service|analytics-service|agentic-service|cadvisor"'
        in content
    )


def test_dashboard_covers_priority_observability_panels():
    dashboard = json.loads(
        (ROOT / "monitoring" / "grafana" / "dashboards" / "hackspark-overview.json").read_text()
    )
    panels = {panel["title"]: panel for panel in dashboard["panels"]}

    assert "In-Flight Requests" in panels
    assert "Route p95 Latency" in panels
    assert "Route Error Rate" in panels
    assert "Active Alerts" in panels
    assert "Prometheus Health" in panels
    assert (
        'job=~"prometheus|api-gateway|user-service|rental-service|analytics-service|agentic-service|cadvisor"'
        in (panels["Service Health"]["targets"][0]["expr"])
    )
