"""
E2E tests for mitrader application (6 tests).

Requires: playwright installed (`uv add playwright && uv run playwright install chromium`)
Auto-skips gracefully when playwright is not available.
"""
import re
from pathlib import Path

import pytest

try:
    import playwright  # noqa: F401
except ImportError:
    pytest.skip('playwright not installed', allow_module_level=True)

TRADE_PATH = str(Path(__file__).parent.parent.parent / 'sample_data' / 'trade.csv')
PRICES_PATH = str(Path(__file__).parent.parent.parent / 'sample_data' / 'prices.parquet')
PNL_PATH = str(Path(__file__).parent.parent.parent / 'sample_data' / 'pnl.csv')


def _load_data(page):
    """Fill file paths and click '加载数据', wait for success alert AND chart render."""
    inputs = page.locator('[data-testid="stTextInput"] input').all()
    inputs[0].fill(TRADE_PATH)
    inputs[1].fill(PRICES_PATH)
    page.get_by_role('button', name='加载数据').click()
    # Success alert: data-testid="stAlertContentSuccess"
    page.wait_for_selector('[data-testid="stAlertContentSuccess"]', timeout=20_000)
    # Streamlit rerenders once more to select the first asset and render the chart
    page.wait_for_selector('[data-testid="stPlotlyChart"]', timeout=15_000)


@pytest.mark.e2e
class TestMitraderUI:

    def test_e2e_load_data_success(self, browser_page):
        """Valid file paths → '数据加载成功' alert + asset count appear."""
        _load_data(browser_page)

        alert = browser_page.locator('[data-testid="stAlertContentSuccess"]')
        assert alert.is_visible()
        assert '数据加载成功' in alert.inner_text()
        assert '个资产' in alert.inner_text()

    def test_e2e_load_data_invalid_path(self, browser_page):
        """Invalid trade path → error alert with FileNotFoundError message."""
        inputs = browser_page.locator('[data-testid="stTextInput"] input').all()
        inputs[0].fill('/nonexistent/trade.csv')
        inputs[1].fill(PRICES_PATH)
        browser_page.get_by_role('button', name='加载数据').click()

        browser_page.wait_for_selector('[data-testid="stAlertContentError"]', timeout=10_000)
        error = browser_page.locator('[data-testid="stAlertContentError"]')
        assert error.is_visible()
        assert 'not found' in error.inner_text().lower()

    def test_e2e_search_and_select_asset(self, browser_page):
        """Load → type in search → asset list narrows → chart remains visible."""
        _load_data(browser_page)

        # After load the first asset is auto-selected and chart is rendered
        assert browser_page.locator('[data-testid="stPlotlyChart"]').is_visible()

        # Type partial ID in search box (placeholder='输入资产ID或名称')
        search = browser_page.locator('input[placeholder="输入资产ID或名称"]')
        assert search.is_visible()
        selected_caption = browser_page.get_by_text(re.compile('当前选中：')).inner_text()
        first_id = selected_caption.split('当前选中：', 1)[1].strip()
        partial = first_id[:3] if len(first_id) >= 3 else first_id

        search.fill(partial)
        browser_page.wait_for_timeout(1_000)  # wait for Streamlit to re-render

        # Asset table and chart should still be present
        assert browser_page.locator('[data-testid="stDataFrame"]').first.is_visible()
        assert browser_page.locator('[data-testid="stPlotlyChart"]').is_visible()

    def test_e2e_chart_render_with_markers(self, browser_page):
        """After load the chart contains K-line and trade markers."""
        _load_data(browser_page)

        chart = browser_page.locator('[data-testid="stPlotlyChart"]')
        assert chart.is_visible()

        # Verify Plotly rendered an actual SVG/canvas inside the chart
        chart_inner = chart.locator('.js-plotly-plot, svg')
        assert chart_inner.count() > 0

        # Page should mention at least one of the trace legend names
        page_text = browser_page.inner_text('body')
        assert '买入点' in page_text or '卖出点' in page_text or 'K线' in page_text

    def test_e2e_trade_details_expander(self, browser_page):
        """Expand '交易详情' → trade table rows appear."""
        _load_data(browser_page)

        # Expander is collapsed by default; click to expand
        expander = browser_page.locator('[data-testid="stExpander"]').first
        assert expander.is_visible()
        expander.click()

        # Trade data table appears inside expander details
        details = browser_page.locator('[data-testid="stExpanderDetails"]').first
        assert details.is_visible()

        # At least one dataframe (trade detail table) must be inside
        inner_df = details.locator('[data-testid="stDataFrame"]')
        assert inner_df.count() > 0

    def test_e2e_date_range_filter(self, browser_page):
        """Change start/end date → chart x-axis re-renders."""
        _load_data(browser_page)

        # Chart visible before filter
        assert browser_page.locator('[data-testid="stPlotlyChart"]').is_visible()

        # Date inputs appear after an asset is auto-selected (Streamlit renders them with YYYY/MM/DD placeholder)
        date_inputs = browser_page.locator('input[placeholder="YYYY/MM/DD"]')
        assert date_inputs.count() >= 2

        # Change start date to a later date to narrow the range
        start_input = date_inputs.nth(0)
        start_input.click(click_count=3)  # select all text
        start_input.type('2025/01/01')
        start_input.press('Enter')
        browser_page.wait_for_timeout(2_000)

        # Chart must still be rendered after date change
        assert browser_page.locator('[data-testid="stPlotlyChart"]').is_visible()


@pytest.mark.e2e
class TestStrategyRiskReturnUI:

    def test_e2e_strategy_page_loads_pnl_and_renders_outputs(self, browser_page):
        """New multipage page loads pnl.csv and renders chart plus tables."""
        browser_page.get_by_role('link', name=re.compile('strategy.*risk.*return', re.I)).click()
        browser_page.wait_for_selector('text=策略风险收益评估及对比', timeout=10_000)

        inputs = browser_page.locator('[data-testid="stTextInput"] input').all()
        inputs[0].fill(PNL_PATH)
        browser_page.get_by_role('button', name='加载收益数据').click()

        browser_page.wait_for_selector('[data-testid="stAlertContentSuccess"]', timeout=20_000)
        assert '数据加载成功' in browser_page.locator('[data-testid="stAlertContentSuccess"]').inner_text()

        browser_page.wait_for_selector('[data-testid="stPlotlyChart"]', timeout=20_000)
        assert browser_page.locator('[data-testid="stPlotlyChart"]').is_visible()
        browser_page.wait_for_selector('[data-testid="stTable"]', timeout=20_000)
        assert browser_page.locator('[data-testid="stTable"]').count() >= 2

        page_text = browser_page.inner_text('body')
        assert '最近收益情况' in page_text
        assert '风险收益评估' in page_text
        assert '最新累计净值' in page_text
        assert '年化收益率' in page_text
