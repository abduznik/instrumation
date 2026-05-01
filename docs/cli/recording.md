# Recording and Replaying

The CLI is the easiest way to generate "Golden Master" files for your digital twin simulations.

## Creating a Recording

The `record` command opens an interactive SCPI shell. Every command you send and every response received is recorded into a JSON file.

```bash
instrumation record "GPIB0::7::INSTR" DMM production_dmm.json
```

### Interactive Commands
Inside the recording shell, you can:
1.  **Send SCPI**: Type `*IDN?` or `MEAS:VOLT:DC?`.
2.  **Wait**: Use `wait 1.0` to simulate a delay.
3.  **Finish**: Type `quit` or `exit` to save and close.

## Replaying the Session

Once you have a `.json` file, you can "measure" against it as if it were a real instrument:

```bash
instrumation measure "replay://production_dmm.json" DMM measure_voltage
```

This is extremely useful for:
- **Offline Development**: Writing your Python scripts at home.
- **Regression Testing**: Ensuring your code still works correctly with "real" data from the lab.
- **Deterministic CI**: Running tests in GitHub Actions without physical hardware.
