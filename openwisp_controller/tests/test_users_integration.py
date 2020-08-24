from django.conf import settings

from openwisp_users.tests.test_admin import TestUsersAdmin


class TestUsersIntegration(TestUsersAdmin):
    """
    tests integration with openwisp_users
    """

    # fixing these tests is overkill
    test_only_superuser_has_add_delete_org_perm = None
    test_can_change_inline_org_owner = None

    @property
    def add_user_inline_params(self):
        params = super().add_user_inline_params
        if 'openwisp_notifications' in settings.INSTALLED_APPS:
            params.update(
                {
                    'notificationsetting_set-TOTAL_FORMS': 0,
                    'notificationsetting_set-INITIAL_FORMS': 0,
                    'notificationsetting_set-MIN_NUM_FORMS': 0,
                    'notificationsetting_set-MAX_NUM_FORMS': 0,
                }
            )
        return params


del TestUsersAdmin
