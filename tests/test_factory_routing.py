import os
import unittest
from unittest.mock import MagicMock, patch

import pyvisa

from instrumation.factory import get_instrument
from instrumation.drivers.generic import GenericDriver
from instrumation.drivers.simulated import SimulatedGeneric


def _mock_rm(idn: str):
    """Build a mock ResourceManager whose open_resource().query() returns idn."""
    rm = MagicMock()
    inst = MagicMock()
    inst.query.return_value = idn
    inst.timeout = 0
    rm.open_resource.return_value = inst
    return rm


class TestFactoryGenericFallback(unittest.TestCase):
    """Covers GH #142/#143: unrecognized IDN must never receive a
    brand-specific driver, and must resolve to the real GenericDriver."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_unrecognized_idn_returns_generic_driver(self):
        rm = _mock_rm("ACME,WIDGET-9000,SN123,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.5::INSTR", "DMM")
        self.assertIsInstance(drv, GenericDriver)

    def test_unrecognized_idn_does_not_pick_brand_driver_when_ambiguous(self):
        # Multiple brand-specific drivers are registered under "DMM"
        # (Keithley2000, Keithley2400, ...); an unrecognized IDN must not
        # silently receive any of them.
        rm = _mock_rm("UNKNOWNCO,MODEL-1,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.6::INSTR", "DMM")
        self.assertNotIn("Keithley", drv.__class__.__name__)
        self.assertIsInstance(drv, GenericDriver)

    def test_known_brand_idn_still_routes_correctly(self):
        rm = _mock_rm("KEITHLEY INSTRUMENTS,MODEL 2000,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.7::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "Keithley2000")

    def test_fluke_idn_routes_to_fluke8846a(self):
        rm = _mock_rm("FLUKE,8846A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.8::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "Fluke8846A")

    def test_fluke_8845a_idn_routes_to_fluke8846a(self):
        rm = _mock_rm("FLUKE,8845A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.9::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "Fluke8846A")

    def test_bk_precision_idn_routes_to_9130b(self):
        rm = _mock_rm("B&K PRECISION,9130B,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.10::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "BKPrecision9130B")

    def test_siglent_sdm_idn_routes_to_sdm3055(self):
        rm = _mock_rm("Siglent Technologies,SDM3055,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.11::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "SiglentSDM3055")

    def test_siglent_scope_idn_still_routes_to_sds(self):
        rm = _mock_rm("Siglent Technologies,SDS1104X-E,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.12::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "SiglentSDS")

    def test_siglent_sds2000x_plus_idn_routes_to_new_driver(self):
        rm = _mock_rm("Siglent Technologies,SDS2102X Plus,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.25::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "SiglentSDS2000XPlus")

    def test_rigol_mso5354_idn_routes_to_mso5000(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,MSO5354,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.26::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "RigolMSO5000")

    def test_keysight_dsox1204g_idn_routes_to_infiniivision(self):
        rm = _mock_rm("KEYSIGHT TECHNOLOGIES,DSOX1204G,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.27::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "KeysightInfiniiVision")

    def test_keysight_n9010b_exa_idn_routes_to_pxa(self):
        rm = _mock_rm("KEYSIGHT TECHNOLOGIES,N9010B,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.28::INSTR", "SA")
        self.assertEqual(drv.__class__.__name__, "KeysightPXA")

    def test_siglent_ssa3000x_idn_routes_correctly(self):
        rm = _mock_rm("Siglent Technologies,SSA3021X,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.29::INSTR", "SA")
        self.assertEqual(drv.__class__.__name__, "SiglentSSA3000X")

    def test_rigol_dsa875_idn_routes_to_rigol_dsa(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,DSA875,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.30::INSTR", "SA")
        self.assertEqual(drv.__class__.__name__, "RigolDSA")

    def test_siglent_sdg2000x_idn_routes_correctly(self):
        rm = _mock_rm("Siglent Technologies,SDG2042X,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.31::INSTR", "SG")
        self.assertEqual(drv.__class__.__name__, "SiglentSDG2000X")

    def test_rigol_dg4000_idn_routes_correctly(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,DG4062,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.32::INSTR", "SG")
        self.assertEqual(drv.__class__.__name__, "RigolDG4000")

    def test_gwinstek_mfg2000_idn_routes_correctly(self):
        rm = _mock_rm("GW INSTEK,MFG-2120,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.33::INSTR", "SG")
        self.assertEqual(drv.__class__.__name__, "GWInstekMFG2000")

    def test_srs_ds345_idn_routes_correctly(self):
        rm = _mock_rm("StanfordResearchSystems,DS345,12345,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::19::INSTR", "SG")
        self.assertEqual(drv.__class__.__name__, "SRSDS345")

    def test_siglent_sna5000a_idn_routes_correctly(self):
        rm = _mock_rm("Siglent Technologies,SNA5012A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.34::INSTR", "VNA")
        self.assertEqual(drv.__class__.__name__, "SiglentSNA5000A")

    def test_keysight_e4980a_idn_routes_correctly(self):
        rm = _mock_rm("KEYSIGHT TECHNOLOGIES,E4980A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::17::INSTR", "LCR")
        self.assertEqual(drv.__class__.__name__, "KeysightE4980A")

    def test_hioki_im3536_idn_routes_correctly(self):
        rm = _mock_rm("HIOKI,IM3536,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::18::INSTR", "LCR")
        self.assertEqual(drv.__class__.__name__, "HiokiIM3536")

    def test_srs_sr830_idn_routes_correctly(self):
        rm = _mock_rm("StanfordResearchSystems,SR830,12345,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::8::INSTR", "LOCKIN")
        self.assertEqual(drv.__class__.__name__, "SRSSR830")

    def test_fluke_pm6690_idn_routes_correctly(self):
        rm = _mock_rm("FLUKE,PM6690,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::3::INSTR", "COUNTER")
        self.assertEqual(drv.__class__.__name__, "FlukePM6690")

    def test_keysight_53230a_idn_routes_correctly(self):
        rm = _mock_rm("KEYSIGHT TECHNOLOGIES,53230A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::4::INSTR", "COUNTER")
        self.assertEqual(drv.__class__.__name__, "Keysight53230A")

    def test_keysight_53181a_idn_routes_correctly(self):
        rm = _mock_rm("KEYSIGHT TECHNOLOGIES,53181A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::5::INSTR", "COUNTER")
        self.assertEqual(drv.__class__.__name__, "Keysight53230A")

    def test_minicircuits_switch_idn_routes_correctly(self):
        rm = _mock_rm("Mini-Circuits,RC-4SPDT-A18,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.35::INSTR", "SWITCH")
        self.assertEqual(drv.__class__.__name__, "MiniCircuitsRCSwitch")

    def test_keysight_u2000_idn_routes_correctly(self):
        rm = _mock_rm("Keysight Technologies,U2004A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("USB0::0x0957::0x2A18::MY12345::INSTR", "SENSOR")
        self.assertEqual(drv.__class__.__name__, "KeysightU2000")

    def test_rs_nrpz_idn_routes_correctly(self):
        rm = _mock_rm("Rohde&Schwarz,NRP-Z21,100001,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("USB0::0x0AAD::0x0138::100001::INSTR", "SENSOR")
        self.assertEqual(drv.__class__.__name__, "RohdeSchwarzNRPZ")

    def test_yokogawa_wt310_idn_routes_correctly(self):
        rm = _mock_rm("YOKOGAWA,WT310,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::1::INSTR", "POWERMETER")
        self.assertEqual(drv.__class__.__name__, "YokogawaWT310")

    def test_tektronix_pa1000_idn_routes_correctly(self):
        rm = _mock_rm("TEKTRONIX,PA1000,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.40::INSTR", "POWERMETER")
        self.assertEqual(drv.__class__.__name__, "TektronixPA1000")

    def test_tektronix_afg_idn_still_routes_correctly(self):
        rm = _mock_rm("TEKTRONIX,AFG3022C,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::10::INSTR", "SG")
        self.assertEqual(drv.__class__.__name__, "TektronixAFG")

    def test_ambiguous_counter_idn_falls_back_to_generic(self):
        # Both COUNTER drivers register lazily on first import inside
        # factory.py branches; force both imports so this test doesn't
        # depend on prior test execution order within the same process.
        import instrumation.drivers.keysight  # noqa: F401
        import instrumation.drivers.fluke_counter  # noqa: F401
        rm = _mock_rm("UNKNOWNCO,COUNTER-1,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::6::INSTR", "COUNTER")
        self.assertIsInstance(drv, GenericDriver)

    def test_rigol_dm3068_idn_routes_to_rigol_dmm(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,DM3068,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.13::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "RigolDM3068")

    def test_rigol_scope_idn_still_routes_to_ds1054z(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,DS1054Z,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.14::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "RigolDS1054Z")

    def test_keithley_dmm6500_idn_routes_correctly(self):
        rm = _mock_rm("KEITHLEY INSTRUMENTS,MODEL DMM6500,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.15::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "KeithleyDMM6500")

    def test_keithley_2000_idn_still_routes_correctly(self):
        rm = _mock_rm("KEITHLEY INSTRUMENTS,MODEL 2000,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.16::INSTR", "DMM")
        self.assertEqual(drv.__class__.__name__, "Keithley2000")

    def test_rigol_dp832_idn_routes_to_rigol_psu(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,DP832,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.17::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "RigolDP832")

    def test_siglent_spd3303x_idn_routes_to_siglent_psu(self):
        rm = _mock_rm("Siglent Technologies,SPD3303X,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.18::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "SiglentSPD3303X")

    def test_keysight_e36313a_idn_routes_to_keysight_psu(self):
        rm = _mock_rm("Keysight Technologies,E36313A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.19::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "KeysightE36313A")

    def test_korad_idn_routes_to_korad_ka3005p(self):
        rm = _mock_rm("KORADKA3005PV2.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.20::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "KoradKA3005P")

    def test_gwinstek_gpp4323_idn_routes_correctly(self):
        rm = _mock_rm("GW INSTEK,GPP-4323,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.21::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "GWInstekGPP4323")

    def test_rigol_dl3021_idn_routes_to_rigol_load(self):
        rm = _mock_rm("RIGOL TECHNOLOGIES,DL3021,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.22::INSTR", "LOAD")
        self.assertEqual(drv.__class__.__name__, "RigolDL3021")

    def test_itech_it8512_idn_routes_correctly(self):
        rm = _mock_rm("ITECH,IT8512+,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.23::INSTR", "LOAD")
        self.assertEqual(drv.__class__.__name__, "ItechIT8512Plus")

    def test_chroma_63204a_idn_routes_correctly(self):
        rm = _mock_rm("CHROMA,63204A,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.24::INSTR", "LOAD")
        self.assertEqual(drv.__class__.__name__, "Chroma63200A")

    def test_bk_precision_idn_routes_to_8600_load(self):
        rm = _mock_rm("B&K PRECISION,8600,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.11::INSTR", "LOAD")
        self.assertEqual(drv.__class__.__name__, "BKPrecision8600")

    def test_hameg_hmo_idn_routes_to_rs_hmo_compact(self):
        rm = _mock_rm("HAMEG,HMO722,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.12::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "RohdeSchwarzHMOCompact")

    def test_rohde_schwarz_hmo_idn_routes_to_rs_hmo_compact(self):
        rm = _mock_rm("ROHDE&SCHWARZ,HMO2024,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.13::INSTR", "SCOPE")
        self.assertEqual(drv.__class__.__name__, "RohdeSchwarzHMOCompact")

    def test_agilent_6632b_idn_routes_correctly(self):
        rm = _mock_rm("AGILENT TECHNOLOGIES,6632B,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::5::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "Agilent6632B")

    def test_aimtti_cpx400dp_idn_routes_correctly(self):
        rm = _mock_rm("AIM-TTI,CPX400DP,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("ASRL3::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "AimTTiCPX400DP")

    def test_sorensen_sg_idn_routes_correctly(self):
        rm = _mock_rm("SORENSEN,SGA80-38,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::10::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "SorensenSG")

    def test_prodigit_3311f_idn_routes_correctly(self):
        rm = _mock_rm("PRODIGIT,3311F,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("GPIB0::12::INSTR", "LOAD")
        self.assertEqual(drv.__class__.__name__, "Prodigit3311F")

    def test_bk_precision_idn_routes_to_1685b_psu(self):
        rm = _mock_rm("B&K PRECISION,1685B,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("ASRL7::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "BKPrecision1685B")

    def test_rohde_schwarz_hmp4040_idn_routes_correctly(self):
        rm = _mock_rm("ROHDE&SCHWARZ,HMP4040,SN1,1.0")
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("TCPIP::10.0.0.14::INSTR", "PSU")
        self.assertEqual(drv.__class__.__name__, "RohdeSchwarzHMP4040")


class TestFactoryGenericSimMode(unittest.TestCase):
    """Covers GH #142/#147: SIM-mode GENERIC must not secretly be a DMM."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_sim_generic_is_not_multimeter(self):
        drv = get_instrument("USB::0x1234::SIM", "GENERIC")
        self.assertIsInstance(drv, SimulatedGeneric)
        self.assertNotEqual(drv.__class__.__name__, "SimulatedMultimeter")

    def test_sim_generic_registered_in_registry(self):
        from instrumation.drivers.registry import DriverRegistry
        drivers = DriverRegistry.get_drivers_by_type("GENERIC")
        self.assertTrue(any(d.__name__ == "SimulatedGeneric" for d in drivers))


