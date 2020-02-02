# bluectl

![Python 3.8](https://img.shields.io/badge/Python->=3.6-blue)
![Linux platform](https://img.shields.io/badge/Platform-Linux-yellow)
![Continuous integration](https://img.shields.io/badge/build-passing-brightgreen)
![MIT license](https://img.shields.io/badge/Licence-MIT-red)
![Contributions are welcome](https://img.shields.io/badge/contributions-welcome-violet)

bluectl is simple `bluetoothctl` wrapper that manages profiles of bluetooth devices.

Main motivation for this project was to develop simple CLI tool that allows creating actual profiles of bluetooth devices with given profile name and further accessing them.

## Prerequisities

bluectl was tested on `archlinux` using `systemd` service manager and relevant bluetooth utilities:

* [bluez 5.52-2](https://www.archlinux.org/packages/extra/x86_64/bluez/)
* [bluez-utils 5.52-2](https://www.archlinux.org/packages/extra/x86_64/bluez-utils/)

## Usage

bluectl implements pairing and connecting of bluetooth devices as described on [wiki.archlinux.org](https://wiki.archlinux.org/index.php/Bluetooth).

```bluectl [subcommands: create|status|start|stop|stop-all]```

#### Subcommands

- `create`\
Creates new bluetooth profile.\
Attempts to pair chosen controller with given bluetooth device.\
If successful, profile details are stored in `/etc/bluectl/[profilename]`.

- `status`\
Shows connected and paired devices.

- `start [profile]`\
Connects selected profile.

- `stop [profile]`\
Disconnects selected profile.

- `stop-all`\
Disconnects any connected profile.

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
