from anthemav.protocol import ALM_NUMBER, LOOKUP
from anthemav import AVR
from unittest.mock import patch


def test_default_alm_list():
    avr = AVR()
    almList = avr.audio_listening_mode_list
    assert almList is not None
    assert len(almList) == 15


def test_restricted_alm_list():
    avr = AVR()
    avr._IDM = "MRX 520"
    almList = avr.audio_listening_mode_list
    assert almList is not None
    assert len(almList) == 8


def test_set_alm_text():
    avr = AVR()
    with patch.object(avr, "command") as mock:
        avr.audio_listening_mode_text = "Neo Music"
        mock.assert_called_once_with("Z1ALM06")


def test_all_alm_matchnumber():
    for alm in list(LOOKUP["Z1ALM"].values())[1:]:
        assert alm in ALM_NUMBER


def test_power_on_force_refresh():
    avr = AVR()
    with patch.object(avr, "query") as mock:
        with patch.object(avr, "_loop"):
            avr._parse_message("Z1INP01;")
            mock.assert_called_once_with("Z1POW")


def test_mute_force_refresh():
    avr = AVR()
    with patch.object(avr, "query") as mock:
        avr.mute = True
        mock.assert_called_once_with("Z1MUT")


def test_populate_input():
    avr = AVR()
    with patch.object(avr, "query") as mock:
        avr._populate_inputs(2)
        mock.assert_any_call("ISN01")
        mock.assert_called_with("ISN02")
