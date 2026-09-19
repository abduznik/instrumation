# Supported Instruments

This page lists all instrument models that Instrumation supports — both the
specific models that have been validated and the broader families that share
the same SCPI command set.

> [!NOTE]
> **Compatibility matrix convention** (see issue #167): every driver
> section lists a **Validated Model** — the specific unit tested against
> real hardware — and an **Also likely compatible** list of sibling
> models that share the same SCPI command set but have not been verified
> in-lab. When one driver class is routed from multiple distinct IDN
> branches in `factory.py` (e.g. `Keysight34461A` serving both the
> Truevolt and legacy 34401-series families), each branch's models are
> called out explicitly with their own compatibility status, since a
> sub-model's SCPI dialect can diverge silently. Treat "assumed
> compatible" as best-effort: fall back to `"GENERIC"` passthrough if an
> untested model raises SCPI errors on a typed command.

---

## Oscilloscopes

### Keysight InfiniiVision

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightInfiniiVision` | DSOX2002A | DSOX/MSOX 2000–6000 Series | `DSO-X`, `MSO-X`, `DSOX`, `MSOX` |

**Also likely compatible** (same InfiniiVision SCPI set):
- DSOX1002A–DSOX1004A, DSOX1102G, DSOX1204G, DSOX2004A–DSOX2012A, DSOX3002T–DSOX3054T
- MSOX1002A–MSOX1004A, MSOX2004A–MSOX3054T, MSOX4002A–MSOX4154A
- DSOX6002A–DSOX6054A, MSOX6002A–MSOX6054A
- EDUX1052A/G

### Rigol DS1000Z / MSO1000Z

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolDS1054Z` | DS1054Z | DS1000Z/MSO1000Z Series | `DS1054Z`, `DS1074Z`, `DS1104Z`, `MSO1054Z`, `DS1000Z`, `MSO1000Z` |

**Also likely compatible** (same MSO1000Z/DS1000Z SCPI set):
- DS1054Z, DS1074Z, DS1102Z, DS1104Z, DS1202Z, DS1204Z
- MSO1054Z, MSO1074Z, MSO1102Z, MSO1104Z, MSO1202Z, MSO1204Z
- DSEQ (DS1000Z-EDU variants)

> [!NOTE]
> The driver implements universal DS1000Z SCPI commands only. LA (logic
> analyzer), `:SOURce` (AWG), `:DECoder`, `:MASK`, and `:FUNCtion`
> commands are reserved for the -S variants or paid options and are not
> covered.

### Rigol MSO5000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolMSO5000` | MSO5354 | MSO5000 Series | `RIGOL` + `MSO5` |

Basic control (`:RUN`/`:STOP`/`:SINGle`/`:AUTOscale`) matches the
MSO1000Z/DS1000Z family, but the measurement subsystem differs:
`:MEASure:ITEM? <item>,<src>` takes the source as an explicit second
argument on every query rather than DS1000Z's per-item
`:MEASure:FREQuency? CHANnel<n>` form.

**Also likely compatible** (same MSO5000 command set):
- MSO5072, MSO5074, MSO5102, MSO5104, MSO5204, MSO5354

> [!NOTE]
> LA (logic analyzer), protocol decode, and mask-test features from
> the Programming Guide are not implemented here.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Siglent SDS

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDS` | SDS1000 Series | SDS Series | `SIGLENT` |

**Also likely compatible:**
- SDS1002X-E, SDS1004X-E, SDS1102X-E, SDS1104X-E, SDS1202X-E, SDS1204X-E
- SDS2002X, SDS2004X, SDS2102X, SDS2104X, SDS2202X, SDS2204X

### Siglent SDS2000X Plus

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDS2000XPlus` | SDS2102X Plus | SDS Series (newer command set) | `SIGLENT` + `PLUS` (with `SDS1`/`SDS2`/`SDS5`) |

Uses the newer standard `:SUBsystem:keyword` command set from the SDS
Series Programming Guide (EN11D+) -- `:TRIGger:RUN`/`:TRIGger:STOP`/
`:TRIGger:MODE SINGle` and `:MEASure:SIMPle:VALue? <type>` -- distinct
from the legacy `SiglentSDS` driver's older `ARM`/`TRSE`/`C<n>:PAVA?`
command shapes still used by the original SDS1000/SDS2000X(-E).

**Also likely compatible** (same newer command set):
- SDS1000X HD, SDS5000X, SDS2000X Plus family models (any `...Plus`/`HD` variant)

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Tektronix TDS

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `TektronixTDS` | TDS Series | Tek TDS/TPS/MDO | `TEKTRONIX` (non-AFG) |

### Rohde & Schwarz / Hameg HMO Compact

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RohdeSchwarzHMOCompact` | HMO722 | HMO Compact Series | `HAMEG`/`ROHDE`/`ROHDE&SCHWARZ` + `HMO` |

**Also likely compatible** (same HMO Compact SCPI set):
- HMO724, HMO1022, HMO1024, HMO1522, HMO1524, HMO2022, HMO2024

> [!NOTE]
> Edge trigger only. Math functions (FFT, add/subtract/multiply), protocol
> decode, and mask-test features from the Programmer's Manual are not yet
> implemented.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

**Also likely compatible:**
- TDS1001C–TDS1012C, TDS2001C–TDS2024C, TDS2012B, TDS2022B
- TPS2002B–TPS2024B
- MDO3012–MDO3054 (basic scope commands)

---

## Spectrum Analyzers

### Keysight MXA / PXA

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightMXA` | MXA N9020A | MXA Series | `MXA` |
| `KeysightPXA` | PXA N9030A | PXA Series | `N9030`, `PXA` |

> [!NOTE]
> `KeysightPXA` (v0.8.0+) ships 29 PXA-specific SCPI methods — measurement
> configuration, advanced triggering, enhanced markers, bandwidth/sweep,
> Real-Time Spectrum Analysis, and system queries — on top of the shared
> spectrum analyzer base API.

**Also likely compatible:**
- MXA N9010A/B (EXA), N9020A/B, N9021A
- PXA N9030A, N9040B

### Rigol DSA

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolDSA` | DSA800 Series | DSA800 | `RIGOL` (non-scope) |

**Also likely compatible:**
- DSA815, DSA815-TG, DSA832E, DSA875E

### Rohde & Schwarz

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RohdeSchwarzSA` | FSV / FSW Series | R&S SA | `ROHDE&SCHWARZ`, `R&S` |

**Also likely compatible:**
- FSV, FSVR, FSW, FSWP, FPS, FPL

### Anritsu

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `AnritsuSA` | MS2830A | MS2830/MS269x | `ANRITSU` |

**Also likely compatible:**
- MS2830A, MS2690A, MS2691A, MS2692A

### Siglent SSA3000X

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSSA3000X` | SSA3021X | SSA3000X Series | `SIGLENT` + `SSA` |

Standard SCPI-99 spectrum-analyzer subsystem, the same command shape as
`RigolDSA`/`AnritsuSA`.

**Also likely compatible:**
- SSA3011X, SSA3015X, SSA3032X, SSA3000X Plus, SSA3000X-R, SVA1000X

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## Signal Generators

### Keysight EXG / MXG

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightSG` | MXG N5183B | EXG/MXG/PSG Series | `N5181`, `N5182`, `N5183`, `PSG`, `MXG`, `EXG` |

**Also likely compatible:**
- EXG N5171B, N5172B, N5173B
- MXG N5181A/B, N5182A/B, N5183A/B
- PSG E8257D, E8267D

### Rohde & Schwarz

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RohdeSchwarzSG` | SMA100B / SMC100A | R&S SG | `ROHDE&SCHWARZ` (SG context) |

**Also likely compatible:**
- SMA100A/B, SMB100A, SMC100A, SMF100A

### Anritsu

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `AnritsuSG` | MG3700A | MG3700 Series | `ANRITSU` (SG context) |

### Tektronix AFG

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `TektronixAFG` | AFG3022C | AFG3000 Series | `TEKTRONIX` + `AFG` |

**Also likely compatible:**
- AFG3011C, AFG3021C, AFG3022C, AFG3102C, AFG3252C

### Siglent SDG2000X

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDG2000X` | SDG2042X | SDG Series AWG | `SIGLENT` + `SDG` |

Uses Siglent's `C<n>:BSWV` (Basic Wave) command: a single keyword
takes comma-separated `PARAM,value` pairs (`C1:BSWV FRQ,1000`,
`C1:BSWV AMP,1`) rather than one SCPI subtree per parameter --
distinct from the Tektronix AFG3000's
`SOURce<n>:FREQuency:FIXed`-per-parameter dialect. Has no
frequency-list sweep mode, so `configure_list_sweep()` logs an
unsupported-feature warning.

**Also likely compatible** (same BSWV/OUTP command set):
- SDG1000X, SDG2000X Plus, SDG6000X

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Rigol DG4000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolDG4000` | DG4062 | DG1000Z/DG4000/DG5000 Series | `RIGOL` + (`DG4`, `DG5`, `DG1000Z`) |

Uses the Agilent/Keysight-33500-derived
`[:SOURce[<n>]]:APPLy:<shape>` single-command style shared across the
DG1000Z/DG4000/DG5000 families -- distinct from Tektronix AFG3000's
subtree-per-parameter dialect and Siglent SDG's comma-separated
`BSWV` keyword. Has no frequency-list sweep mode in this base command
set, so `configure_list_sweep()` logs an unsupported-feature warning.

**Also likely compatible** (same APPLy/SOURce command set):
- DG4102, DG4162, DG4202, DG1022Z, DG1032Z, DG5071, DG5102, DG5252

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### GW Instek MFG-2000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `GWInstekMFG2000` | MFG-2120 | MFG-2000 Series | `GW`/`GW INSTEK` + `MFG` |

Combines Rigol-style `SOURce<n>:APPLy:<shape>` waveform selection with
a separate per-parameter SCPI subtree for frequency/amplitude/offset/
phase (`SOURce<n>:FREQuency`, `SOURce<n>:AMPLitude`,
`SOURce<n>:DCOffset`, `SOURce<n>:PHASe`) -- unlike Rigol's single
combined-argument `APPLy` call, MFG-2000 setpoints are each sent
independently after selecting the waveform shape. Roadmap #176.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Stanford Research Systems DS345

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SRSDS345` | DS345 | SRS terse mnemonics (non-SCPI-subtree) | `STANFORD` + `DS345` |

Uses SRS's distinctively terse, colon-free command mnemonics (`FREQ`,
`AMPL`, `OFFS`, `FUNC`, `PHSE`) rather than a SCPI `:SOURce:*` subtree;
waveform shape is a numeric code (0=sine, 1=square, 2=triangle,
3=ramp, 4=noise, 5=arbitrary) instead of a mnemonic string. The DS345
has **no software output-enable command** -- the configured waveform
is always live on the output BNC -- so `set_output()` logs an
unsupported-feature warning and `get_output()` always reports `True`.

