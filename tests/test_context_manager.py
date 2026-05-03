import os
from instrumation.factory import get_instrument

def test_context_manager_connect_disconnect():
    """Test that the context manager correctly connects and disconnects."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    
    # We'll use a SimulatedMultimeter for testing
    with get_instrument("DUMMY", "DMM") as dmm:
        assert dmm.connected is True
        # Identification should work
        assert "SIM" in dmm.get_id()
    
    # After exiting the context, it should be disconnected
    assert dmm.connected is False

def test_context_manager_exception_handling():
    """Test that disconnect is called even if an exception occurs."""
    os.environ["INSTRUMATION_MODE"] = "SIM"
    
    dmm_ref = None
    try:
        with get_instrument("DUMMY", "DMM") as dmm:
            dmm_ref = dmm
            assert dmm.connected is True
            raise ValueError("Test Exception")
    except ValueError:
        pass
    
    assert dmm_ref is not None
    assert dmm_ref.connected is False
