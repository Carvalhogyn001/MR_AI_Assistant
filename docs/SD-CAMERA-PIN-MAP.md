# SD and Camera Pin Map

## Verified onboard microSD interface

Source: Freenove Wrover `Sketch_03.1_SDMMC_Test`.

| Function | GPIO | Interface |
| - | -: | - |
| SD command | 15 | SD MMC one bit |
| SD clock | 14 | SD MMC one bit |
| SD data 0 | 2 | SD MMC one bit |

The first MR. Robot SD firmware only mounts the card and reads metadata and the root directory. It does not create, modify, delete, rename, or format any files.

## Camera reservation

Source: Freenove Wrover `CAMERA_MODEL_WROVER_KIT` configuration.

Camera reserves GPIO 4, 5, 18, 19, 21, 22, 23, 25, 26, 27, 34, 35, 36, and 39. The verified microSD pins 2, 14, and 15 do not overlap, so SD and camera can coexist.

## Display coexistence

The connected QAPASS 1602A LCD responds at address `0x27` on GPIO 33 for SDA and GPIO 13 for SCL. Those pins do not overlap the Wrover camera reservation or the SD MMC pins. On 2026-08-09, camera initialization completed while the LCD remained wired to this relocated bus:

```text
Camera ready. Sensor PID: 0x009b
CAMERA_AP_READY ssid=MR-Robot-Camera url=http://192.168.4.1
```

The wiring conflict is resolved. The LCD character panel itself remains blank at 3.3 V and requires separate electrical diagnosis before it can provide visible status output.

GPIO 2 and GPIO 15 have boot related behavior. They are assigned to the onboard SD design and must not be reused for external circuitry.
