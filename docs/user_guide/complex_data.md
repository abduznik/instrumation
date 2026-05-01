# Complex Data & Multi-Channel Support

Instrumation is designed to handle advanced RF measurements, including Vector Network Analysis (VNA) and Mixed Signal Oscilloscope (MSO) traces.

## Complex (I/Q) Data

The `MeasurementResult` object supports complex numbers and `numpy` arrays. This is essential for Phase/Magnitude traces in VNAs.

### Working with complex traces
```python
with get_instrument(vna_addr, "VNA") as vna:
    # get_complex_trace returns a list of complex numbers
    res = vna.get_complex_trace("S21")
    
    for val in res.value:
        print(f"Real: {val.real}, Imag: {val.imag}")
```

## Multi-Channel Measurements

Measurement results can now specify a `channel` or `pod` (for digital signals).

```python
res = MeasurementResult(value=5.0, unit="V", channel=1)
print(res) # Output: 5.0 V [CH 1] (OK) @ ...
```

## NumPy Integration

If `numpy` is installed, `MeasurementResult` can store high-performance arrays directly in the `value` field. When converted to JSON (via `to_json()`), these arrays are automatically serialized to lists.

```python
import numpy as np
trace = np.sin(np.linspace(0, 10, 100))
res = MeasurementResult(value=trace, unit="V")

# JSON output is ready for the VFP or data logging
print(res.to_json())
```
