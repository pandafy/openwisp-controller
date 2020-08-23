from django.test import TestCase
from swapper import load_model

from openwisp_controller.config.tests.utils import CreateConfigMixin
from openwisp_users.tests.utils import TestOrganizationMixin

Config = load_model('config', 'Config')
Notification = load_model('openwisp_notifications', 'Notification')

notification_qs = Notification.objects.all()


class TestConfigNotifications(CreateConfigMixin, TestOrganizationMixin, TestCase):
    def setUp(self):
        self.admin = self._get_admin()

    def test_config_problem_notification(self):
        config = self._create_config()
        config.set_status_error()

        self.assertEqual(config.status, 'error')
        # One notification for device registration, other for config
        self.assertEqual(notification_qs.count(), 2)
        notification = notification_qs.first()
        self.assertEqual(notification.actor, config)
        self.assertEqual(notification.target, config.device)
        self.assertEqual(notification.type, 'config_problem')
        self.assertEqual(
            notification.email_subject,
            f'[example.com] PROBLEM: {config} configuration encountered an error',
        )
        self.assertIn('encountered an error', notification.message)

    def test_config_recovery_notification(self):
        config = self._create_config()
        config.set_status_error()

        self.assertEqual(config.status, 'error')
        # One notification for device registration, other for config
        self.assertEqual(notification_qs.count(), 2)
        notification = notification_qs.first()
        self.assertEqual(notification.actor, config)
        self.assertEqual(notification.target, config.device)
        self.assertEqual(notification.type, 'config_problem')
        self.assertEqual(
            notification.email_subject,
            f'[example.com] PROBLEM: {config} configuration encountered an error',
        )
        self.assertIn('encountered an error', notification.message)

    def test_device_registered(self):
        device = self._create_device()

        self.assertEqual(notification_qs.count(), 1)
        notification = notification_qs.first()
        self.assertEqual(notification.actor, device)
        self.assertEqual(notification.target, device)
        self.assertEqual(notification.type, 'device_registered')
        self.assertEqual(
            notification.email_subject,
            f'[example.com] SUCCESS: {device.name} registered successfully',
        )
        self.assertIn('registered successfully', notification.message)
