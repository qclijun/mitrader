"""
E2E tests for mitrader application.

These tests verify the UI behavior after the type mismatch fix.
Run manually or via Playwright MCP tools.
"""
import pytest


@pytest.mark.e2e
class TestMitraderUI:
    """Tests for mitrader UI behavior."""

    def test_app_loads(self, streamlit_server):
        """Verify the app page loads without errors."""
        # This test is a placeholder for manual verification
        # Use Playwright MCP tools:
        # 1. mcp_playwright_browser_navigate(url=streamlit_server)
        # 2. mcp_playwright_browser_snapshot() to verify page
        # 3. Check that title contains "mitrader" or "交易"
        pytest.skip("Manual E2E test - use Playwright MCP tools")

    def test_load_data_no_console_error(self, streamlit_server):
        """Verify loading data produces no JavaScript console errors."""
        # This test is a placeholder for manual verification
        # Use Playwright MCP tools:
        # 1. Navigate to streamlit_server
        # 2. Fill inputs: sample_data/trade.csv, sample_data/prices.parquet
        # 3. Click "加载数据" button
        # 4. Wait for "数据加载成功"
        # 5. Check console messages for errors (mcp_playwright_browser_console_messages)
        # 6. Verify no "undefined" or "trade_date" errors
        pytest.skip("Manual E2E test - use Playwright MCP tools")

    def test_select_asset_shows_chart(self, streamlit_server):
        """Verify selecting an asset displays the K-line chart."""
        # This test is a placeholder for manual verification
        # Use Playwright MCP tools:
        # 1. Navigate and load data (as above)
        # 2. Select asset from dropdown
        # 3. Wait for "K线图" to appear
        # 4. Verify chart is rendered
        pytest.skip("Manual E2E test - use Playwright MCP tools")