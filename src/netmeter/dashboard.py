"""Generate HTML dashboard with per-network graphs."""

import os
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from jinja2 import Template

from netmeter.config import DB_PATH, GRAPH_DPI, NETWORK_TYPE_LABELS, OUTPUT_DIR, PERIODS, Period
from netmeter.database import connect, fetch_data, get_network_stats, get_networks

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetMeter Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
        }
        h1 {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #38bdf8;
        }
        .updated {
            text-align: center;
            color: #64748b;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
        .network-section {
            max-width: 1200px;
            margin: 0 auto 3rem;
        }
        .network-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #1e293b;
        }
        .network-header h2 {
            font-size: 1.5rem;
            color: #f1f5f9;
        }
        .network-badge {
            background: #1e293b;
            color: #94a3b8;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.8rem;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: #1e293b;
            border-radius: 0.75rem;
            padding: 1.25rem;
            text-align: center;
        }
        .stat-card .label { color: #94a3b8; font-size: 0.85rem; }
        .stat-card .value { font-size: 1.75rem; font-weight: 700; margin: 0.25rem 0; }
        .stat-card .unit { color: #64748b; font-size: 0.8rem; }
        .stat-card.download .value { color: #22c55e; }
        .stat-card.upload .value { color: #3b82f6; }
        .stat-card.ping .value { color: #f59e0b; }
        .stat-card.count .value { color: #a78bfa; }
        .network-picker {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
            position: relative;
        }
        .network-picker select {
            appearance: none;
            -webkit-appearance: none;
            background: #1e293b;
            color: #e2e8f0;
            border: 2px solid #334155;
            border-radius: 0.75rem;
            padding: 0.75rem 3rem 0.75rem 1.25rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
            min-width: 280px;
            text-align: center;
        }
        .network-picker select:hover { border-color: #38bdf8; }
        .network-picker select:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
        }
        .network-picker select option {
            background: #1e293b;
            color: #e2e8f0;
            padding: 0.5rem;
        }
        .network-picker-wrapper {
            position: relative;
            display: inline-block;
        }
        .network-picker-wrapper::after {
            content: "\\25BE";
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #38bdf8;
            font-size: 1.2rem;
            pointer-events: none;
        }
        .network-section { display: none; }
        .network-section.active { display: block; }
        .comparison {
            max-width: 1200px;
            margin: 0 auto 2.5rem;
        }
        .comparison h2 {
            font-size: 1.25rem;
            color: #f1f5f9;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #1e293b;
        }
        .comparison table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            background: #1e293b;
            border-radius: 0.75rem;
            overflow: hidden;
        }
        .comparison th {
            background: #0f172a;
            color: #94a3b8;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.75rem 1rem;
            text-align: left;
        }
        .comparison td {
            padding: 0.75rem 1rem;
            border-top: 1px solid #334155;
            font-size: 0.95rem;
        }
        .comparison tr:hover td { background: #263348; }
        .comparison .net-name { font-weight: 600; color: #f1f5f9; }
        .comparison .net-type { color: #64748b; font-size: 0.8rem; margin-left: 0.5rem; }
        .comparison .val-down { color: #22c55e; font-weight: 600; }
        .comparison .val-up { color: #3b82f6; font-weight: 600; }
        .comparison .val-ping { color: #f59e0b; font-weight: 600; }
        .comparison .val-count { color: #a78bfa; }
        .comparison .best { position: relative; }
        .comparison .best::after {
            content: "\\2605";
            margin-left: 0.35rem;
            font-size: 0.75rem;
        }
        .graphs { display: flex; flex-direction: column; gap: 1.5rem; }
        .graph-card {
            background: #1e293b;
            border-radius: 0.75rem;
            padding: 1rem;
        }
        .graph-card h3 { color: #cbd5e1; font-size: 1rem; margin-bottom: 0.75rem; }
        .graph-card img { width: 100%; height: auto; border-radius: 0.5rem; }
    </style>
</head>
<body>
    <h1>NetMeter Dashboard</h1>
    <p class="updated">Updated: {{ updated }}</p>

    {% if networks|length > 1 %}
    <div class="comparison">
        <h2>Network Comparison</h2>
        <table>
            <thead>
                <tr>
                    <th>Network</th>
                    <th>Download</th>
                    <th>Upload</th>
                    <th>Ping</th>
                    <th>Tests</th>
                    <th>Last</th>
                </tr>
            </thead>
            <tbody>
                {% for network in networks %}
                <tr>
                    <td>
                        <span class="net-name">{{ network.name }}</span>
                        <span class="net-type">{{ network.type_label }}</span>
                    </td>
                    <td class="val-down{% if network.avg_download == best_download %} best{% endif %}">{{ "%.1f"|format(network.avg_download) }} Mbps</td>
                    <td class="val-up{% if network.avg_upload == best_upload %} best{% endif %}">{{ "%.1f"|format(network.avg_upload) }} Mbps</td>
                    <td class="val-ping{% if network.avg_ping == best_ping %} best{% endif %}">{{ "%.1f"|format(network.avg_ping) }} ms</td>
                    <td class="val-count">{{ network.measurement_count }}</td>
                    <td>{{ network.last_measured }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    {% if networks|length > 1 %}
    <div class="network-picker">
        <div class="network-picker-wrapper">
            <select id="networkSelect" onchange="switchNetwork(this.value)">
                {% for network in networks %}
                <option value="{{ network.id }}">{{ network.name }} ({{ network.type_label }})</option>
                {% endfor %}
            </select>
        </div>
    </div>
    {% endif %}

    {% for network in networks %}
    <div class="network-section{% if loop.first %} active{% endif %}" data-network="{{ network.id }}">
        <div class="network-header">
            <h2>{{ network.name }}</h2>
            <span class="network-badge">{{ network.type_label }}</span>
            <span class="network-badge">{{ network.measurement_count }} measurements</span>
        </div>
        <div class="stats">
            <div class="stat-card download">
                <div class="label">Avg Download</div>
                <div class="value">{{ "%.1f"|format(network.avg_download) }}</div>
                <div class="unit">Mbps</div>
            </div>
            <div class="stat-card upload">
                <div class="label">Avg Upload</div>
                <div class="value">{{ "%.1f"|format(network.avg_upload) }}</div>
                <div class="unit">Mbps</div>
            </div>
            <div class="stat-card ping">
                <div class="label">Avg Ping</div>
                <div class="value">{{ "%.1f"|format(network.avg_ping) }}</div>
                <div class="unit">ms</div>
            </div>
            <div class="stat-card count">
                <div class="label">Last Test</div>
                <div class="value">{{ network.last_measured }}</div>
                <div class="unit"></div>
            </div>
        </div>
        <div class="graphs">
            {% for graph in network.graphs %}
            <div class="graph-card">
                <h3>{{ graph.label }}</h3>
                <img src="{{ graph.filename }}" alt="{{ graph.label }}">
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}

    <script>
    function switchNetwork(id) {
        document.querySelectorAll('.network-section').forEach(function(el) {
            el.classList.toggle('active', el.dataset.network === id);
        });
    }
    </script>
</body>
</html>"""


def sanitize_filename(name: str) -> str:
    """Convert a network name to a safe filename component."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def generate_graph(data: dict, network_name: str, period: Period, output_path: str) -> bool:
    """Render a speed/ping graph and save it as a PNG file."""
    if not data["timestamps"]:
        return False

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.patch.set_facecolor("#1e293b")

    for ax in (ax1, ax2):
        ax.set_facecolor("#0f172a")
        ax.tick_params(colors="#94a3b8")
        ax.spines["bottom"].set_color("#334155")
        ax.spines["left"].set_color("#334155")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.15, color="#64748b")

    use_markers = len(data["timestamps"]) < 50
    marker = "." if use_markers else None

    ax1.plot(
        data["timestamps"],
        data["downloads"],
        color="#22c55e",
        linewidth=1.5,
        label="Download",
        marker=marker,
        markersize=4,
    )
    ax1.plot(
        data["timestamps"], data["uploads"], color="#3b82f6", linewidth=1.5, label="Upload", marker=marker, markersize=4
    )
    ax1.fill_between(data["timestamps"], data["downloads"], alpha=0.1, color="#22c55e")
    ax1.fill_between(data["timestamps"], data["uploads"], alpha=0.1, color="#3b82f6")
    ax1.set_ylabel("Mbps", color="#94a3b8")
    ax1.legend(loc="upper left", facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")

    ax2.plot(
        data["timestamps"], data["pings"], color="#f59e0b", linewidth=1.5, label="Ping", marker=marker, markersize=4
    )
    ax2.fill_between(data["timestamps"], data["pings"], alpha=0.1, color="#f59e0b")
    ax2.set_ylabel("ms", color="#94a3b8")
    ax2.legend(loc="upper left", facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")

    if period["hours"] <= 24:
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    elif period["hours"] <= 168:
        ax2.xaxis.set_major_locator(mdates.DayLocator())
        ax2.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%a %d/%m"))
    else:
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))

    fig.autofmt_xdate(rotation=30, ha="right")
    ax2.tick_params(axis="x", colors="#94a3b8")

    plt.tight_layout()
    plt.savefig(output_path, dpi=GRAPH_DPI, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return True


def generate_dashboard() -> None:
    """Build the full HTML dashboard with graphs for every network."""
    os.makedirs(str(OUTPUT_DIR), exist_ok=True)

    if not DB_PATH.exists():
        print("No database found. Run a measurement first.")
        return

    with connect() as conn:
        networks = get_networks(conn)

        if not networks:
            print("No measurements found.")
            return

        template_data = []

        for network_name in networks:
            stats = get_network_stats(conn, network_name)
            safe_name = sanitize_filename(network_name)
            graphs = []

            for period in PERIODS:
                data = fetch_data(conn, network_name, period["hours"], period["aggregate"])
                filename = f"speed_{safe_name}_{period['name']}.png"
                output_path = os.path.join(str(OUTPUT_DIR), filename)

                if generate_graph(data, network_name, period, output_path):
                    graphs.append({"label": period["label"], "filename": filename})

            template_data.append(
                {
                    "id": safe_name,
                    "name": network_name,
                    "type": stats["type"],
                    "type_label": NETWORK_TYPE_LABELS.get(stats["type"], stats["type"]),
                    "avg_download": stats["avg_download"],
                    "avg_upload": stats["avg_upload"],
                    "avg_ping": stats["avg_ping"],
                    "measurement_count": stats["measurement_count"],
                    "last_measured": stats["last_measured"],
                    "graphs": graphs,
                }
            )

    best_download = max((n["avg_download"] for n in template_data), default=0)
    best_upload = max((n["avg_upload"] for n in template_data), default=0)
    best_ping = min((n["avg_ping"] for n in template_data if n["avg_ping"] > 0), default=0)

    template = Template(HTML_TEMPLATE)
    html = template.render(
        networks=template_data,
        best_download=best_download,
        best_upload=best_upload,
        best_ping=best_ping,
        updated=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    html_path = os.path.join(str(OUTPUT_DIR), "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {html_path}")
    print(f"Networks: {', '.join(networks)}")
