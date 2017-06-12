from setuptools import setup

setup(name         = 'systemd_notifier',
      version      = '0.1.0',
      author       = 'David R. Bild',
      author_email = 'david@davidbild.org',
      keywords     = 'systemd monitor alert notify unit slack email status change',
      url          = 'http://github.com/drbild/systemd_notifier',
      description  = 'Notify for systemd unit status changes',
      classifiers  = [
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python',
      ],
      packages     = ['systemd_notifier',
                      'systemd_notifier.notifiers'],
      
      entry_points = {
          'console_scripts' : [
              'systemd-notifier=systemd_notifier.main:main',
          ]
      }
)
