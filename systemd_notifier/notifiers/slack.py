import logging
import json
import urllib2

class Slack(object):

    def __init__(self, options):
        self._options = options
        self._name    = "SlackNotifier"

        self._webhook = SlackWebHook(url        = options['webhook_url'],
                                     channel    = options['channel'],
                                     username   = options['username'],
                                     icon_emoji = options['icon_emoji'],
                                     icon_url   = options['icon_url'])

    @property
    def options(self):
        return self._options

    @property
    def name(self):
        return self._name
        
    def notify_start(self, hostname):
        message = "SystemdNotifier is starting on %s"%(hostname)

        attach  = {
            'fallback' : message,
            'text'     : message,
            'color'    : 'good'
        }

        self._webhook.ping("", attachments = [attach])

    def notify_stop(self, hostname):
        message = "SystemdNotifier is stopping on %s"%(hostname)

        attach = {
            'fallback' : message,
            'text'     : message,
            'color'    : 'danger'
        }

        self._webhook.ping("", attachments = [attach])

    def notify(self, notification):
        unit    = notification.unit
        message = "%s: systemd unit %s on %s %s"%(notification.type,
                                                  unit.name,
                                                  notification.hostname,
                                                  unit.state_change.status_text)

        attach  = {
            'fallback' : "%s: %s (%s)"%(message, unit.state.active, unit.state.sub),
            'color'    : self.color(notification.type),
            'fields'   : self.fields(notification)}

        logging.debug("Sending slack notification with attachment: %s"%(attach))
        self._webhook.ping(message, attachments = [attach])
        logging.debug("Sent slack notification")

    @staticmethod
    def color(type):
        if type == 'alert':
            return 'danger'
        elif type == 'warning':
            return '#FF9900'
        elif type == 'info':
            return '#0099CC'
        else:
            return 'good'

    @staticmethod
    def fields(notification):
        f = [{ 'title' : "Hostname",
               'value' : notification.hostname,
               'short': True},
             { 'title' : "Unit",
               'value' : notification.unit.name,
               'short' : True }]

        changes = [diff[-1] for diff in notification.unit.state_change.diff()]
        return f + [{ 'title' : c.display_name,
                      'value' : c.value,
                      'short' : True} for c in changes]

class SlackWebHook(object):
            
    def __init__(self, url, channel, username, icon_emoji, icon_url):
        self.url = url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji
        self.icon_url = icon_url

    def ping(self, text, attachments=None):
        message = {
            'text'        : text,
            'attachments' : attachments,
            'channel'     : self.channel,
            'username'    : self.username,
            'icon_emoji'  : self.icon_emoji,
            'icon_url'    : self.icon_url
        }

        request = urllib2.Request(self.url, json.dumps(message), {'Content-Type': 'application/json', 'Content-Length': len(json.dumps(message))})
        response = urllib2.urlopen(request)
