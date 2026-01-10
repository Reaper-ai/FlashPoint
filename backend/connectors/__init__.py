"""Connectors Module: Data Source Implementations

This package contains Pathway-compatible connector implementations for various data sources:

- news_src.py: GNews API polling connector
- reddit_src.py: Reddit public API polling connector
- telegram_src.py: Telegram real-time streaming connector
- rss_src.py: RSS feed polling connector (multiple sources)
- sim_src.py: Simulation/test data connector (JSONL file)

All connectors inherit from pw.io.python.ConnectorSubject and emit events in InputSchema format.
Each connector can operate in polling mode (scheduled) or streaming mode (event-driven).
"""

pass