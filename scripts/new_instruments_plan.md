# New Instrument Rollout Plan (working doc, not committed to release notes)

Tracking issue: created via `gh issue create` (see ROADMAP.md link once filed).

Status legend: `[ ]` pending &nbsp; `[~]` manual fetched &nbsp; `[x]` driver + tests + docs done

Process per instrument:
1. WebSearch/WebFetch official programming/SCPI manual (or closest public reference).
2. Save manual text/notes to scratchpad `manuals/<slug>.md`.
3. Implement real driver in `src/instrumation/drivers/<vendor>.py` (register with `@register_driver`).
4. Implement simulated twin in `drivers/simulated.py`.
5. Wire IDN auto-routing in `factory.py`.
6. Add unit tests in `tests/test_<vendor>_<model>.py` (mocked VISA, mirrors existing style).
7. Update `docs/supported_instruments.md` compatibility table + summary counts.
8. Commit (no co-author trailer).

## Final list (34 instruments)

### Multimeters (3)
1. [x] Siglent SDM3055 — 5.5-digit bench DMM
2. [ ] Rigol DM3068 — 6.5-digit DMM
3. [ ] Keithley DMM6500 — graphical sampling DMM

### Power Supplies (5)
4. [ ] Rigol DP832 — triple-output PSU
5. [ ] Siglent SPD3303X — triple-output PSU
6. [ ] Keysight E36313A — triple-output PSU
7. [ ] Korad KA3005P — single-output hobbyist PSU
8. [ ] GW Instek GPP-4323 — quad-output PSU (roadmap #171)

### Electronic Loads (3)
9. [ ] Rigol DL3021 — programmable DC load
10. [ ] ITECH IT8512+ — DC electronic load
11. [ ] Chroma 63200 series — DC electronic load

### Oscilloscopes (4)
12. [ ] Siglent SDS2000X Plus
13. [ ] Rigol MSO5000 series
14. [ ] Keysight DSOX1204G
15. [ ] PicoScope 2208B (USB scope, PicoSDK-style)

### Spectrum Analyzers (3)
16. [ ] Siglent SSA3000X
17. [ ] Rigol DSA875
18. [ ] Keysight N9010B EXA

### Signal/Function Generators (4)
19. [ ] Siglent SDG2000X AWG
20. [ ] Rigol DG4000 series AWG
21. [ ] GW Instek MFG-2000 (roadmap #176)
22. [ ] SRS DS345

### Network/Impedance Analyzers (3)
23. [ ] Siglent SNA5000A VNA
24. [ ] Keysight E4980A LCR meter
25. [ ] Hioki IM3536 LCR meter

### Lock-in Amplifiers (2)
26. [ ] Stanford Research Systems SR830 (roadmap #180)
27. [ ] Zurich Instruments MFLI

### Frequency Counters (2)
28. [ ] Keysight 53181A
29. [ ] Fluke PM6690 counter

### RF / Sensors (3)
30. [ ] Mini-Circuits RFS RF switch matrix (roadmap #174)
31. [ ] Keysight U2004A USB power sensor
32. [ ] Rohde & Schwarz NRP-Z USB power sensor

### Power Analyzers (2)
33. [ ] Yokogawa WT310
34. [ ] Tektronix PA1000

---

Work proceeds top to bottom, one instrument at a time, fully finished
(manual -> driver -> sim -> factory routing -> tests -> docs) before moving
to the next, per user instruction. Loop continues until stopped.