> [!WARNING]
> Not yet verified against real hardware. If you hit a command error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## Network Analyzers

### Keysight PNA

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightPNA` | PNA N5232A | PNA / PNA-L / PNA-X | `E83`, `N52`, `PNA` |

**Also likely compatible:**
- E8361C, E8362B, N5221A, N5222A, N5224A, N5225A, N5227A, N5230A–N5247A

### Keysight FieldFox

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightFieldFox` | N9913A / N9914A | FieldFox SA+VNA | `N99`, `FIELD FOX` |

### Anritsu ShockLine / MS2035B

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `AnritsuShockLineVNA` | MS2035B | ShockLine Series | `MS2035` |

**Also likely compatible:**
- MS2034B, MS2035B, MS2036A, MS2037A, MS2038C, MS2039C, MS2047A, MS2060A

### Siglent SNA5000A

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSNA5000A` | SNA5012A | SNA5000A/X Series | `SIGLENT` + `SNA` |

Standard SCPI-99 network-analyzer subsystem, the same command shape as
`KeysightPNA` -- Siglent's SNA5000A documentation is explicitly
SCPI-99 compliant for this measurement class.

**Also likely compatible:**
- SNA5014A, SNA5024A, SNA5044A, SNA5000X series

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## Multimeters

### Keysight 34461A Truevolt

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Keysight34461A` | 34461A | Truevolt DMM | `34461`, `34460`, `34401`, `34410`, `34411`, `34420` |

