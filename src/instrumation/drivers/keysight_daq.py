from typing import List, Union
from .base import DataAcquisitionUnit
from .registry import register_driver
from .real import RealDriver
from ..results import MeasurementResult


@register_driver("DAQ")
class KeysightDAQ970A(RealDriver, DataAcquisitionUnit):
    """Driver for Keysight DAQ970A/DAQ973A Data Acquisition Systems.

    Successor to the venerable 34970A/34972A Data Acquisition/Switch
    Unit, backward-compatible at the command level. Channels are
    addressed with SCPI channel-list syntax: slot number is the
    hundreds digit, channel is the tens/units (e.g. ``101`` = slot 1
    channel 01, ``203`` = slot 2 channel 03). Most commands accept a
    full channel list, e.g. ``(@101:110)`` or ``(@101,102,203)`` --
    see `DataAcquisitionUnit.format_channel_list`.

    Command Reference (DAQ970A/DAQ973A Programming Guide):
        - CONFigure:VOLTage:DC <range>,<resolution>,(@<ch list>)
        - CONFigure:VOLTage:AC (@<ch list>)
        - CONFigure:RESistance <range>,(@<ch list>)          — 2-wire
        - CONFigure:FRESistance <range>,(@<ch list>)         — 4-wire
        - CONFigure:TEMPerature <probe_type>,<type>,(@<ch list>)
        - CONFigure:FREQuency (@<ch list>)
        - MEASure:<FUNC>? [<range>[,<resolution>]],(@<ch list>)
        - READ?                                              — fetch scan data
        - ROUTe:SCAN (@<ch list>)                             — define scan list
        - ROUTe:CLOSe (@<ch list>) / ROUTe:OPEN (@<ch list>)
        - ROUTe:CLOSe? (@<ch>)                                — query relay state
        - INITiate / TRIGger:SOURce {IMMediate|BUS|EXTernal}
        - *IDN? / *RST / *CLS / *OPC?
    """

    _FUNC_MAP = {
        "VOLT:DC": "VOLT:DC",
        "VOLT:AC": "VOLT:AC",
        "RES": "RES",
        "FRES": "FRES",
        "TEMP": "TEMP",
        "FREQ": "FREQ",
    }

    def configure_channel(self, channel: Union[List[int], List[str], str], function: str, **kwargs) -> None:
        func_key = function.upper()
        if func_key not in self._FUNC_MAP:
            raise ValueError(f"Unsupported measurement function: {function}")
        ch_list = self.format_channel_list(channel)

        if func_key == "TEMP":
            probe_type = kwargs.get("probe_type", "TC")
            sensor = kwargs.get("sensor", "K")
            self.safe_send(f"CONF:TEMP {probe_type},{sensor},{ch_list}")
            return

        # Optional <range>[,<resolution>] prefix before the channel list.
        params = []
        if "range" in kwargs:
            params.append(str(kwargs["range"]))
            if "resolution" in kwargs:
                params.append(str(kwargs["resolution"]))
        params.append(ch_list)
        self.safe_send(f"CONF:{self._FUNC_MAP[func_key]} {','.join(params)}")

    def measure_scan(self, channels: Union[List[int], List[str], str]) -> MeasurementResult:
        ch_list = self.format_channel_list(channels)
        resp = self.query_ascii(f"READ? {ch_list}")
        values = [float(v) for v in resp.split(",") if v.strip()]
        return MeasurementResult(values, "")

    def read_channel(self, channel: str) -> MeasurementResult:
        ch_list = self.format_channel_list(channel if isinstance(channel, (list, str)) else [channel])
        val = self.query_ascii(f"READ? {ch_list}")
        parts = [float(v) for v in val.split(",") if v.strip()]
        return MeasurementResult(parts[0] if len(parts) == 1 else parts, "", channel=channel)

    def set_scan_list(self, channels: Union[List[int], List[str], str]) -> None:
        ch_list = self.format_channel_list(channels)
        self.safe_send(f"ROUT:SCAN {ch_list}")

    def start_scan(self) -> None:
        self.write("INIT")

    def get_scan_data(self) -> MeasurementResult:
        resp = self.query_ascii("FETC?")
        values = [float(v) for v in resp.split(",") if v.strip()]
        return MeasurementResult(values, "")

    def set_trigger_source(self, source: str) -> None:
        key = source.upper()
        mapping = {"IMMEDIATE": "IMM", "BUS": "BUS", "EXTERNAL": "EXT"}
        if key not in mapping and key not in mapping.values():
            raise ValueError(f"Invalid trigger source: {source}")
        self.safe_send(f"TRIG:SOUR {mapping.get(key, key)}")

    def close_relay(self, channel: Union[List[int], List[str], str]) -> None:
        ch_list = self.format_channel_list(channel if isinstance(channel, (list, str)) else [channel])
        self.safe_send(f"ROUT:CLOS {ch_list}")

    def open_relay(self, channel: Union[List[int], List[str], str]) -> None:
        ch_list = self.format_channel_list(channel if isinstance(channel, (list, str)) else [channel])
        self.safe_send(f"ROUT:OPEN {ch_list}")

    def get_relay_state(self, channel: str) -> bool:
        ch_list = self.format_channel_list([channel])
        resp = self.query_ascii(f"ROUT:CLOS? {ch_list}").strip()
        return resp in ("1", "ON")

    def shutdown_safety(self) -> None:
        self.write("ROUT:OPEN (@100:322)")
        self.sync_config()
