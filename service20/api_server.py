"""Simple API server to serve dashboard data from database."""

import asyncio
import asyncpg
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from dotenv import load_dotenv
load_dotenv()


class DashboardAPIHandler(BaseHTTPRequestHandler):
    """Handle API requests for dashboard data."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if parsed_path.path == '/api/alerts':
            # Fetch alerts from database
            data = asyncio.run(self.fetch_alerts())
            self.wfile.write(json.dumps(data).encode())
        elif parsed_path.path == '/api/matches':
            # Fetch matches from database
            data = asyncio.run(self.fetch_matches())
            self.wfile.write(json.dumps(data).encode())
        elif parsed_path.path == '/api/history/investment':
            # Fetch investment research history
            data = asyncio.run(self.fetch_investment_history())
            self.wfile.write(json.dumps(data).encode())
        elif parsed_path.path == '/api/history/funding':
            # Fetch funding research history
            data = asyncio.run(self.fetch_funding_history())
            self.wfile.write(json.dumps(data).encode())
        else:
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    async def fetch_alerts(self):
        """Fetch alerts from database."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {'error': 'DATABASE_URL not set'}

        try:
            conn = await asyncpg.connect(database_url)

            query = """
                SELECT
                    id,
                    research_id,
                    alert_type,
                    criteria,
                    created_at,
                    status
                FROM service20_alerts
                ORDER BY created_at DESC
                LIMIT 100;
            """

            rows = await conn.fetch(query)
            await conn.close()

            alerts = []
            for row in rows:
                # Parse criteria - asyncpg returns JSONB as dict already, but sometimes as string
                criteria = row['criteria']
                if isinstance(criteria, str):
                    import json
                    criteria = json.loads(criteria)
                if not criteria:
                    criteria = {}

                # Extract data from criteria JSONB
                basic_info = criteria.get('basic_info', {})
                location_info = criteria.get('location', {})
                sector_info = criteria.get('sector', {})
                financial_info = criteria.get('financial', {})
                timeline_info = criteria.get('timeline', {})

                alert = {
                    'id': row['research_id'],
                    'type': row['alert_type'],
                    'location': f"{location_info.get('city', 'Unknown')}, {location_info.get('country', '')}".strip(', '),
                    'sector': sector_info.get('primary', 'unknown').replace('_', ' '),
                    'status': 'completed',
                    'started': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else 'N/A',
                    'duration': 'N/A',
                    'alertCreated': True
                }
                alerts.append(alert)

            return {'success': True, 'alerts': alerts, 'count': len(alerts)}

        except Exception as e:
            return {'error': str(e)}

    async def fetch_matches(self):
        """Fetch matches from database."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {'error': 'DATABASE_URL not set'}

        try:
            conn = await asyncpg.connect(database_url)

            query = """
                SELECT
                    match_id,
                    match_type,
                    compatibility_score,
                    confidence_level,
                    bundle_metrics,
                    created_at,
                    status,
                    opportunities_data,
                    funders_data
                FROM opportunity_matches
                ORDER BY created_at DESC
                LIMIT 100;
            """

            rows = await conn.fetch(query)
            await conn.close()

            matches = []
            for row in rows:
                # Parse JSONB fields
                bundle_metrics = row['bundle_metrics']
                if isinstance(bundle_metrics, str):
                    import json
                    bundle_metrics = json.loads(bundle_metrics)
                if not bundle_metrics:
                    bundle_metrics = {}

                opportunities = row['opportunities_data']
                if isinstance(opportunities, str):
                    import json
                    opportunities = json.loads(opportunities)
                if not opportunities:
                    opportunities = []

                funders = row['funders_data']
                if isinstance(funders, str):
                    import json
                    funders = json.loads(funders)
                if not funders:
                    funders = []

                match = {
                    'id': row['match_id'],
                    'date': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else 'N/A',
                    'matchesFound': len(opportunities),
                    'highConfidence': 1 if row['confidence_level'] == 'high' else 0,
                    'mediumConfidence': 1 if row['confidence_level'] == 'medium' else 0,
                    'bundled': 1 if row['match_type'] == 'bundled' else 0,
                    'duration': 'N/A',
                    'status': row['status'] or 'proposed'
                }
                matches.append(match)

            return {'success': True, 'matches': matches, 'count': len(matches)}

        except Exception as e:
            return {'error': str(e)}

    async def fetch_investment_history(self):
        """Fetch investment research history from database."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {'error': 'DATABASE_URL not set'}

        try:
            conn = await asyncpg.connect(database_url)

            query = """
                SELECT
                    id,
                    query,
                    research_brief,
                    final_report,
                    research_iterations,
                    tool_calls_count,
                    created_at,
                    updated_at,
                    metadata,
                    langfuse_trace_id
                FROM service20_investment_opportunities
                ORDER BY created_at DESC;
            """

            rows = await conn.fetch(query)
            await conn.close()

            history = []
            for row in rows:
                # Parse metadata
                metadata = row['metadata']
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)
                if not metadata:
                    metadata = {}

                # Extract city from query (simple extraction)
                query_text = row['query'] or ''
                city = 'Unknown'
                if ' in ' in query_text:
                    parts = query_text.split(' in ')
                    if len(parts) > 1:
                        city_part = parts[1].split('.')[0].split(',')[0].strip()
                        city = city_part

                # Extract sector from query
                sector = 'renewable_energy'
                if 'solar' in query_text.lower():
                    sector = 'solar_energy'
                elif 'wind' in query_text.lower():
                    sector = 'wind_energy'
                elif 'energy storage' in query_text.lower():
                    sector = 'energy_storage'

                item = {
                    'id': f'inv-{row["id"]}',
                    'type': 'investment',
                    'location': city,
                    'sector': sector,
                    'status': 'completed',
                    'started': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else 'N/A',
                    'duration': 'N/A',
                    'alertCreated': bool(row['final_report']),
                    'iterations': row['research_iterations'] or 0,
                    'tool_calls': row['tool_calls_count'] or 0,
                    'report_length': len(row['final_report']) if row['final_report'] else 0,
                    'trace_id': row['langfuse_trace_id']
                }
                history.append(item)

            return {'success': True, 'history': history, 'count': len(history)}

        except Exception as e:
            return {'error': str(e)}

    async def fetch_funding_history(self):
        """Fetch funding research history from database."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {'error': 'DATABASE_URL not set'}

        try:
            conn = await asyncpg.connect(database_url)

            query = """
                SELECT
                    id,
                    query,
                    research_brief,
                    final_report,
                    research_iterations,
                    tool_calls_count,
                    created_at,
                    updated_at,
                    metadata,
                    langfuse_trace_id
                FROM service20_funding_opportunities
                ORDER BY created_at DESC;
            """

            rows = await conn.fetch(query)
            await conn.close()

            history = []
            for row in rows:
                # Parse metadata
                metadata = row['metadata']
                if isinstance(metadata, str):
                    import json
                    metadata = json.loads(metadata)
                if not metadata:
                    metadata = {}

                # Extract organization from query
                query_text = row['query'] or ''
                organization = 'Unknown'
                if ' from ' in query_text:
                    parts = query_text.split(' from ')
                    if len(parts) > 1:
                        org_part = parts[1].split('.')[0].strip()
                        organization = org_part

                # Extract sector from query
                sector = 'renewable_energy'
                if 'solar' in query_text.lower():
                    sector = 'solar_energy'
                elif 'wind' in query_text.lower():
                    sector = 'wind_energy'

                item = {
                    'id': f'fund-{row["id"]}',
                    'type': 'funding',
                    'location': organization,
                    'sector': sector,
                    'status': 'completed',
                    'started': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else 'N/A',
                    'duration': 'N/A',
                    'alertCreated': bool(row['final_report']),
                    'iterations': row['research_iterations'] or 0,
                    'tool_calls': row['tool_calls_count'] or 0,
                    'report_length': len(row['final_report']) if row['final_report'] else 0,
                    'trace_id': row['langfuse_trace_id']
                }
                history.append(item)

            return {'success': True, 'history': history, 'count': len(history)}

        except Exception as e:
            return {'error': str(e)}

    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass


def run_server(port=8898):
    """Run the API server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardAPIHandler)
    print(f"Dashboard API server running on http://localhost:{port}")
    print(f"Endpoints:")
    print(f"  - http://localhost:{port}/api/alerts")
    print(f"  - http://localhost:{port}/api/matches")
    print(f"  - http://localhost:{port}/api/history/investment")
    print(f"  - http://localhost:{port}/api/history/funding")
    print("\nPress Ctrl+C to stop...")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
