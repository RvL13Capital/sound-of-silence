"""Tests for universe helpers and data filename conversion."""
import pytest

from dach_momentum.universe import _clean_ticker
from dach_momentum.data import _ticker_to_filename, _filename_to_ticker


# ========================================================================== #
# _clean_ticker()
# ========================================================================== #

class TestCleanTicker:
    def test_removes_exchange_suffix_pa(self):
        assert _clean_ticker("AIR.PA") == "AIR"

    def test_removes_exchange_suffix_de(self):
        assert _clean_ticker("SAP.DE") == "SAP"

    def test_removes_wikipedia_annotation(self):
        assert _clean_ticker("[1]SAP") == "SAP"

    def test_none_input(self):
        assert _clean_ticker(None) is None

    def test_nan_input(self):
        assert _clean_ticker(float("nan")) is None

    def test_strips_whitespace(self):
        assert _clean_ticker("  BMW.DE  ") == "BMW"

    def test_uppercase(self):
        assert _clean_ticker("bmw.de") == "BMW"

    def test_keeps_dash(self):
        # Tickers like "AB-C" should keep the dash
        assert _clean_ticker("AB-C.DE") == "AB-C"

    def test_removes_complex_annotation(self):
        assert _clean_ticker("[note 1]SAP.DE") == "SAP"

    def test_empty_string(self):
        assert _clean_ticker("") is None

    def test_suffix_vi(self):
        assert _clean_ticker("VOE.VI") == "VOE"

    def test_suffix_sw(self):
        assert _clean_ticker("NESN.SW") == "NESN"


# ========================================================================== #
# _ticker_to_filename() and _filename_to_ticker() round-trip
# ========================================================================== #

class TestTickerFilenameConversion:
    @pytest.mark.parametrize("ticker", [
        "SAP.DE", "VOE.VI", "NESN.SW", "AIR.PA",
        "ASML.AS", "UCB.BR", "ENI.MI", "SAN.MC",
        "VOLV-B.ST", "NOVO-B.CO", "NOKIA.HE",
        "TEL.OL", "EDP.LS", "CDR.WA", "AZN.L", "OPAP.AT",
    ])
    def test_round_trip(self, ticker):
        filename = _ticker_to_filename(ticker)
        recovered = _filename_to_ticker(filename)
        assert recovered == ticker

    def test_ticker_to_filename_replaces_dots(self):
        assert _ticker_to_filename("SAP.DE") == "SAP_DE"

    def test_ticker_to_filename_replaces_slashes(self):
        assert _ticker_to_filename("A/B.DE") == "A_B_DE"

    def test_filename_no_suffix(self):
        # A stem without a known suffix should be returned unchanged
        assert _filename_to_ticker("UNKNOWN") == "UNKNOWN"
