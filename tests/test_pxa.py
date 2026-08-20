import pytest
from unittest.mock import MagicMock, patch, call
from instrumation.drivers.keysight import KeysightPXA
from instrumation.results import MeasurementResult


@pytest.fixture
def mock_pxa():
    with patch('pyvisa.ResourceManager'):
        driver = KeysightPXA("TCPIP::1.2.3.4::INSTR")
        driver.inst = MagicMock()
        driver.inst.query.return_value = "1"
        yield driver


# ── Measurement Configuration ────────────────────────────────────────────────


class TestSweepType:
    def test_set_sweep_type_imm(self, mock_pxa):
        mock_pxa.set_sweep_type("IMM")
        mock_pxa.inst.write.assert_any_call(":SENS:SWE:TYPE IMM")

    def test_set_sweep_type_auto(self, mock_pxa):
        mock_pxa.set_sweep_type("AUTO")
        mock_pxa.inst.write.assert_any_call(":SENS:SWE:TYPE AUTO")

    def test_set_sweep_type_sweep(self, mock_pxa):
        mock_pxa.set_sweep_type("SWE")
        mock_pxa.inst.write.assert_any_call(":SENS:SWE:TYPE SWE")

    def test_set_sweep_type_fft(self, mock_pxa):
        mock_pxa.set_sweep_type("FFT")
        mock_pxa.inst.write.assert_any_call(":SENS:SWE:TYPE FFT")

    def test_set_sweep_type_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Invalid sweep type"):
            mock_pxa.set_sweep_type("INVALID")


class TestDetector:
    @pytest.mark.parametrize("func", ["AVER", "POS", "NEG", "SAMP", "RMS", "QPEAK"])
    def test_set_detector_valid(self, mock_pxa, func):
        mock_pxa.set_detector(func)
        mock_pxa.inst.write.assert_any_call(f":SENS:AVER:FUNC {func}")

    def test_set_detector_case_insensitive(self, mock_pxa):
        mock_pxa.set_detector("aver")
        mock_pxa.inst.write.assert_any_call(":SENS:AVER:FUNC aver")

    def test_set_detector_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Invalid detector function"):
            mock_pxa.set_detector("INVALID")


class TestAverageCount:
    def test_set_average_count(self, mock_pxa):
        mock_pxa.set_average_count(100)
        mock_pxa.inst.write.assert_any_call(":SENS:AVER:COUN 100")

    def test_set_average_count_minimum(self, mock_pxa):
        mock_pxa.set_average_count(1)
        mock_pxa.inst.write.assert_any_call(":SENS:AVER:COUN 1")

    def test_set_average_count_zero_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Average count must be >= 1"):
            mock_pxa.set_average_count(0)

    def test_set_average_count_negative_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Average count must be >= 1"):
            mock_pxa.set_average_count(-5)


class TestVideoAverage:
    def test_set_video_average_enable(self, mock_pxa):
        mock_pxa.set_video_average(True)
        mock_pxa.inst.write.assert_any_call(":SENS:BAND:VID:AUTO ON")

    def test_set_video_average_disable(self, mock_pxa):
        mock_pxa.set_video_average(False)
        mock_pxa.inst.write.assert_any_call(":SENS:BAND:VID:AUTO OFF")


class TestFrequencyCorrection:
    def test_set_frequency_correction_enable(self, mock_pxa):
        mock_pxa.set_frequency_correction(True)
        mock_pxa.inst.write.assert_any_call(":SENS:FREQ:CORR:STAT ON")

    def test_set_frequency_correction_disable(self, mock_pxa):
        mock_pxa.set_frequency_correction(False)
        mock_pxa.inst.write.assert_any_call(":SENS:FREQ:CORR:STAT OFF")


class TestInputCoupling:
    def test_set_input_coupling_dc(self, mock_pxa):
        mock_pxa.set_input_coupling("DC")
        mock_pxa.inst.write.assert_any_call(":INP:COUP DC")

    def test_set_input_coupling_ac(self, mock_pxa):
        mock_pxa.set_input_coupling("AC")
        mock_pxa.inst.write.assert_any_call(":INP:COUP AC")

    def test_set_input_coupling_case_insensitive(self, mock_pxa):
        mock_pxa.set_input_coupling("dc")
        mock_pxa.inst.write.assert_any_call(":INP:COUP DC")

    def test_set_input_coupling_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Invalid coupling"):
            mock_pxa.set_input_coupling("RF")


