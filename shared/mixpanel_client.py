"""
MixPanel API Client for fetching analytics data
"""
import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import base64


class MixPanelClient:
    """Client for interacting with MixPanel Query and Export APIs"""
    
    def __init__(self):
        self.username = os.environ.get("MIXPANEL_USERNAME")
        self.secret = os.environ.get("MIXPANEL_SECRET")
        self.project_id = os.environ.get("MIXPANEL_PROJECT_ID")
        region = os.environ.get("MIXPANEL_REGION", "us")  # Default to US, use 'eu' for EU residency
        
        # API Base URLs based on data residency
        if region.lower() == "eu":
            self.query_base_url = "https://eu.mixpanel.com/api/query"
            self.export_base_url = "https://data-eu.mixpanel.com/api/2.0"
        elif region.lower() == "in":
            self.query_base_url = "https://in.mixpanel.com/api/query"
            self.export_base_url = "https://data-in.mixpanel.com/api/2.0"
        else:
            self.query_base_url = "https://mixpanel.com/api/query"
            self.export_base_url = "https://data.mixpanel.com/api/2.0"
        
        if not self.username or not self.secret:
            raise ValueError("MixPanel credentials not configured. Set MIXPANEL_USERNAME and MIXPANEL_SECRET")
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Generate Basic Auth header for API requests"""
        credentials = f"{self.username}:{self.secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json"
        }
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict:
        """Make authenticated request to MixPanel API"""
        try:
            response = requests.get(
                url,
                headers=self._get_auth_header(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"MixPanel API Error: {e}")
            return {"error": str(e)}
    
    def get_segmentation_data(
        self,
        event: str,
        from_date: str,
        to_date: str,
        segment_on: Optional[str] = None,
        unit: str = "day",
        type_: str = "general"
    ) -> Dict:
        """
        Query segmentation data for an event
        
        Args:
            event: Event name to query
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            segment_on: Property to segment by (optional)
            unit: Time bucket - minute, hour, day, month
            type_: Query type - general, unique, average
        """
        params = {
            "project_id": self.project_id,
            "event": event,
            "from_date": from_date,
            "to_date": to_date,
            "unit": unit,
            "type": type_
        }
        
        if segment_on:
            params["on"] = segment_on
            
        return self._make_request(f"{self.query_base_url}/segmentation", params)
    
    def get_event_counts(
        self,
        events: List[str],
        from_date: str,
        to_date: str,
        unit: str = "day"
    ) -> Dict[str, Any]:
        """Get counts for multiple events"""
        results = {}
        for event in events:
            data = self.get_segmentation_data(
                event=event,
                from_date=from_date,
                to_date=to_date,
                unit=unit,
                type_="general"
            )
            results[event] = data
        return results
    
    def get_unique_users(
        self,
        event: str,
        from_date: str,
        to_date: str
    ) -> Dict:
        """Get unique user count for an event"""
        return self.get_segmentation_data(
            event=event,
            from_date=from_date,
            to_date=to_date,
            type_="unique"
        )
    
    def export_raw_events(
        self,
        from_date: str,
        to_date: str,
        event: Optional[str] = None,
        limit: int = 10000
    ) -> List[Dict]:
        """
        Export raw event data
        
        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            event: Specific event to filter (optional)
            limit: Max events to return
        """
        params = {
            "project_id": self.project_id,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit
        }
        
        if event:
            params["event"] = f'["{event}"]'
        
        try:
            response = requests.get(
                f"{self.export_base_url}/export",
                headers=self._get_auth_header(),
                params=params,
                timeout=60
            )
            response.raise_for_status()
            
            # Response is JSONL (one JSON object per line)
            events = []
            for line in response.text.strip().split('\n'):
                if line:
                    import json
                    events.append(json.loads(line))
            return events
            
        except requests.exceptions.RequestException as e:
            print(f"Export API Error: {e}")
            return []
    
    def get_top_events(self, from_date: str, to_date: str, limit: int = 10) -> List[Dict]:
        """Get top events by count (requires raw export and aggregation)"""
        events = self.export_raw_events(from_date, to_date, limit=100000)
        
        # Count events
        event_counts = {}
        for event in events:
            event_name = event.get("event", "unknown")
            event_counts[event_name] = event_counts.get(event_name, 0) + 1
        
        # Sort and return top N
        sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"event": name, "count": count} for name, count in sorted_events[:limit]]


def get_date_range(period: str = "daily") -> tuple:
    """
    Get date range based on period
    
    Args:
        period: daily, weekly, biweekly, monthly
    
    Returns:
        tuple: (from_date, to_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    to_date = today.strftime("%Y-%m-%d")
    
    if period == "daily":
        from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif period == "weekly":
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "biweekly":
        from_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    elif period == "monthly":
        from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    return from_date, to_date
