import pytest
from anthemav.protocol import LOOKUP, MODEL_X20, ALM_NUMBER_x20
from anthemav import AVR
from unittest.mock import call, patch


@pytest.mark.asyncio
class TestProtocol:
    def test_default_alm_list(self):
        avr = AVR()
        avr.set_model_command("MRX 1120")
        almList = avr.audio_listening_mode_list
        assert almList is not None
        assert len(almList) == 15

    async def test_restricted_alm_list(self):
        avr = AVR()
        await avr._parse_message("IDMMRX 520")
        almList = avr.audio_listening_mode_list
        assert almList is not None
        assert len(almList) == 8

    def test_set_alm_text(self):
        avr = AVR()
        avr.set_model_command("MRX 520")
        with patch.object(avr, "command") as mock:
            avr.audio_listening_mode_text = "Neo Music"
            mock.assert_called_once_with("Z1ALM06")

    def test_all_alm_matchnumber(self):
        for alm in list(LOOKUP["Z1ALM"].values())[1:]:
            assert alm in ALM_NUMBER_x20

    async def test_power_on_force_refresh(self):
        avr = AVR()
        with patch.object(avr, "query") as mock, patch.object(avr, "_loop"):
            await avr._parse_message("Z1AIC;")
            mock.assert_called_once_with("Z1POW")

    def test_mute_force_refresh(self):
        avr = AVR()
        with patch.object(avr, "query") as mock:
            avr.zones[1].mute = True
            mock.assert_called_once_with("Z1MUT")

    def test_populate_input_x20(self):
        avr = AVR()
        with patch.object(avr, "query") as mock:
            avr._populate_inputs(2)
            mock.assert_any_call("ISN01")
            mock.assert_called_with("ISN02")

    def test_populate_input_x40(self):
        avr = AVR()
        with patch.object(avr, "query") as mock:
            avr.set_model_command("MRX 1140")
            avr._populate_inputs(2)
            mock.assert_any_call("IS1IN")
            mock.assert_any_call("IS1ARC")
            mock.assert_any_call("IS2IN")
            mock.assert_any_call("IS2ARC")

    async def test_parse_input_x40(self):
        avr = AVR()
        with patch.object(avr, "query"):
            await avr._parse_message("IS3INName")
            assert avr._input_names.get(3, "") == "Name"

    async def test_parse_arc_x40(self):
        avr = AVR()
        with patch.object(avr, "query"), patch.object(avr, "_loop"):
            avr.set_model_command("MRX 1140")
            avr.zones[1].input_number = 2
            await avr._parse_message("Z1INP2")
            await avr._parse_message("IS2ARC1")
            await avr._parse_message("IS1ARC0")
            assert avr.arc is True

    async def test_parse_arc_x20(self):
        avr = AVR()
        with patch.object(avr, "query"):
            avr.set_model_command("MRX 520")
            await avr._parse_message("Z1ARC1")
            assert avr.arc is True

    async def test_set_arc_x20(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "command") as mock:
            avr._model_series = MODEL_X20
            avr.arc = True
            mock.assert_called_once_with("Z1ARC1")

    async def test_set_arc_x40(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "query"), patch.object(
            avr, "command"
        ) as mock, patch.object(avr, "_loop"):
            avr.set_model_command("MRX 1140")
            await avr._parse_message("Z1INP3")
            avr.arc = True
            mock.assert_called_once_with("IS3ARC1")

    @pytest.mark.parametrize(
        "model,zone",
        [
            ("MRX 520", 2),
            ("MRX 1140", 2),
            ("MDX8", 4),
            ("MDX16", 8),
            ("MDA8", 4),
            ("MDA16", 8),
        ],
    )
    async def test_zone_created(self, model: str, zone: int):
        avr = AVR()
        with patch.object(avr, "query"):
            await avr._parse_message(f"IDM{model}")
            assert len(avr.zones) == zone

    async def test_power_refreshed_MDX16(self):
        avr = AVR()
        with patch.object(avr, "query") as mock:
            await avr._parse_message("IDMMDX16")
            for zone in range(1, 9):
                mock.assert_any_call(f"Z{zone}POW")
            assert call("Z9POW") not in mock.mock_calls

    async def test_input_name_queried_for_MDX16(self):
        avr = AVR()
        with patch.object(avr, "query") as mock, patch.object(avr, "transport"):
            await avr._parse_message("IDMMDX16")
            await avr.refresh_all()
            for input_number in range(1, 13):
                mock.assert_any_call(f"ISN{input_number:02d}")

    async def test_input_name_queried_for_MDX8(self):
        avr = AVR()
        with patch.object(avr, "query") as mock, patch.object(avr, "transport"):
            await avr._parse_message("IDMMDX8")
            await avr.refresh_all()
            for input_number in range(1, 13):
                if input_number in [1, 2, 3, 4, 9]:
                    mock.assert_any_call(f"ISN{input_number:02d}")
                else:
                    assert call(f"ISN{input_number:02d}") not in mock.mock_calls

    async def test_pvol_x40(self):
        avr = AVR()
        with patch.object(avr, "query"):
            await avr._parse_message("IDMMRX 740")
            await avr._parse_message("Z2PVOL51")
            assert avr.zones[2].volume == 51

    async def test_zone2_power(self):
        avr = AVR()
        with patch.object(avr, "refresh_zone") as refreshmock, patch.object(
            avr, "_loop"
        ):
            await avr._parse_message("IDMMRX 740")
            assert avr.zones[2].power is False
            await avr._parse_message("Z2POW1")
            refreshmock.assert_called_with(2)
            assert avr.zones[2].power is True
            assert avr._device_power is True

    async def test_attenuation(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "query"):
            await avr._parse_message("IDMMRX 740")
            assert avr.zones[1].attenuation == -90
            await avr._parse_message("Z1VOL-42")
            assert avr.zones[1].attenuation == -42

    async def test_volume_x20(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "query"):
            await avr._parse_message("IDMMRX 1120")
            assert avr.zones[1].volume == 0
            await avr._parse_message("Z1VOL-42")
            assert avr.zones[1].volume == 53

    async def test_zone_set_volume_as_percentage_x20(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "command") as mock:
            avr._model_series = "x20"
            assert avr.zones[1].volume_as_percentage == 0
            avr.zones[1].volume_as_percentage = 0.53
            mock.assert_any_call("Z1VOL-42")

    async def test_set_volume_as_percentage_x20(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "command") as mock:
            avr._model_series = "x20"
            assert avr.volume_as_percentage == 0
            avr.volume_as_percentage = 0.53
            mock.assert_any_call("Z1VOL-42")

    async def test_set_volume_as_percentage_x40(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "command") as mock:
            avr._model_series = "x40"
            avr.volume_as_percentage = 0.53
            mock.assert_any_call("Z1PVOL53")

    async def test_set_volume_as_percentage_mdx(self):
        avr = AVR()
        avr._device_power = True
        with patch.object(avr, "command") as mock:
            avr._model_series = "mdx"
            avr.volume_as_percentage = 0.53
            mock.assert_any_call("Z1VOL53")

    async def test_refresh_zone_x40(self):
        avr = AVR()
        with patch.object(avr, "query") as mock, patch.object(avr, "transport"):
            await avr._parse_message("IDMMRX 740")
            await avr.refresh_zone(2)
            mock.assert_any_call("Z2POW")
            mock.assert_any_call("Z2INP")
            mock.assert_any_call("Z2PVOL")
            mock.assert_any_call("Z2VOL")
            mock.assert_any_call("Z2MUT")

    async def test_refresh_zone_x20(self):
        avr = AVR()
        with patch.object(avr, "query") as mock, patch.object(avr, "transport"):
            await avr._parse_message("IDMMRX 720")
            await avr.refresh_zone(2)
            mock.assert_any_call("Z2POW")
            mock.assert_any_call("Z2INP")
            mock.assert_any_call("Z2VOL")
            mock.assert_any_call("Z2MUT")
            assert call("Z2PVOL") not in mock.mock_calls

    async def test_device_power_off(self):
        avr = AVR()
        with patch.object(avr, "refresh_zone") as refreshmock, patch.object(
            avr, "_loop"
        ):
            await avr._parse_message("IDMMRX 740")
            await avr._parse_message("Z2POW1")
            refreshmock.assert_called_with(2)
            assert avr._device_power is True
            await avr._parse_message("Z1POW1")
            assert avr._device_power is True
            await avr._parse_message("Z1POW0")
            assert avr._device_power is True
            await avr._parse_message("Z2POW0")
            assert avr._device_power is False

    async def test_zone_input_format_mrx(self):
        avr = AVR()
        avr._model_series = "x40"
        avr._device_power = True
        await avr._parse_message("Z1VIR6")
        await avr._parse_message("Z1AINDTS Master Audio")
        assert avr.zones[1].input_format == "1080i50 DTS Master Audio"

    def test_zone_input_format_mdx(self):
        avr = AVR()
        avr._model_series = "mdx"
        avr._device_power = True
        assert avr.zones[1].input_format == ""

    async def test_input_format_mrx_zone2(self):
        avr = AVR()
        avr._model_series = "x40"
        avr._device_power = True
        avr.set_zones("MRX 540")
        await avr._parse_message("Z1VIR6")
        await avr._parse_message("Z1AINDTS Master Audio")
        assert avr.zones[2].input_format == ""

    @pytest.mark.parametrize(
        "model,expected", [("MRX 520", True), ("MRX 740", True), ("MDX8", False)]
    )
    async def test_support_zone1_MRX(self, model: str, expected: bool):
        avr = AVR()
        with patch.object(avr, "query"):
            avr._device_power = True
            avr.set_model_command(model)
            avr.set_zones(model)
            assert avr.zones[1].support_audio_listening_mode == expected
            assert avr.zones[2].support_audio_listening_mode is False
            assert avr.zones[1].support_profile == expected
            assert avr.zones[2].support_profile is False

    @pytest.mark.parametrize(
        "model,expected", [("MRX 520", True), ("MRX 1140", False), ("MDX8", False)]
    )
    async def test_support_attenuation(self, model: str, expected: bool):
        avr = AVR()
        with patch.object(avr, "query"):
            avr._device_power = True
            avr.set_model_command(model)
            avr.set_zones(model)
            assert avr.zones[1].support_attenuation == expected
            assert avr.zones[2].support_attenuation == expected