class TestInputImpedance:
    def test_set_input_impedance_50(self, mock_pxa):
        mock_pxa.set_input_impedance(50)
        mock_pxa.inst.write.assert_any_call(":INP:IMP 50")

    def test_set_input_impedance_75(self, mock_pxa):
        mock_pxa.set_input_impedance(75)
        mock_pxa.inst.write.assert_any_call(":INP:IMP 75")

    def test_set_input_impedance_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Invalid impedance"):
            mock_pxa.set_input_impedance(100)


# ── Advanced Triggering ──────────────────────────────────────────────────────


class TestTriggerSource:
    @pytest.mark.parametrize("source", ["IMM", "EXT", "VID", "IFP", "TIME"])
    def test_set_trigger_source_valid(self, mock_pxa, source):
        mock_pxa.set_trigger_source(source)
        mock_pxa.inst.write.assert_any_call(f":TRIG:SOUR {source}")

    def test_set_trigger_source_case_insensitive(self, mock_pxa):
        mock_pxa.set_trigger_source("imm")
        mock_pxa.inst.write.assert_any_call(":TRIG:SOUR IMM")

    def test_set_trigger_source_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Invalid trigger source"):
            mock_pxa.set_trigger_source("INVALID")


class TestTriggerLevel:
    def test_set_trigger_level(self, mock_pxa):
        mock_pxa.set_trigger_level(-20.0)
        mock_pxa.inst.write.assert_any_call(":TRIG:LEV -20.0")

    def test_set_trigger_level_positive(self, mock_pxa):
        mock_pxa.set_trigger_level(0.5)
        mock_pxa.inst.write.assert_any_call(":TRIG:LEV 0.5")


class TestTriggerDelay:
    def test_set_trigger_delay(self, mock_pxa):
        mock_pxa.set_trigger_delay(0.001)
        mock_pxa.inst.write.assert_any_call(":TRIG:DEL 0.001")

    def test_set_trigger_delay_zero(self, mock_pxa):
        mock_pxa.set_trigger_delay(0.0)
        mock_pxa.inst.write.assert_any_call(":TRIG:DEL 0.0")

    def test_set_trigger_delay_negative_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Trigger delay must be >= 0"):
            mock_pxa.set_trigger_delay(-1.0)


class TestTriggerSlope:
    def test_set_trigger_slope_pos(self, mock_pxa):
        mock_pxa.set_trigger_slope("POS")
        mock_pxa.inst.write.assert_any_call(":TRIG:SLOP POS")

    def test_set_trigger_slope_neg(self, mock_pxa):
        mock_pxa.set_trigger_slope("NEG")
        mock_pxa.inst.write.assert_any_call(":TRIG:SLOP NEG")

    def test_set_trigger_slope_case_insensitive(self, mock_pxa):
        mock_pxa.set_trigger_slope("pos")
        mock_pxa.inst.write.assert_any_call(":TRIG:SLOP POS")

    def test_set_trigger_slope_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Invalid trigger slope"):
            mock_pxa.set_trigger_slope("ZERO")


# ── Marker Operations ────────────────────────────────────────────────────────


class TestMarkerFrequency:
    def test_get_marker_frequency(self, mock_pxa):
        mock_pxa.inst.query.return_value = "2.4e9"
        result = mock_pxa.get_marker_frequency()
        assert isinstance(result, MeasurementResult)
        assert result.value == 2.4e9
        assert result.unit == "Hz"
        mock_pxa.inst.query.assert_any_call(":CALC:MARK1:X?")

    def test_get_marker_frequency_returns_float(self, mock_pxa):
        mock_pxa.inst.query.return_value = "100e6"
        result = mock_pxa.get_marker_frequency()
        assert isinstance(result.value, float)


class TestMarkerPosition:
    def test_set_marker_position(self, mock_pxa):
        mock_pxa.set_marker_position(1e9)
        mock_pxa.inst.write.assert_any_call(":CALC:MARK1:X 1000000000.0")

    def test_set_marker_position_validates_frequency(self, mock_pxa):
        with pytest.raises(Exception):
            mock_pxa.set_marker_position(60e9)  # Above max frequency


