from unittest import mock

from django.test import TransactionTestCase
from swapper import load_model

from openwisp_utils.tests import catch_signal

from ..config.signals import config_modified
from ..connection import settings as app_settings
from ..connection.tests.utils import CreateConnectionsMixin

Config = load_model('config', 'Config')


class TestTransactionBlocks(CreateConnectionsMixin, TransactionTestCase):
    _connect_path = 'paramiko.SSHClient.connect'
    _exec_command_path = 'paramiko.SSHClient.exec_command'

    def _exec_command_return_value(
        self, stdin='', stdout='mocked', stderr='', exit_code=0
    ):
        stdin_ = mock.Mock()
        stdout_ = mock.Mock()
        stderr_ = mock.Mock()
        stdin_.read().decode('utf8').strip.return_value = stdin
        stdout_.read().decode('utf8').strip.return_value = stdout
        stdout_.channel.recv_exit_status.return_value = exit_code
        stderr_.read().decode('utf8').strip.return_value = stderr
        return (stdin_, stdout_, stderr_)

    @mock.patch(_connect_path)
    def test_device_config_update(self, mocked_connect):
        org1 = self._create_org(name='org1')
        cred = self._create_credentials_with_key(
            organization=org1, port=self.ssh_server.port
        )
        device = self._create_device(organization=org1)
        update_strategy = app_settings.UPDATE_STRATEGIES[0][0]
        c = self._create_config(device=device, status='applied')
        self._create_device_connection(
            device=device, credentials=cred, update_strategy=update_strategy
        )
        c.config = {
            'interfaces': [
                {
                    'name': 'eth10',
                    'type': 'ethernet',
                    'addresses': [{'family': 'ipv4', 'proto': 'dhcp'}],
                }
            ]
        }
        c.full_clean()

        with mock.patch(self._exec_command_path) as mocked:
            mocked.return_value = self._exec_command_return_value()
            c.save()
            mocked.assert_called_once()
        c.refresh_from_db()
        self.assertEqual(c.status, 'applied')

    def test_config_modified_signal_always_sent(self):
        temp = self._create_template()
        conf = self._create_config(device=self._create_device(name='test-status'))
        self.assertEqual(conf.status, 'modified')
        # refresh instance to reset _just_created attribute
        conf = Config.objects.get(pk=conf.pk)

        with catch_signal(config_modified) as handler:
            conf.templates.add(temp)
            handler.assert_called_once_with(
                sender=Config,
                signal=config_modified,
                instance=conf,
                device=conf.device,
                config=conf,
            )

        conf.status = 'applied'
        conf.save()
        conf.refresh_from_db()
        self.assertEqual(conf.status, 'applied')
        temp.config['interfaces'][0]['name'] = 'eth1'
        temp.full_clean()

        with catch_signal(config_modified) as handler:
            temp.save()
            conf.refresh_from_db()
            handler.assert_called_once()
            self.assertEqual(conf.status, 'modified')

        # status has already changed to modified
        # sgnal should be triggered anyway
        with catch_signal(config_modified) as handler:
            temp.config['interfaces'][0]['name'] = 'eth2'
            temp.full_clean()
            temp.save()
            conf.refresh_from_db()
            handler.assert_called_once()
            self.assertEqual(conf.status, 'modified')

    def test_config_modified_sent(self):
        org = self._get_org()
        with catch_signal(config_modified) as handler:
            c = self._create_config(organization=org, status='applied')
            handler.assert_not_called()
            self.assertEqual(c.status, 'applied')

        with catch_signal(config_modified) as handler:
            c.config = {'general': {'description': 'test'}}
            c.full_clean()
            handler.assert_not_called()
            self.assertEqual(c.status, 'modified')

        with catch_signal(config_modified) as handler:
            c.save()
            handler.assert_called_once_with(
                sender=Config,
                signal=config_modified,
                instance=c,
                device=c.device,
                config=c,
            )
            self.assertEqual(c.status, 'modified')

        with catch_signal(config_modified) as handler:
            c.config = {'general': {'description': 'changed again'}}
            c.full_clean()
            c.save()
            handler.assert_called_once()
            self.assertEqual(c.status, 'modified')