`Keysight34461A` is shared across two IDN branches in `factory.py`
(`~line 423` and `~line 429`, see issue #167): the Truevolt 34460/34461
family and the older 34401/34410/34411/34420 family. Only 34461A has been
tested against real hardware; the rest are **assumed compatible** based
on their published SCPI command references, not verified in-lab:

| Model | Family | Status |
|:---|:---|:---|
| 34461A | Truevolt | ✅ Validated |
| 34460A | Truevolt | Assumed compatible (6.5 digit, same SCPI set as 34461A) |
| 34401A | Legacy | Assumed compatible (base `MEAS:`/`CONF:` subset only) |
| 34410A | Legacy | Assumed compatible (6.5 digit) |
| 34411A | Legacy | Assumed compatible (6.5 digit) |
| 34420A | Legacy | Assumed compatible (μV/μΩ nanovolt commands untested) |

> [!WARNING]
> The 34401/34410/34411/34420 family predates Truevolt and may not
> support every SCPI command `Keysight34461A` sends (e.g. newer
> `SENSe` subsystem extensions). If you hit an SCPI error on one of
> these models, prefer `"GENERIC"` passthrough or file an issue with
> the failing command.

### Fluke 8845A/8846A

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Fluke8846A` | 8846A | Fluke 884x Series | `FLUKE` + (`8845`, `8846`) |

`Fluke8846A` is not validated against real hardware yet; it targets the
`:MEAS:*?`/`:CONF:*` SCPI subset documented in the Fluke 8845A/8846A
Programmer's Manual, mirroring `Keysight34461A`'s command shapes:

| Model | Status |
|:---|:---|
| 8846A | Assumed compatible (6.5 digit, same measurement subsystem as 8845A) |
| 8845A | Assumed compatible (5.5 digit, same command set as 8846A) |

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Keithley 2000

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Keithley2000` | 2000 | Keithley 2000 Series | `KEITHLEY` + `2000` |

### Siglent SDM3000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDM3055` | SDM3055 | SDM3000 Series | `SIGLENT` + `SDM` |

Standard SCPI-99 `MEASure`/`CONFigure` multimeter subsystem, the same
command shape as the Keysight 34401A family and Fluke 884x — DCV, ACV,
DCI, ACI, 2W/4W resistance, frequency, period, capacitance, continuity,
diode, and RTD/thermistor temperature. `set_nplc()` is SDM3000-specific.

**Also likely compatible** (same SDM series command set):
- SDM3045X, SDM3065X, SDM3055A

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Rigol DM3000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolDM3068` | DM3068 | DM3000 Series | `RIGOL` + `DM3` |

Unlike the SCPI-99 `CONFigure`/`MEASure?` split used elsewhere in this
library, the DM3000 dialect selects the active function with
`:FUNCtion:*` and reads it back with a bare `:MEASure:<FUNC>?` query;
`:MEASure {AUTO|MANU}` toggles ranging globally instead of a per-function
`RANG:AUTO`. `set_digits()` (5/6/7/INC/DEC) is DM3000-specific.

**Also likely compatible** (same DM3000 command set):
- DM3058, DM3058E, DM3062, DM3064

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Keithley DMM6500

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeithleyDMM6500` | DMM6500 | DMM6500 native SCPI | `KEITHLEY` + (`DMM6500`, `6500`) |

Targets the DMM6500's native SCPI command set (function selection via
`:SENSe:FUNCtion "<FUNC>"` then `:READ?`), not the `SCPI2000`/`SCPI34401`
compatibility personalities or TSP scripting. `set_nplc()`,
`set_auto_range()` and `set_offset_compensation()` take an explicit
SCPI function-name argument since ranging/NPLC live under
`:SENSe:<FUNC>:*`, not a single global subsystem.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## Power Supplies