class TestMarkerNextPeak:
    def test_marker_next_peak(self, mock_pxa):
        mock_pxa.marker_next_peak()
        mock_pxa.inst.write.assert_any_call(":CALC:MARK1:MAX")


class TestMarkerThreshold:
    def test_set_marker_threshold(self, mock_pxa):
        mock_pxa.set_marker_threshold(-50.0)
        mock_pxa.inst.write.assert_any_call(":CALC:MARK1:THRESH -50.0")


class TestMarkerNoise:
    def test_get_marker_noise(self, mock_pxa):
        mock_pxa.inst.query.return_value = "-120.5"
        result = mock_pxa.get_marker_noise()
        assert isinstance(result, MeasurementResult)
        assert result.value == -120.5
        assert result.unit == "dBm/Hz"
        mock_pxa.inst.query.assert_any_call(":CALC:MARK1:NOIS?")


# ── Bandwidth & Sweep ────────────────────────────────────────────────────────


class TestRbwAuto:
    def test_set_rbw_auto_enable(self, mock_pxa):
        mock_pxa.set_rbw_auto(True)
        mock_pxa.inst.write.assert_any_call(":SENS:BAND:AUTO ON")

    def test_set_rbw_auto_disable(self, mock_pxa):
        mock_pxa.set_rbw_auto(False)
        mock_pxa.inst.write.assert_any_call(":SENS:BAND:AUTO OFF")


class TestVbwRatio:
    def test_set_vbw_ratio(self, mock_pxa):
        mock_pxa.set_vbw_ratio(3.0)
        mock_pxa.inst.write.assert_any_call(":SENS:BAND:VID:RAT 3.0")

    def test_set_vbw_ratio_fractional(self, mock_pxa):
        mock_pxa.set_vbw_ratio(0.1)
        mock_pxa.inst.write.assert_any_call(":SENS:BAND:VID:RAT 0.1")

    def test_set_vbw_ratio_zero_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="VBW ratio must be > 0"):
            mock_pxa.set_vbw_ratio(0.0)

    def test_set_vbw_ratio_negative_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="VBW ratio must be > 0"):
            mock_pxa.set_vbw_ratio(-1.0)


class TestSweepTime:
    def test_get_sweep_time(self, mock_pxa):
        mock_pxa.inst.query.return_value = "0.05"
        result = mock_pxa.get_sweep_time()
        assert result == 0.05
        mock_pxa.inst.query.assert_any_call(":SENS:SWE:TIME?")

    def test_get_sweep_time_returns_float(self, mock_pxa):
        mock_pxa.inst.query.return_value = "1.23"
        result = mock_pxa.get_sweep_time()
        assert isinstance(result, float)


class TestIfGain:
    def test_set_if_gain_zero(self, mock_pxa):
        mock_pxa.set_if_gain(0)
        mock_pxa.inst.write.assert_any_call(":SENS:POW:GAIN:IF 0")

    def test_set_if_gain_max(self, mock_pxa):
        mock_pxa.set_if_gain(30)
        mock_pxa.inst.write.assert_any_call(":SENS:POW:GAIN:IF 30")

    def test_set_if_gain_mid(self, mock_pxa):
        mock_pxa.set_if_gain(15)
        mock_pxa.inst.write.assert_any_call(":SENS:POW:GAIN:IF 15")

    def test_set_if_gain_negative_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="IF gain must be between 0 and 30"):
            mock_pxa.set_if_gain(-5)

    def test_set_if_gain_over_max_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="IF gain must be between 0 and 30"):
            mock_pxa.set_if_gain(35)


# ── Real-Time Spectrum Analysis (PXA-exclusive) ──────────────────────────────


class TestRtsaEnable:
    def test_set_rtsa_enable(self, mock_pxa):
        mock_pxa.set_rtsa_enable(True)
        mock_pxa.inst.write.assert_any_call(":SPEC:RTSA:STAT ON")

    def test_set_rtsa_disable(self, mock_pxa):
        mock_pxa.set_rtsa_enable(False)
        mock_pxa.inst.write.assert_any_call(":SPEC:RTSA:STAT OFF")


