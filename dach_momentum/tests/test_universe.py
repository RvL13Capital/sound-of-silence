"""Tests for universe helpers and data filename conversion."""
import pytest

from dach_momentum.universe import _clean_ticker
from dach_momentum.data import _ticker_to_filename, _filename_to_ticker


# ========================================================================== #
# _clean_ticker()
# ========================================================================== #


class TestCleanTicker:
    def test_strips_exchange_suffix(self):
        assert _clean_ticker("AIR.PA") == "AIR"
        assert _clean_ticker("SAP.DE") == "SAP"

    def test_removes_wiki_annotations(self):
        assert _clean_ticker("[1]SAP") == "SAP"
        assert _clean_ticker("SAP[note]") == "SAP"

    def test_none_input(self):
        assert _clean_ticker(None) is None

    def test_nan_input(self):
        import math
        assert _clean_ticker(float("nan")) is None

    def test_preserves_alphanumeric_and_dash(self):
        assert _clean_ticker("AB-C.DE") == "AB-C"

    def test_uppercase_conversion(self):
        assert _clean_ticker("sap.de") == "SAP"


# ========================================================================== #
# _ticker_to_filename() / _filename_to_ticker()  round-trip
# ========================================================================== #


class TestTickerFilenameRoundTrip:
    @pytest.mark.parametrize(
        "ticker",
        [
            "SAP.DE",
            "AIR.PA",
            "NOVN.SW",
            "ISP.MI",
            "VOLV-B.ST",
            "UCG.MI",
            "ADS.DE",
        ],
    )
    def test_round_trip(self, ticker):
        filename = _ticker_to_filename(ticker)
        recovered = _filename_to_ticker(filename)
        assert recovered == ticker

    def test_to_filename_replaces_dots_and_slashes(self):
        assert _ticker_to_filename("SAP.DE") == "SAP_DE"
        assert _ticker_to_filename("A/B.DE") == "A_B_DE"

    def test_plain_ticker_unchanged(self):
        """A ticker with no suffix round-trips as itself."""
        assert _filename_to_ticker("AAPL") == "AAPL"
