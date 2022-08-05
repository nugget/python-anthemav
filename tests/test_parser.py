"""Test for parser."""
from anthemav.parser import parse_message


def test_parse_x40_arc():
    """Parse x40 model ARC command."""
    parsed_message = parse_message("IS2ARC1")
    assert parsed_message.command == "IS2ARC"
    assert parsed_message.input_number == 2
    assert parsed_message.value == "1"
