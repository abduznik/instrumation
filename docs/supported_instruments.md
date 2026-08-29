# Supported Instruments

This page lists all instrument models that Instrumation supports — both the
specific models that have been validated and the broader families that share
the same SCPI command set.

---

## Oscilloscopes

### Keysight InfiniiVision

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `KeysightInfiniiVision` | DSOX2002A | DSOX/MSOX 2000–6000 Series | `DSO-X`, `MSO-X`, `DSOX`, `MSOX` |

**Also likely compatible** (same InfiniiVision SCPI set):
- DSOX1002A–DSOX1004A, DSOX2004A–DSOX2012A, DSOX3002T–DSOX3054T
- MSOX1002A–MSOX1004A, MSOX2004A–MSOX3054T, MSOX4002A–MSOX4154A
- DSOX6002A–DSOX6054A, MSOX6002A–MSOX6054A

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

### Siglent SDS

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDS` | SDS1000 Series | SDS Series | `SIGLENT` |

**Also likely compatible:**
- SDS1002X-E, SDS1004X-E, SDS1102X-E, SDS1104X-E, SDS1202X-E, SDS1204X-E
- SDS2002X, SDS2004X, SDS2102X, SDS2104X, SDS2202X, SDS2204X

### Tektronix TDS

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `TektronixTDS` | TDS Series | Tek TDS/TPS/MDO | `TEKTRONIX` (non-AFG) |

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
- MXA N9010A (EXA), N9020A, N9021A
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

---

## Multimeters

### Keysight 34461A Truevolt

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Keysight34461A` | 34461A | Truevolt DMM | `34461`, `34460` |

**Also likely compatible:**
- 34460A (6.5 digit), 34461A (6.5 digit), 34410A (6.5 digit), 34411A (6.5 digit), 34420A (μV/μΩ)

### Keithley 2000

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Keithley2000` | 2000 | Keithley 2000 Series | `KEITHLEY` + `2000` |

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

---

## Electronic Loads

### Siglent SDL1000X

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `SiglentSDL1000X` | SDL1000X | SDL1000X Series | `SIGLENT` + `LOAD` |

**Also likely compatible:**
- SDL1020X, SDL1030X, SDL1060X

---

## Frequency Counters

### Keysight 53230A

| Driver | Validated Model | SCPI Family | Auto-Detect IDN Keywords |
|:---|:---|:---|:---|
| `Keysight53230A` | 53230A | 53230A/53220A Universal Counter | `34401`, `34410`, `53230`, `53220` |

**Also likely compatible:**
- 53220A (350 MHz), 53230A (350 MHz, 12 digits/s)

---

## Summary

| Category | Drivers | Validated Models |
|:---|:---|:---|
| Oscilloscopes | 4 | DSOX2002A, DS1054Z, SDS Series, TDS Series |
| Spectrum Analyzers | 4 | MXA N9020A, PXA N9030A, DSA800, MS2830A |
| Signal Generators | 5 | N5183B, AFG3022C, SMA100B, MG3700A, SMA100A |
| Network Analyzers | 3 | N5232A, N9913A, MS2035B |
| Multimeters | 2 | 34461A, 2000 |
| Power Supplies | 1 | Z+100-2 |
| Electronic Loads | 1 | SDL1000X |
| Frequency Counters | 1 | 53230A |
| **Total** | **21** | |

> [!TIP]
> If your model shares a SCPI command set with one of the listed
> families, the existing driver will almost certainly work. Try
> `"AUTO"` discovery first — the factory matches on `*IDN?` keywords.
