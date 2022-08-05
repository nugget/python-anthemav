"""Module containing the parser for Anthem command."""


class ParsedMessage:
    """Class containing parsed message information."""

    command: str
    value: str
<<<<<<< HEAD
    input_number: int
=======
    input_number: int | None
>>>>>>> Add support for ARC and some refactoring


def parse_message(message: str) -> ParsedMessage:
    """Try to parse a message to a ParsedMessage object."""
    return parse_x40_message(message)


def parse_x40_message(message: str) -> ParsedMessage:
    """Try to parse a message for the x40 models."""
    return parse_x40_input_message(message, "ARC")


def parse_x40_input_message(message: str, command: str) -> ParsedMessage:
    """Try to parse a message associated to a specific input for the x40 models."""
    if (
        message.startswith("IS")
        and command in message
        and len(message) >= len(command) + 4
    ):
        parsed_message = ParsedMessage()
        command_position = message.index(command)
        parsed_message.command = message[0 : command_position + len(command)]
        parsed_message.input_number = int(message[2:command_position])
        parsed_message.value = message[command_position + len(command) :]
        return parsed_message
    return None


<<<<<<< HEAD
def get_x40_input_command(self, input_number: int, command: str) -> str:
=======
def get_x40_input_command(self, input_number: int, command: str) -> str | None:
>>>>>>> Add support for ARC and some refactoring
    """Return a formatted message for a specific input."""
    if input_number > 0:
        return f"IS{self.input_number}{command}"
    return None
