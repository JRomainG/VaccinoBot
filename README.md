# VaccinoBot

A Telegram bot to automatically find available vaccines in France using Doctolib.

## Installation

VaccinoBot requires Python 3.7 or newer.

Dependencies can be installed using pip:

```bash
$ pip3 install -r requirements.txt
```

## Usage

### Configuration

#### Telegram

To use the Telegram transport, you first need to create a [Telegram bot](https://core.telegram.org/bots). For this, you need to talk to [BotFather](https://t.me/botfather) and issue the `/newbot` command. Once you are done, BotFather will provide you with a token, save it in a `secret.token` file:

```bash
$ echo 'your_secret_token' > secret.token
```

Once this is done, you can invite your bot to a Telegram group or channel and retreive its chat id. After inviting the bot, you can find the chat ID from the `https://api.telegram.org/bot{token}/getUpdates` URL (replacing `{token}` with your bot's token).

#### Doctolib

First start by building a list of vaccination centers close to you (e.g. using the [covidtracker website](https://vitemadose.covidtracker.fr/)) and add them to the `LAB_URLS` list in `tools/generate_lab_file.py`.

You can then run the `tools/generate_lab_file.py` script, which will create a `generated_labs.json` that you can use to configure the bot.

#### VaccinoBot

Finally, you can configure this script by creating a `profiles.ini` file. You can start by copying the `profiles.ini.example` and editing its content.

Here are the available options:

| Key                       | Type   | Description                                                                                   |
| ------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| check_interval            | int    | How often to check available slots for each lab (in seconds)                                  |
| lab_file                  | string | The path to the file containing the labs to check                                             |
| chat_id                   | string | The ID of the Telegram chat to which messages are sent                                        |
| confirm_slot_availability | bool   | Whether to perform a second request to ensure slots found are still available (default: `no`) |
| enabled                   | bool   | Whether to enable the profile or not (default: `yes`)                                         |

### Running

Simply start the script and let it run in the background:

```bash
$ python3 main.py
```

By default, the logger will print messages informing you each time slots are checked for a vaccination center, as well as each time a slot is found. You can tweak this by editing the log level in `main.py`.

### Systemd service

If you use systemd, you can run the bot as a service. Here is an example configuration file:

```
[Unit]
Description=VaccinoBot
After=network.target

[Service]
User=bot
Nice=1
KillMode=mixed
SuccessExitStatus=0 1
ProtectHome=true
ProtectSystem=full
PrivateDevices=true
NoNewPrivileges=true
WorkingDirectory=/var/bots/
ExecStart=/usr/bin/python3 /var/bots/VaccinoBot/main.py
#ExecStop=

[Install]
WantedBy=multi-user.target
```

You can save it as `/etc/systemd/system/VaccinoBot.service`, and then start it:

```bash
$ systemctl daemon-reload
$ systemctl enable VaccinoBot
$ systemctl start VaccinoBot
```

## Contributing

As is, this bot only supports the Doctolib backend and the Telegram transport. This could be extended to support other backends (e.g; KelDoc, Maiia, ...) and transports (SMTP, Signal, ...).

The bot also explicitly checks for first shots available in the next 24 hours, as these are the ones available to the whole population (for now).

If you wish to change one of these behaviors, or add other features, pull requests are welcome!
