"""Regression tests for GH #161: close_rm() API for the global VISA resource manager."""
import unittest
from unittest.mock import MagicMock, patch

import instrumation.factory as factory


class TestCloseRm(unittest.TestCase):
    def tearDown(self):
        factory._GLOBAL_RM = None

    def test_close_rm_noop_when_never_created(self):
        factory._GLOBAL_RM = None
        factory.close_rm()  # must not raise
        self.assertIsNone(factory._GLOBAL_RM)

    @patch("instrumation.factory.pyvisa.ResourceManager")
    def test_close_rm_closes_and_resets_singleton(self, mock_rm_cls):
        mock_rm = MagicMock()
        mock_rm_cls.return_value = mock_rm

        rm1 = factory.get_rm()
        self.assertIs(rm1, mock_rm)

        factory.close_rm()

        mock_rm.close.assert_called_once()
        self.assertIsNone(factory._GLOBAL_RM)

    @patch("instrumation.factory.pyvisa.ResourceManager")
    def test_get_rm_after_close_creates_fresh_manager(self, mock_rm_cls):
        first_rm = MagicMock()
        second_rm = MagicMock()
        mock_rm_cls.side_effect = [first_rm, second_rm]

        rm1 = factory.get_rm()
        factory.close_rm()
        rm2 = factory.get_rm()

        self.assertIs(rm1, first_rm)
        self.assertIs(rm2, second_rm)
        self.assertEqual(mock_rm_cls.call_count, 2)


if __name__ == "__main__":
    unittest.main()
