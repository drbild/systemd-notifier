# systemd_notifier

Send notifications (to Slack, email, etc) on `systemd` unit status
changes.  A `python` port of
[systemd_mon](https://github.com/joonty/systemd_mon/).

## Installation

`pip install systemd-notifier`

## Usage

`systemd-notifier -c <yaml-config-file>`

or

`systemctl start systemd-notifier`.

The systemd service unit uses `/etc/systemd-notifier/conf.yml` as the
default configuration file.

## Configuration

```yaml
---
notifiers:
  slack:
    webhook_url: https://hooks.slack.com/services/token/path
    channel: mychannel
    username: myuser
    icon_emoji: ":myicon"
    icon_url: "http://example.com/myicon"
  units:
  - sshd.service
  - ntpd.service
```