### TDK-Lambda Z+

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `TDKLambdaZPlus` | Z+100-2 | Z+ Series (Serial/USB) | `TDK-LAMBDA`, `Z+` |

**Also likely compatible:**
- Z+36-10, Z+50-2.5, Z+60-5, Z+100-2, Z+100-7, Z+150-4, Z+200-2.5, Z+360-1.7

> [!IMPORTANT]
> Z+ units must be switched to USB mode on the front panel and
> wake up with `INST:NSEL 6` before SCPI communication.

### BK Precision 9130B

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `BKPrecision9130B` | 9130B | 9130B Series (Triple Output) | `B&K`/`BK PRECISION` + `9130` |

Not yet validated against real hardware. Three independent output
channels are addressed via `INST:NSEL {1\|2\|3}`; every `PowerSupply`
interface method accepts an optional `channel=` argument (defaults to
channel 1) to select which output it targets before sending the
plain `VOLT`/`CURR`/`OUTP`/`MEAS:*?` command. `set_tracking_mode()` is
9130B-specific and links CH2/CH3 outputs.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Rigol DP800 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolDP832` | DP832 | DP800 Series (Triple Output) | `RIGOL` + `DP8` |

Unlike the BK Precision 9130B's `INST:NSEL`-then-plain-command style,
DP800 series commands address a channel directly via a `[:SOURce<n>]`
numeric suffix or an explicit `CH1|CH2|CH3` argument on
`:OUTPut`/`:MEASure` — no channel-select round-trip required. Every
`PowerSupply` interface method accepts an optional `channel=` (defaults
to 1). `set_tracking_mode()` is DP800-specific and links CH2/CH3.

**Also likely compatible** (same DP800 command set):
- DP831, DP831A, DP832A, DP821, DP821A, DP811, DP811A

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Siglent SPD3303X

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSPD3303X` | SPD3303X | SPD3303X Series | `SIGLENT` + `SPD` |

CH1/CH2 are independently controlled outputs addressed with a `CH1`/
`CH2` command prefix; CH3 is a fixed 5V/2.5A logic supply with
output-enable control only (no settable voltage/current, and
`set_ovp`/`set_ocp`/`clear_protection` are unsupported — the SPD3303X
has no software OVP/OCP command). `set_track_mode()` selects
independent/series/parallel CH1+CH2 coupling.

**Also likely compatible:**
- SPD3303X-E, SPD3303C

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Keysight E36300 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightE36313A` | E36313A | E36300 Series (Triple Output) | `KEYSIGHT`/`AGILENT` + (`E3631`, `E36313`, `E3633`) |

Uses the SCPI-99 channel-list syntax `(@<chanlist>)` shared with other
Keysight instruments -- every setpoint/measurement command takes an
explicit `(@<n>)` argument, distinct from the BK Precision 9130B's
channel-select round-trip and the Rigol/Siglent `CH<n>` prefix style.
`set_output_pairing()` is E36300-specific (OFF/series/parallel CH1+CH2).

**Also likely compatible:**
- E36311A, E36312A

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Korad KA3005P

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KoradKA3005P` | KA3005P | Korad flat ASCII (non-SCPI) | `KORAD` |

**Not a SCPI instrument.** Speaks Korad's own flat ASCII command set
over serial (9600 8N1, no line termination, no error queue, no
`*RST`/`*CLS`/`*OPC?`) -- this driver overrides `check_errors`,
`sync_config`, and `clear_status` as no-ops and skips the
`SYST:ERR?` round-trip in `safe_send`/`query_ascii` entirely.
`preset()` emulates a reset by forcing output off, 0V, 0A limit since
the hardware has no reset command. `get_output()` decodes bit 6 of the
single-byte `STATUS?` response. Widely cloned by Tenma, RS, Velleman,
and Stamos under different model numbers with an identical protocol.

> [!WARNING]
> Not yet verified against real hardware. If you hit a protocol error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### GW Instek GPP Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `GWInstekGPP4323` | GPP-4323 | GPP Series (4 independent channels) | `GW`/`GW INSTEK` + `GPP` |

