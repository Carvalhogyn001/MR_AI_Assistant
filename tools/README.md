# Tools

Run `python3 tools/run_host_tests.py` to compile and run the Freenove firmware helper tests without hardware.

## Assistant and future PC manager

```sh
python3 tools/test_assistant.py
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
~/.platformio/penv/bin/python tools/device.py status
~/.platformio/penv/bin/python tools/device.py face orbit
~/.platformio/penv/bin/python tools/device.py expression happy
~/.platformio/penv/bin/python tools/device.py brightness 80
~/.platformio/penv/bin/python tools/device.py card
```

`Device` is the reusable USB client. An explicit `-p PORT` precedes the command when needed. Face/brightness change volatile device state; `card` reads controller capacity and boot-sector metadata without mounting or writing. Provider tests use synthetic in-memory responses only; they do not start a server or call paid APIs.