class TestFactoryASRLSmartProbe(unittest.TestCase):
    """Covers GH #145/#150: TDK-Lambda smart probe on ASRL ports."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_asrl_unrelated_serial_device_does_not_get_tdk_driver(self):
        # A non-TDK serial device that doesn't understand INST:NSEL should
        # fail the smart probe gracefully and fall through to IDN discovery,
        # never silently becoming a TDKLambdaZPlus.
        rm = MagicMock()
        inst = MagicMock()

        def write_side_effect(cmd):
            if cmd == "INST:NSEL 6":
                raise Exception("unsupported command")

        inst.write.side_effect = write_side_effect
        inst.query.return_value = "UNRELATED,SERIAL-DEVICE,SN1,1.0"
        rm.open_resource.return_value = inst
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("ASRL5::INSTR", "PSU")
        self.assertNotEqual(drv.__class__.__name__, "TDKLambdaZPlus")

    def test_asrl_smart_probe_disabled_for_auto_discovery(self):
        # #150: the TDK-specific INST:NSEL handshake must never be sent to
        # arbitrary serial devices during AUTO discovery. probe_asrl=False
        # is how the AUTO probe_resource path calls get_instrument.
        rm = MagicMock()
        inst = MagicMock()
        inst.query.return_value = "UNRELATED,SERIAL-DEVICE,SN1,1.0"
        rm.open_resource.return_value = inst
        with patch("instrumation.factory.get_rm", return_value=rm):
            drv = get_instrument("ASRL5::INSTR", "PSU", probe_asrl=False)
        writes = [c.args[0] for c in inst.write.call_args_list]
        self.assertNotIn("INST:NSEL 6", writes)


class TestFactoryIDNErrorHandling(unittest.TestCase):
    """Covers GH #149: broad except during IDN probing hides real errors."""

    def setUp(self):
        os.environ["INSTRUMATION_MODE"] = "REAL"

    def tearDown(self):
        os.environ["INSTRUMATION_MODE"] = "SIM"

    def test_identification_programming_error_propagates(self):
        # A genuine (non-transport) error during identification must surface
        # instead of being swallowed into a silent GENERIC fallback.
        rm = MagicMock()
        with patch("instrumation.factory.get_rm", return_value=rm):
            with patch(
                "instrumation.drivers.real.RealDriver.get_id",
                side_effect=AttributeError("boom"),
            ):
                with self.assertRaises(AttributeError):
                    get_instrument("TCPIP::10.0.0.8::INSTR", "DMM")

    def test_identification_visa_error_is_swallowed(self):
        # Expected transport failures (unreachable/timeout) degrade to
        # unidentified and fall back to GENERIC, not a crash.
        rm = MagicMock()
        with patch("instrumation.factory.get_rm", return_value=rm):
            with patch(
                "instrumation.drivers.real.RealDriver.get_id",
                side_effect=pyvisa.VisaIOError(1073676294),  # VI_ERROR_TMO
            ):
                drv = get_instrument("TCPIP::10.0.0.9::INSTR", "DMM")
        self.assertIsInstance(drv, GenericDriver)


if __name__ == "__main__":
    unittest.main()