The GPP dialect puts the channel number directly as a numeric suffix
on the keyword itself (`SOURce2:VOLTage`, `OUTPut2:STATe`,
`MEASure2:CURRent?`), distinct from every other multi-channel PSU
dialect already in this library (Keysight `(@<n>)`, Rigol/Siglent
`CH<n>:` prefix, BK Precision channel-select round-trip). Channel 1's
suffix may be omitted on real hardware but this driver always sends it
explicitly for clarity. `set_series_mode()`/`set_parallel_mode()` link
CH1+CH2 (and CH3+CH4 where present).

**Also likely compatible** (same GPP command set):
- GPP-1326, GPP-2323, GPP-3323

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Agilent/HP 6632B/6634B Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Agilent6632B` | 6632B | 663xB System DC Power Supply | `KEYSIGHT`/`AGILENT`/`HEWLETT-PACKARD`/`HP` + (`6631`, `6632`, `6633`, `6634`) |

Legacy single-channel SCPI-99 PSU family, routed through the same
Keysight/Agilent IDN branch as `Keysight34461A`/`KeysightPNA` since it
predates the Keysight brand name but shares the same SCPI lineage.
`set_autostart()` maps to `OUTP:PON:STAT {RCL0|RST}` (power-on state).

**Also likely compatible:**
- 6631B, 6633B (same programming guide, different voltage/current ranges)

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### AIM-TTi CPX400DP

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `AimTTiCPX400DP` | CPX400DP | AIM-TTi PowerFlex command set | `AIM-TTI`/`THURLBY THANDAR`/`AIMTTI` + `CPX400` |

Puts the channel number directly on the command keyword with no colon
or prefix separator (`V1 <v>`, `I2 <i>`, `OP1 {0|1}`) -- distinct from
every SCPI-99 `SOURce<n>:`-prefixed or `INST:NSEL`-selected dialect
elsewhere in this library. Measured readbacks (`V<n>O?`/`I<n>O?`) may
echo a trailing unit suffix (`"4.999V"`); the driver strips it before
parsing. `set_track_mode()` maps to `CONFIG {0|1|2}` (independent/
series/parallel).

> [!WARNING]
> Not yet verified against real hardware. If you hit a command error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Rohde & Schwarz HMP4040 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RohdeSchwarzHMP4040` | HMP4040 | HMP Series (4 independent channels) | `HAMEG`/`ROHDE`/`ROHDE&SCHWARZ` + `HMP` |

Channels are selected via `INST:NSEL {1..4}` and then addressed with
plain `VOLT`/`CURR`/`OUTP` commands -- the same select-then-command
shape as `BKPrecision9130B`, distinct from the GW Instek GPP's
numeric-suffix-on-keyword dialect. `set_global_output()` maps to
`OUTP:GEN {ON|OFF}`, the master enable for channels armed via
`OUTP:SEL` (not wired up individually here). `clear_protection()`
disables the fuse-link coupling (`FUSE:STAT OFF`) since the HMP series
has no separate OVP/OCP trip-clear command.

**Also likely compatible** (same SCPI dialect, fewer channels):
- HMP2020, HMP2030, HMP4030

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Ametek Sorensen SG Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SorensenSG` | SG Series | SG/SGA/SGX Series (core PSU subsystem) | `SORENSEN` |

Standard SCPI-99 `:SOURce`/`:OUTPut`/`:MEASure` subsystem, directly
comparable to `KeysightE36313A`/`RigolDP832`. The Sorensen-specific
`:PROGram` subsystem for stored multi-step voltage/current sequences
is intentionally **not implemented** in this initial driver -- it is a
genuinely new interaction pattern (triggered sequence playback) not
present in any other `PowerSupply` driver in this library, and is left
for a future pass.

**Also likely compatible:**
- SGA, SGX series (same core SCPI subsystem; `:PROGram` support varies)

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### BK Precision 1685B/1687B/1688B Series

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `BKPrecision1685B` | 1685B | BK Precision flat ASCII (non-SCPI) | `B&K`/`BK PRECISION` + (`1685`, `1687`, `1688`) |

**Not a SCPI instrument.** Speaks the same flat ASCII command family
as `KoradKA3005P` (`VSET1:<v>`, `ISET1:<i>`, `OUT1`/`OUT0`) over a USB
virtual COM port -- distinct from the SCPI-based `BKPrecision9130B`
driver, which targets BK Precision's other, multi-channel product
line. `check_errors`, `sync_config`, and `clear_status` are no-ops;
`preset()` emulates a reset (no hardware `*RST`) by forcing output
off, 0V, 0A limit.

**Also likely compatible:**
- 1687B, 1688B (same programming manual, different voltage/current ranges)

> [!WARNING]
> Not yet verified against real hardware. If you hit a protocol error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## AC Power Sources

### Keysight AC6800B Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightAC6800B` | AC6800B Series | AC6800B Series Programming Guide | `KEYSIGHT` + `AC68` |

New `ACPowerSource` base class (`src/instrumation/drivers/base.py`) --
every `PowerSupply` driver in this library is DC-only (a single
voltage/current setpoint with no frequency/phase/output-mode concept),
which does not fit an AC source needing frequency programming and an
explicit AC/DC/AC+DC output mode. Covers voltage/frequency setpoints
(`SOURce:VOLTage`/`:FREQuency`), output mode select
(`SOURce:VOLTage:MODE {AC|DC|AC+DC}`), output on/off, true-RMS
voltage/current/power measurement (`MEASure:VOLTage:AC?`/
`:CURRent:AC?`/`:POWer:AC?`), OVP/OCP, and DC offset (for `AC+DC` mode).
Registered under a new `"ACPSU"` driver type to avoid conflating it
with the DC-only `"PSU"` category.