class TestCaptureBandwidth:
    def test_set_capture_bandwidth(self, mock_pxa):
        mock_pxa.set_capture_bandwidth(160e6)
        mock_pxa.inst.write.assert_any_call(":SPEC:RTSA:CAP:BAND 160000000.0")

    def test_set_capture_bandwidth_validates_frequency(self, mock_pxa):
        with pytest.raises(Exception):
            mock_pxa.set_capture_bandwidth(60e9)  # Above max frequency


class TestSpoiledRegions:
    def test_set_spoiled_regions(self, mock_pxa):
        mock_pxa.set_spoiled_regions(10)
        mock_pxa.inst.write.assert_any_call(":SPEC:RTSA:SWR:FCO 10")

    def test_set_spoiled_regions_zero(self, mock_pxa):
        mock_pxa.set_spoiled_regions(0)
        mock_pxa.inst.write.assert_any_call(":SPEC:RTSA:SWR:FCO 0")

    def test_set_spoiled_regions_negative_invalid(self, mock_pxa):
        with pytest.raises(ValueError, match="Spoiled region count must be >= 0"):
            mock_pxa.set_spoiled_regions(-1)


class TestSpectrumPowerDensity:
    def test_get_spectrum_power_density(self, mock_pxa):
        mock_pxa.inst.query.return_value = "-85.2"
        result = mock_pxa.get_spectrum_power_density()
        assert isinstance(result, MeasurementResult)
        assert result.value == -85.2
        assert result.unit == "dBm/Hz"
        mock_pxa.inst.query.assert_any_call(":CALC:MARK1:FUNC?")


# ── System ───────────────────────────────────────────────────────────────────


class TestOptionList:
    def test_get_option_list(self, mock_pxa):
        mock_pxa.inst.query.return_value = '"DP010,DP020,DP030"'
        result = mock_pxa.get_option_list()
        assert result == ["DP010", "DP020", "DP030"]
        mock_pxa.inst.query.assert_any_call(":SYST:OPT:LIST?")

    def test_get_option_list_empty(self, mock_pxa):
        mock_pxa.inst.query.return_value = '""'
        result = mock_pxa.get_option_list()
        assert result == []

    def test_get_option_list_single(self, mock_pxa):
        mock_pxa.inst.query.return_value = '"DP010"'
        result = mock_pxa.get_option_list()
        assert result == ["DP010"]


class TestSerialNumber:
    def test_get_serial_number(self, mock_pxa):
        mock_pxa.inst.query.return_value = '"MY12345678"'
        result = mock_pxa.get_serial_number()
        assert result == "MY12345678"
        mock_pxa.inst.query.assert_any_call(":SYST:SER")


class TestFirmwareVersion:
    def test_get_firmware_version(self, mock_pxa):
        mock_pxa.inst.query.return_value = '"A.22.10"'
        result = mock_pxa.get_firmware_version()
        assert result == "A.22.10"
        mock_pxa.inst.query.assert_any_call(":SYST:VER")


class TestSelfTest:
    def test_self_test_pass(self, mock_pxa):
        mock_pxa.inst.query.return_value = "0"
        result = mock_pxa.self_test()
        assert result is True
        mock_pxa.inst.query.assert_any_call(":DIAG:TEST?")

    def test_self_test_fail(self, mock_pxa):
        mock_pxa.inst.query.return_value = "1"
        result = mock_pxa.self_test()
        assert result is False

    def test_self_test_error_code(self, mock_pxa):
        mock_pxa.inst.query.return_value = "42"
        result = mock_pxa.self_test()
        assert result is False


# ── Inherited Methods (basic coverage) ───────────────────────────────────────


class TestInheritedMethods:
    def test_set_center_freq(self, mock_pxa):
        mock_pxa.set_center_freq(1e9)
        mock_pxa.inst.write.assert_any_call(":SENS:FREQ:CENT 1000000000.0")

    def test_set_center_freq_validates(self, mock_pxa):
        with pytest.raises(Exception):
            mock_pxa.set_center_freq(60e9)  # Above 50 GHz max

    def test_max_frequency(self, mock_pxa):
        assert mock_pxa.max_frequency == 50e9
