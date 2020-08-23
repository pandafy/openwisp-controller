#!/bin/bash
set -e

# TODO: remove when openwisp-notifications 0.1 is released
pip install -U https://github.com/openwisp/openwisp-notifications/tarball/fix-notification-setting
# TODO: remove it before merging
pip install -U https://github.com/openwisp/openwisp-users/tarball/master