Per issue #192's scope, transient/waveform-step programming and
arbitrary-waveform output are **not implemented** in this initial
driver -- left as a follow-up, consistent with how `SorensenSG`
deferred its `:PROGram` subsystem.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## Electronic Loads

### Siglent SDL1000X

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDL1000X` | SDL1000X | SDL1000X Series | `SIGLENT` + `LOAD` |

**Also likely compatible:**
- SDL1020X, SDL1030X, SDL1060X

### BK Precision 8600 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `BKPrecision8600` | 8600 | 8600 Series | `B&K`/`BK PRECISION` + (`8600`, `8601`, `8602`, `8610`, `8612`, `8614`, `8620`) |

Not yet validated against real hardware. Supports CC/CV/CR/CP modes,
OVP/OCP/OPP protection, and BK-specific battery discharge test mode
(`set_battery_test_mode`, `set_battery_cutoff_voltage`,
`get_battery_test_capacity`). List-mode and transient-stepping
programming from the 8600 Series manual are not yet implemented.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Rigol DL3000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RigolDL3021` | DL3021 | DL3000 Series | `RIGOL` + `DL3` |

Supports CC/CV/CR/CP modes and battery discharge test mode
(`set_battery_test_mode`, `get_battery_test_capacity`,
`get_watt_hours`, `get_discharging_time`). Unlike the BK Precision
8600, the DL3000 series has no software OVP/OCP/OPP trip-point
subsystem in its base command set — front-panel OCP/OPP are test
*modes*, not simple protection levels — so `set_ovp`/`set_ocp`/
`set_opp`/`clear_protection` log an unsupported-feature warning here.

**Also likely compatible** (same DL3000 command set):
- DL3031, DL3031A

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### ITECH IT8500+ Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `ItechIT8512Plus` | IT8512+ | IT8500+ Series | `ITECH` + `IT85` |

Supports CC/CV/CR/CP modes plus `CURRent:PROTection`/`POWer:PROTection`
(OCP/OPP trip levels) and a simulated short-circuit input
(`set_short_circuit`). The IT8500+ series has no dedicated software OVP
trip-point command in its base command set, so `set_ovp`/
`clear_protection` log an unsupported-feature warning here.

**Also likely compatible** (same IT8500+ command set):
- IT8511+, IT8513+, IT8511A+, IT8512A+, IT8513A+

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Chroma 63200A Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Chroma63200A` | 63200A series | 63200A Series (High Power) | `CHROMA` + `632` |

The most distinctive load dialect in this library: a single `MODE`
mnemonic encodes BOTH the operating mode and measurement range
(`MODE CCH` = CC High range, `MODE CVL` = CV Low range, etc.).
`set_mode()` always selects the **High**-range variant as the safest
default for an unknown DUT — send `write("MODE CCL")`/`"MODE CCM"`
directly for Low/Middle range. Setpoints use the `<FUNC>:STATic:L1`
level-1 static value (the front panel's "A" state); the `L2` ("B"
state) and slew-rate parameters are not wired up. No dedicated
software OVP/OCP/OPP trip-level commands exist — OCP/OPP are
selectable `MODE`s, not settable protection levels — and there is no
direct `MEASure:RESistance?` query, so those methods log an
unsupported-feature warning.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Prodigit 3311F

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Prodigit3311F` | 3311F | 3310F Series plug-in module | `PRODIGIT` + (`3311`, `3310`) |

The 3311F is a plug-in module hosted in a 3302F mainframe chassis, not
a standalone load -- every command is prefixed with a `CHAN<n>` slot
select (default slot 1, override via `slot=` on any method), an extra
addressing layer beyond standalone loads like `SiglentSDL1000X` or
`ItechIT8512Plus`. The CC/CV/CR/CP command shape itself
(`MODE:CC`/`CURR <a>`/`LOAD ON`/`MEAS:VOLT?`) is otherwise directly
comparable.

> [!WARNING]
> Not yet verified against real hardware. If you hit a command error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## Lock-In Amplifiers

