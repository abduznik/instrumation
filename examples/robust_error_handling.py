from instrumation.factory import get_instrument
from instrumation.exceptions import InstrumentTimeout, ConnectionLost, InstrumentError

def measure_with_retry(address, retries=3):
    """
    Attempts to measure voltage with a robust retry mechanism using unified exceptions.
    """
    attempt = 0
    while attempt < retries:
        try:
            print(f"Attempt {attempt + 1}: Connecting to DMM...")
            with get_instrument(address, "DMM") as dmm:
                res = dmm.measure_voltage()
                print(f"Measurement Success: {res}")
                return res
        except InstrumentTimeout:
            print("Timeout occurred. Retrying...")
            attempt += 1
        except ConnectionLost:
            print("Connection lost. Check cables. Aborting.")
            break
        except InstrumentError as e:
            print(f"General instrument error: {e}. Retrying...")
            attempt += 1
    
    print("Failed to complete measurement.")
    return None

if __name__ == "__main__":
    measure_with_retry("TCPIP0::127.0.0.1::inst0::INSTR")
