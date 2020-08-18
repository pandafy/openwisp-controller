from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from netjsonconfig import OpenWrt
from swapper import load_model

from openwisp_users.tests.utils import TestOrganizationMixin
from openwisp_utils.tests import catch_signal

from ..signals import config_status_changed
from .utils import CreateConfigTemplateMixin, TestVpnX509Mixin

Config = load_model('config', 'Config')
Device = load_model('config', 'Device')
Template = load_model('config', 'Template')
Vpn = load_model('config', 'Vpn')
Ca = load_model('pki', 'Ca')
Cert = load_model('pki', 'Cert')
User = get_user_model()


class TestTemplate(
    TestOrganizationMixin, CreateConfigTemplateMixin, TestVpnX509Mixin, TestCase
):
    """
    tests for Template model
    """

    def test_str(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertEqual(str(t), 'test')

    def test_backend_class(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(t.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general': {'hostname': 'template'}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertIsInstance(t.backend_instance, OpenWrt)

    def test_validation(self):
        config = {'interfaces': {'invalid': True}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        # ensure django ValidationError is raised
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_config_status_modified_after_change(self):
        t = self._create_template()
        c = self._create_config(device=self._create_device(name='test-status'))
        self.assertEqual(c.status, 'modified')

        with catch_signal(config_status_changed) as handler:
            c.templates.add(t)
            handler.assert_not_called()

        c.status = 'applied'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'applied')
        t.config['interfaces'][0]['name'] = 'eth1'
        t.full_clean()

        with catch_signal(config_status_changed) as handler:
            t.save()
            c.refresh_from_db()
            handler.assert_called_once_with(
                sender=Config, signal=config_status_changed, instance=c,
            )
            self.assertEqual(c.status, 'modified')

        # status has already changed to modified
        # sgnal should not be triggered again
        with catch_signal(config_status_changed) as handler:
            t.config['interfaces'][0]['name'] = 'eth2'
            t.full_clean()
            t.save()
            c.refresh_from_db()
            handler.assert_not_called()
            self.assertEqual(c.status, 'modified')

    def test_config_status_modified_after_template_added(self):
        t = self._create_template()
        c = self._create_config(device=self._create_device(name='test-status'))
        c.status = 'applied'
        c.save()
        c.refresh_from_db()
        with catch_signal(config_status_changed) as handler:
            c.templates.add(t)
            c.refresh_from_db()
            handler.assert_called_once_with(
                sender=Config, signal=config_status_changed, instance=c,
            )

    # def test_config_modified_signal_always_sent(self):
    #     temp = self._create_template()
    #     conf = self._create_config(device=self._create_device(name='test-status'))
    #     self.assertEqual(conf.status, 'modified')
    #     # refresh instance to reset _just_created attribute
    #     conf = Config.objects.get(pk=conf.pk)

    #     with catch_signal(config_modified) as handler:
    #         conf.templates.add(temp)
    #         handler.assert_called_once_with(
    #             sender=Config,
    #             signal=config_modified,
    #             instance=conf,
    #             device=conf.device,
    #             config=conf,
    #         )

    #     conf.status = 'applied'
    #     conf.save()
    #     conf.refresh_from_db()
    #     self.assertEqual(conf.status, 'applied')
    #     temp.config['interfaces'][0]['name'] = 'eth1'
    #     temp.full_clean()

    #     with catch_signal(config_modified) as handler:
    #         temp.save()
    #         conf.refresh_from_db()
    #         handler.assert_called_once()
    #         self.assertEqual(conf.status, 'modified')

    #     # status has already changed to modified
    #     # sgnal should be triggered anyway
    #     with catch_signal(config_modified) as handler:
    #         temp.config['interfaces'][0]['name'] = 'eth2'
    #         temp.full_clean()
    #         temp.save()
    #         conf.refresh_from_db()
    #         handler.assert_called_once()
    #         self.assertEqual(conf.status, 'modified')

    def test_no_auto_hostname(self):
        t = self._create_template()
        self.assertNotIn('general', t.backend_instance.config)
        t.refresh_from_db()
        self.assertNotIn('general', t.config)

    def test_default_template(self):
        # no default templates defined yet
        org = self._get_org()
        c = self._create_config(organization=org)
        self.assertEqual(c.templates.count(), 0)
        c.device.delete()
        # create default templates for different backends
        t1 = self._create_template(
            name='default-openwrt', backend='netjsonconfig.OpenWrt', default=True
        )
        t2 = self._create_template(
            name='default-openwisp', backend='netjsonconfig.OpenWisp', default=True
        )
        c1 = self._create_config(
            device=self._create_device(name='test-openwrt'),
            backend='netjsonconfig.OpenWrt',
        )
        d2 = self._create_device(
            name='test-openwisp', mac_address=self.TEST_MAC_ADDRESS.replace('55', '56')
        )
        c2 = self._create_config(device=d2, backend='netjsonconfig.OpenWisp')
        # ensure OpenWRT device has only the default OpenWRT backend
        self.assertEqual(c1.templates.count(), 1)
        self.assertEqual(c1.templates.first().id, t1.id)
        # ensure OpenWISP device has only the default OpenWISP backend
        self.assertEqual(c2.templates.count(), 1)
        self.assertEqual(c2.templates.first().id, t2.id)

    def test_vpn_missing(self):
        try:
            self._create_template(type='vpn')
        except ValidationError as err:
            self.assertTrue('vpn' in err.message_dict)
        else:
            self.fail('ValidationError not raised')

    def test_generic_has_no_vpn(self):
        t = self._create_template(vpn=self._create_vpn())
        self.assertIsNone(t.vpn)
        self.assertFalse(t.auto_cert)

    def test_generic_has_create_cert_false(self):
        t = self._create_template()
        self.assertFalse(t.auto_cert)

    def test_auto_client_template(self):
        org = self._get_org()
        vpn = self._create_vpn(organization=org)
        t = self._create_template(
            name='autoclient',
            organization=org,
            type='vpn',
            auto_cert=True,
            vpn=vpn,
            config={},
        )
        control = t.vpn.auto_client()
        self.assertDictEqual(t.config, control)

    def test_auto_client_template_auto_cert_False(self):
        vpn = self._create_vpn()
        t = self._create_template(
            name='autoclient', type='vpn', auto_cert=False, vpn=vpn, config={}
        )
        vpn = t.config['openvpn'][0]
        self.assertEqual(vpn['cert'], 'cert.pem')
        self.assertEqual(vpn['key'], 'key.pem')
        self.assertEqual(len(t.config['files']), 1)
        self.assertIn('ca_path', t.config['files'][0]['path'])

    def test_template_context_var(self):
        org = self._get_org()
        t = self._create_template(
            organization=org,
            config={
                'files': [
                    {
                        'path': '/etc/vpnserver1',
                        'mode': '0600',
                        'contents': '{{ name }}\n{{ vpnserver1 }}\n',
                    }
                ]
            },
        )
        c = self._create_config(organization=org)
        c.templates.add(t)
        # clear cache
        del c.backend_instance
        output = c.backend_instance.render()
        vpnserver1 = settings.OPENWISP_CONTROLLER_CONTEXT['vpnserver1']
        self.assertIn(vpnserver1, output)

    def test_get_context(self):
        t = self._create_template()
        expected = {}
        expected.update(settings.OPENWISP_CONTROLLER_CONTEXT)
        self.assertEqual(t.get_context(), expected)

    def test_tamplates_clone(self):
        org = self._get_org()
        t = self._create_template(organization=org, default=True)
        t.save()
        user = User.objects.create_superuser(
            username='admin', password='tester', email='admin@admin.com'
        )
        c = t.clone(user)
        c.full_clean()
        c.save()
        self.assertEqual(c.name, '{} (Clone)'.format(t.name))
        self.assertIsNotNone(c.pk)
        self.assertNotEqual(c.pk, t.pk)
        self.assertFalse(c.default)

    def test_duplicate_files_in_template(self):
        try:
            self._create_template(
                name='test-vpn-1',
                config={
                    'files': [
                        {
                            'path': '/etc/vpnserver1',
                            'mode': '0644',
                            'contents': '{{ name }}\n{{ vpnserver1 }}\n',
                        },
                        {
                            'path': '/etc/vpnserver1',
                            'mode': '0644',
                            'contents': '{{ name }}\n{{ vpnserver1 }}\n',
                        },
                    ]
                },
            )
        except ValidationError as e:
            self.assertIn('Invalid configuration triggered by "#/files"', str(e))
        else:
            self.fail('ValidationError not raised!')

    def test_variable_substition(self):
        config = {"dns_servers": ["{{dns}}"]}
        default_values = {"dns": "4.4.4.4"}
        options = {
            "name": "test1",
            "backend": "netjsonconfig.OpenWrt",
            "config": config,
            "default_values": default_values,
        }
        temp = Template(**options)
        temp.full_clean()
        temp.save()
        obj = Template.objects.get(name='test1')
        self.assertEqual(obj.name, 'test1')

    def test_template_with_org(self):
        org = self._get_org()
        template = self._create_template(organization=org)
        self.assertEqual(template.organization_id, org.pk)

    def test_template_without_org(self):
        template = self._create_template()
        self.assertIsNone(template.organization)

    def test_template_with_shared_vpn(self):
        vpn = self._create_vpn()  # shared VPN
        org = self._get_org()
        template = self._create_template(organization=org, type='vpn', vpn=vpn)
        self.assertIsNone(vpn.organization)
        self.assertEqual(template.vpn_id, vpn.pk)

    def test_template_and_vpn_different_organization(self):
        org1 = self._get_org()
        vpn = self._create_vpn(organization=org1)
        org2 = self._create_org(name='test org2', slug='test-org2')
        try:
            self._create_template(organization=org2, type='vpn', vpn=vpn)
        except ValidationError as e:
            self.assertIn('organization', e.message_dict)
            self.assertIn('related VPN server match', e.message_dict['organization'][0])
        else:
            self.fail('ValidationError not raised')

    def test_org_default_template(self):
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self._create_template(organization=org1, name='t1', default=True)
        self._create_template(organization=org2, name='t2', default=True)
        d1 = self._create_device(organization=org1, name='d1')
        c1 = self._create_config(device=d1)
        self.assertEqual(c1.templates.count(), 1)
        self.assertEqual(c1.templates.filter(name='t1').count(), 1)
        d2 = self._create_device(
            organization=org2,
            name='d2',
            mac_address='00:00:00:11:22:33',
            key='1234567890',
        )
        c2 = self._create_config(device=d2)
        self.assertEqual(c2.templates.count(), 1)
        self.assertEqual(c2.templates.filter(name='t2').count(), 1)

    def test_org_default_shared_template(self):
        org1 = self._create_org(name='org1')
        self._create_template(organization=org1, name='t1', default=True)
        self._create_template(organization=None, name='t2', default=True)
        c1 = self._create_config(organization=org1)
        self.assertEqual(c1.templates.count(), 2)
        self.assertEqual(c1.templates.filter(name='t1').count(), 1)
        self.assertEqual(c1.templates.filter(name='t2').count(), 1)

    def test_auto_client_template_default(self):
        org = self._get_org()
        vpn = self._create_vpn(organization=org)
        self._create_template(
            name='autoclient',
            organization=org,
            default=True,
            type='vpn',
            auto_cert=True,
            vpn=vpn,
            config={},
        )
        self._create_config(organization=org)

    def test_auto_generated_certificate_for_organization(self):
        organization = self._get_org()
        vpn = self._create_vpn()
        template = self._create_template(type='vpn', auto_cert=True, vpn=vpn)
        corresponding_device = self._create_device(organization=organization,)
        config = self._create_config(device=corresponding_device,)
        config.templates.add(template)
        vpn_clients = config.vpnclient_set.all()
        for vpn_client in vpn_clients:
            self.assertIsNotNone(vpn_client.cert.organization)
            self.assertEqual(vpn_client.cert.organization, config.device.organization)

    def test_template_name_and_organization_unique(self):
        org = self._get_org()
        self._create_template(name='template', organization=org, default=True)
        kwargs = {
            'name': 'template',  # the name attribute is same as in the template created
            'organization': org,
            'default': True,
        }
        # _create_template should raise an exception as
        # two templates with the same organization can't have the same name
        with self.assertRaises(ValidationError):
            self._create_template(**kwargs)
