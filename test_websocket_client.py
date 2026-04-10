#!/usr/bin/env python3
"""
WebSocket Alert Test Client

This script connects to the SecuWatch 2.0 WebSocket alert endpoint 
and displays received alerts in real-time.

Usage:
    python test_websocket_client.py [--url ws://localhost:8000/ws/alerts]

Requirements:
    pip install websockets
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional

import websockets


class WebSocketAlertClient:
    """Simple WebSocket client for testing the alert system."""

    def __init__(self, url: str = "ws://localhost:8000/ws/alerts"):
        self.url = url
        self.connected = False
        self.alert_count = 0

    async def connect(self) -> None:
        """Connect to the WebSocket alert endpoint."""
        try:
            async with websockets.connect(self.url) as websocket:
                self.connected = True
                self.print_banner("✓ Connected to alert stream")
                await self.listen(websocket)
        except ConnectionRefusedError:
            self.print_error("✗ Connection refused. Is the server running?")
            sys.exit(1)
        except websockets.exceptions.WebSocketException as e:
            self.print_error(f"✗ WebSocket error: {e}")
            sys.exit(1)

    async def listen(self, websocket) -> None:
        """Listen for incoming alerts."""
        try:
            while True:
                message = await websocket.recv()
                self.handle_alert(message)
        except websockets.exceptions.ConnectionClosed:
            self.print_warning("⚠ Connection closed by server")

    def handle_alert(self, message: str) -> None:
        """Process and display an alert."""
        try:
            alert = json.loads(message)
            self.alert_count += 1
            self.display_alert(alert)
        except json.JSONDecodeError:
            self.print_error(f"✗ Invalid JSON received: {message}")

    def display_alert(self, alert: dict) -> None:
        """Display alert in a formatted way."""
        print("\n" + "=" * 70)
        print(f"[ALERT #{self.alert_count}] {alert.get('type', 'Unknown').upper()}")
        print("=" * 70)
        
        severity = alert.get("severity", "UNKNOWN")
        severity_color = self.get_severity_color(severity)
        
        print(f"  Severity  : {severity_color}{severity}\033[0m")
        print(f"  Alert ID  : {alert.get('id', 'N/A')}")
        print(f"  Device ID : {alert.get('device_id', 'N/A')}")
        print(f"  Type      : {alert.get('type', 'N/A')}")
        print(f"  Created   : {alert.get('created_at', 'N/A')}")
        print(f"\n  Description:")
        description = alert.get("description", "N/A")
        for line in description.split('\n'):
            print(f"    {line}")
        
        print("=" * 70)

    @staticmethod
    def get_severity_color(severity: str) -> str:
        """Get ANSI color code for severity level."""
        colors = {
            "HIGH": "\033[91m",      # Red
            "MEDIUM": "\033[93m",    # Yellow
            "LOW": "\033[92m",       # Green
        }
        return colors.get(severity, "\033[0m")  # Default: no color

    @staticmethod
    def print_banner(message: str) -> None:
        """Print a formatted banner message."""
        print(f"\n{message}")

    @staticmethod
    def print_warning(message: str) -> None:
        """Print a warning message."""
        print(f"\033[93m{message}\033[0m")  # Yellow

    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message."""
        print(f"\033[91m{message}\033[0m")  # Red

    def get_stats(self) -> str:
        """Get client statistics."""
        return f"Alerts received: {self.alert_count}"


async def main():
    """Main entry point."""
    url = "ws://localhost:8000/ws/alerts"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    client = WebSocketAlertClient(url)
    
    print("\n" + "=" * 70)
    print("SecuWatch 2.0 - WebSocket Alert Client")
    print("=" * 70)
    print(f"Connecting to: {url}")
    print("\nWaiting for alerts... (Press Ctrl+C to exit)")
    print("=" * 70)
    
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n\nClient stopped by user")
        print(f"Session stats: {client.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
