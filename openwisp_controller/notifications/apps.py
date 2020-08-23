from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from openwisp_notifications.types import (
    register_notification_type,
    unregister_notification_type,
)


class NotificationsConfig(AppConfig):
    name = 'openwisp_controller.notifications'

    def ready(self):
        from . import handlers  # noqa

        self.register_notification_types()

    def register_notification_types(self):
        unregister_notification_type('default')
        register_notification_type(
            'config_problem',
            {
                'verbose_name': _('Configuration PROBLEM'),
                'verb': _('encountered an error'),
                'level': 'warning',
                'email_subject': _(
                    '[{site.name}] PROBLEM: {notification.target.name} configuration'
                    ' {notification.verb}'
                ),
                'message': _(
                    'The configuration for [{notification.target.name}]'
                    ' ({notification.target_link}) {notification.verb}.'
                ),
            },
        )

        register_notification_type(
            'config_recovery',
            {
                'verbose_name': _('Configuration RECOVERY'),
                'verb': _('recovered successfully'),
                'level': 'info',
                'email_subject': _(
                    '[{site.name}] RECOVERY: {notification.target.name} configuration '
                    '{notification.verb}'
                ),
                'message': _(
                    'The configuration for [{notification.target.name}]'
                    '({notification.target_link}) has {notification.verb}.'
                ),
            },
        )

        register_notification_type(
            'device_registered',
            {
                'verbose_name': _('Device Registration'),
                'verb': _('registered successfully'),
                'level': 'success',
                'email_subject': _(
                    '[{site.name}] SUCCESS: {notification.target.name} '
                    '{notification.verb}'
                ),
                'message': _(
                    'The device [{notification.target.name}]'
                    '({notification.target_link}) has {notification.verb}.'
                ),
            },
        )
