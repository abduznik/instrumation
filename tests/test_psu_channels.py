"""GH #248: uniform channel= on PowerSupply aliases + CHANNELS."""
from unittest.mock import MagicMock

from instrumation.drivers.korad import KoradKA3005P
from instrumation.drivers.rigol_psu import RigolDP832


def _mock(drv):
    drv.inst = MagicMock()
    drv.check_errors_enabled = False
    return drv


def test_aliases_forward_channel_on_multichannel_psu():
    psu = _mock(RigolDP832("TCPIP::1::INSTR"))
    psu.set_current(0.5, channel=2)
    psu.inst.write.assert_called_with("SOUR2:CURR 0.5")
    psu.inst.query.return_value = "3.3"
    assert psu.measure_voltage(channel=3).value == 3.3
    psu.inst.query.assert_any_call("MEAS:VOLT? CH3")


def test_aliases_still_work_on_single_channel_psu():
    psu = _mock(KoradKA3005P("ASRL1::INSTR"))
    psu.set_current(0.5)  # no channel kwarg forwarded to a channel-less driver
    assert psu.CHANNELS == (1,)


def test_shutdown_iterates_channels():
    psu = _mock(RigolDP832("TCPIP::1::INSTR"))
    psu.shutdown_safety()
    writes = [c.args[0] for c in psu.inst.write.call_args_list]
    assert [w for w in writes if w.startswith("OUTP ")] == [f"OUTP CH{c},OFF" for c in RigolDP832.CHANNELS]
