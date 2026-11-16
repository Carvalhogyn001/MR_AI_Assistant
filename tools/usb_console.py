"""Keep a POSIX USB console close from toggling modem lines and resetting the board."""


def preserve_modem_lines(connection):
    try:
        import termios
        descriptor = connection.fileno()
        attributes = termios.tcgetattr(descriptor)
        attributes[2] &= ~termios.HUPCL
        termios.tcsetattr(descriptor, termios.TCSANOW, attributes)
        return True
    except (ImportError, AttributeError, OSError, TypeError):
        return False
