def load_config(config_file):
    import yaml

    with open(config_file, 'r') as f:
        return yaml.load(f)

def load_hostname(config):
    import socket

    return config.get('hostname', socket.gethostname())

def load_dbus_manager(config):
    from systemd import DBusManager

    return DBusManager()

def load_notification_center(config):
    from collections import defaultdict
    from notification import NotificationCenter, load_notifier

    notification_center = NotificationCenter()

    for name, options in config.get('notifiers', {}).iteritems():
        notifier = load_notifier(name)(defaultdict(str, options))
        notification_center.add_notifier(notifier)

    return notification_center;

def configure_logging(config):
    import logging
    import sys

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def load_monitor(config, hostname, dbus_manager, notification_center):
    from monitor import Monitor

    monitor = Monitor(hostname, dbus_manager, notification_center)

    monitor.register_units(config.get('units', []))

    return monitor
    
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Notifier for systemd unit status changes")
    parser.add_argument("-c", "--config" , required=True, help="configuration file")

    args = parser.parse_args()
    config              = load_config(args.config)

    configure_logging(config)
    
    hostname            = load_hostname(config)
    dbus_manager        = load_dbus_manager(config)
    notification_center = load_notification_center(config)

    monitor             = load_monitor(config, hostname, dbus_manager, notification_center)
    monitor.start()
    
if __name__ == "__main__":
    main()