New instrument category (issue #204). `LockInAmplifier` is a new
abstract base in `drivers/base.py`; `"LOCKIN"` is a new canonical
`driver_type` key registered in `factory.KNOWN_DRIVER_TYPES`, with a
`SimulatedLockInAmplifier` registered for SIM mode.

### Stanford Research Systems SR830

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SRSSR830` | SR830 | SRS terse mnemonics (non-SCPI-subtree) | `STANFORD` + `SR830` |

Like the SRS DS345, uses terse colon-free command mnemonics (`FREQ`,
`PHAS`, `SLVL`, `SENS`, `OFLT`, `HARM`) rather than a
`:SOURce:*`/`:SENSe:*` subtree. Sensitivity and time-constant values
are indexed by integer code, not physical units directly --
`set_sensitivity()`/`set_time_constant()` accept a physical value and
round it to the nearest supported code. `measure_xy()`/
`measure_r_theta()` use `SNAP?` to read multiple parameters at a
single instant, avoiding the time skew that separate `OUTP?` queries
would introduce for a fast time constant. Roadmap #180.

> [!WARNING]
> Not yet verified against real hardware. If you hit a command error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## LCR Meters

New instrument category (issue #204). `LCRMeter` is a new abstract
base in `drivers/base.py`; `"LCR"` is a new canonical `driver_type`
key registered in `factory.KNOWN_DRIVER_TYPES`, with a
`SimulatedLCRMeter` registered for SIM mode.

### Keysight E4980A/AL

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightE4980A` | E4980A | E4980A/AL Precision LCR Meter | `KEYSIGHT`/`AGILENT` + `E4980` |

`set_measurement_function()` selects the impedance parameter type
(`CPD`, `CPQ`, `CSD`, `LSD`, `RX`, `ZTD`, etc.); `measure()` returns a
`(primary, secondary)` tuple, e.g. capacitance and dissipation factor
for `CPD`. `set_bias_voltage`/`set_bias_state` control the DC bias
source.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Hioki IM3536

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `HiokiIM3536` | IM3536 | IM3523/IM3533/IM3536/IM3570/IM3590 family | `HIOKI` + `IM35` |

SCPI-style command set shared across the IM35xx/IM3570/IM3590
family. `:FREQuency`/`:FREQuency?` confirmed against Hioki's own
PLC-integration examples; parameter-type selection and measurement
readback follow the same `:FUNC:IMP`/`:MEASure?` shape as the
Keysight E4980A LCR meter class.

> [!WARNING]
> Best-effort: the full IM3536 command reference requires a
> Hioki-issued LCR Application Disc not published as a standalone
> PDF. Not yet verified against real hardware -- prefer `"GENERIC"`
> passthrough or file an issue with the failing command.

---

## Frequency Counters

### Keysight 53230A

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Keysight53230A` | 53230A | 53230A/53220A Universal Counter | `KEYSIGHT`/`AGILENT`/`HP` + (`53230`, `53220`, `53181`) |

**Also likely compatible:**
- 53220A (350 MHz), 53230A (350 MHz, 12 digits/s), 53181A (225 MHz, RF counter predecessor)

> [!NOTE]
> Prior to issue #204, this driver had no explicit IDN branch in
> `factory.py` and relied on the single-registered-candidate fallback;
> now that a second `"COUNTER"` driver (`FlukePM6690`) is registered,
> an explicit `KEYSIGHT`/`AGILENT`/`HP` + model-number branch is required.

### Fluke PM6690

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `FlukePM6690` | PM6690 | PM6690 native SCPI | `FLUKE` + `PM6690` |

The PM6690 has two GPIB personalities: a native SCPI mode (targeted
here) with a command set optimized for its own capabilities, and a
compatible mode that emulates a Keysight/HP 53131A/53132A. Native
mode uses the same standard SCPI-99 counter subsystem shape as
`Keysight53230A`.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## USB Power Sensors

New instrument category (issue #204). `"SENSOR"` is a new canonical
`driver_type` key registered in `factory.KNOWN_DRIVER_TYPES`.

### Keysight U2000 Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightU2000` | U2004A | U2000 Series USB Power Sensor | `KEYSIGHT`/`AGILENT`/`HP` + (`U2000`, `U200`) |

Headless USBTMC-only sensor (no front panel); standard SCPI power-
sensor command set (`FETCh?`/`MEASure?`, `SENSe:FREQuency`,
`SENSe:CORRection:GAIN2` for external gain/loss offset,
`CALibration:ZERO`). `set_frequency()` sets the CW frequency used for
the sensor's internal cal-factor table lookup, not an output.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Rohde & Schwarz NRP-Z Series

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `RohdeSchwarzNRPZ` | NRP-Z21 | NRP-Z Series USB Power Sensor | `HAMEG`/`ROHDE`/`ROHDE&SCHWARZ` + `NRP` |

Headless USB sensor (no front panel), similar in shape to the
Keysight U2000 series but with R&S-specific correction subsystems:
`SENSe:CORRection:DCYCle` for pulse-power duty-cycle correction and
`SENSe:CORRection:SPDevice` for S-parameter device correction.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

---

## RF Switches

New instrument category (issue #204). `"SWITCH"` is a new canonical
`driver_type` key registered in `factory.KNOWN_DRIVER_TYPES`.

### Mini-Circuits RC/RFS Series

| Driver | Purpose | Auto-Detect IDN Keywords |
|:---|:---|:---|
| `MiniCircuitsRCSwitch` | RF switch matrix control (RC-4SPDT, RC-1SP4T, RC-2SP4T, etc.) | `MINI-CIRCUITS`/`MINICIRCUITS` |

**Not a SCPI instrument.** Uses Mini-Circuits' own flat ASCII command
set over USB/Ethernet: `SET{switch}={0|1}` for individual SPDT
switches (A-H), `SP{n}T:STATE:PORT {port}` for SPnT port selection.
Roadmap #174.

> [!WARNING]
> Could not be verified against Mini-Circuits' official Programming
> Manual PDF at write time (host was unreachable from this
> environment). Confirmed only via third-party summaries of the
> `SET[switch]=[state]` command. Not yet verified against real
> hardware -- prefer `"GENERIC"` passthrough or file an issue with
> the failing command.

---

## Power Analyzers

New instrument category (issue #204). `"POWERMETER"` is a new
canonical `driver_type` key registered in
`factory.KNOWN_DRIVER_TYPES`.

### Yokogawa WT310 Series

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `YokogawaWT310` | WT310 | WT310/WT310HC/WT332/WT333 | `YOKOGAWA` + `WT3` |

Uses Yokogawa's `:NUMeric[:NORMal]:ITEM<x>` output-item configuration
model: each numeric output slot (1-255) is assigned a function
(`U`=voltage, `I`=current, `P`=active power, `S`=apparent, `Q`=reactive,
`LAMBda`=power factor) and element (1-3 for multi-element models),
then `:NUMeric[:NORMal]:VALue?` reads back all configured items as a
single comma-separated response -- distinct from a per-quantity
`MEASure:<FUNC>?` query used by DMM-style instruments.
`measure_voltage`/`measure_current`/`measure_active_power`/
`measure_power_factor` are convenience wrappers that configure slot 1
and read it back in one call.

> [!WARNING]
> Not yet verified against real hardware. If you hit an SCPI error,
> prefer `"GENERIC"` passthrough or file an issue with the failing
> command.

### Tektronix PA1000

| Driver | Validated Model | Command Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `TektronixPA1000` | PA1000 | Community-verified quirky SCPI | `TEKTRONIX` + `PA1000` |

Tektronix's published PA1000 manual omits the SCPI programming
chapter; this driver is built from community-verified, hands-on
PyVISA usage notes and documents several real quirks:

- Every command requires the leading `:` root designator.
- Semicolon-separated command chaining is **not** supported.
- No `*OPC?` support -- `wait_ready()` sleeps a fixed 0.5s settle
  time instead of polling; `*RST` needs a fixed 5s delay.
- Uses `:SEL:*` to choose which readings appear in `:FRD?` output,
  then `:FRD?` fetches them as a comma-separated list -- `clear_selection()`
  + `select_*()` + `fetch_readings()` compose into the
  `measure_voltage_rms`/`measure_current_rms`/`measure_active_power`/
  `measure_frequency` convenience wrappers.
- Non-LXI-compliant Ethernet: raw socket on port 5025, no VXI-11.

> [!WARNING]
> Not yet verified against real hardware by this project. If you hit
> a command error, prefer `"GENERIC"` passthrough or file an issue
> with the failing command.

---

## GENERIC (Universal Fallback)

| Driver | Purpose | Auto-Detect IDN Keywords |
|:---|:---|:---|
| `GenericDriver` | Catch-all driver for unidentified instruments; accepts any model | none (explicit `"GENERIC"` request or unrecognized `*IDN?`) |

`"GENERIC"` is a first-class, always-registered key in
`DriverRegistry` — `get_drivers_by_type("GENERIC")` always returns
`GenericDriver` (real mode) and `SimulatedGeneric` (SIM mode). It is used
when `connect_instrument()` cannot identify an instrument, or when you
explicitly pass `driver_type="GENERIC"` to `get_instrument()`. It exposes
only generic SCPI passthrough (no typed measurement API), so it is a safe
default, never a silent DMM/SA misread — see issue #148.

---

## Summary

| Category | Drivers | Validated Models |
|:---|:---|:---|
| Oscilloscopes | 7 | DSOX2002A, DS1054Z, SDS Series, TDS Series, HMO722, SDS2102X Plus, MSO5354 |
| Spectrum Analyzers | 5 | MXA N9020A, PXA N9030A, DSA800, MS2830A, SSA3021X |
| Signal Generators | 9 | N5183B, AFG3022C, SMA100B, MG3700A, SMA100A, SDG2042X, DG4062, MFG-2120, DS345 |
| Network Analyzers | 4 | N5232A, N9913A, MS2035B, SNA5012A |
| Multimeters | 6 | 34461A, 2000, 8846A, SDM3055, DM3068, DMM6500 |
| Power Supplies | 12 | Z+100-2, 9130B, DP832, SPD3303X, E36313A, KA3005P, GPP-4323, 6632B, CPX400DP, HMP4040, SG Series, 1685B |
| AC Power Sources | 1 | AC6800B Series |
| Electronic Loads | 6 | SDL1000X, 8600, DL3021, IT8512+, 63200A, 3311F |
| Lock-In Amplifiers | 1 | SR830 |
| LCR Meters | 2 | E4980A, IM3536 |
| Frequency Counters | 2 | 53230A, PM6690 |
| RF Switches | 1 | RC-4SPDT-A18 |
| USB Power Sensors | 2 | U2004A, NRP-Z21 |
| Power Analyzers | 2 | WT310, PA1000 |
| **Total** | **56** | |

> [!TIP]
> If your model shares a SCPI command set with one of the listed
> families, the existing driver will almost certainly work. Try
> `"AUTO"` discovery first — the factory matches on `*IDN?` keywords.
