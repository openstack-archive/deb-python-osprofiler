# Copyright 2014 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import os
import sys

import mock
import six

from osprofiler.cmd import exc
from osprofiler.cmd import shell
from tests import test


class ShellTestCase(test.TestCase):
    def setUp(self):
        super(ShellTestCase, self).setUp()
        self.old_environment = os.environ.copy()
        os.environ = {
            "OS_USERNAME": "username",
            "OS_USER_ID": "user_id",
            "OS_PASSWORD": "password",
            "OS_USER_DOMAIN_ID": "user_domain_id",
            "OS_USER_DOMAIN_NAME": "user_domain_name",
            "OS_PROJECT_DOMAIN_ID": "project_domain_id",
            "OS_PROJECT_DOMAIN_NAME": "project_domain_name",
            "OS_PROJECT_ID": "project_id",
            "OS_PROJECT_NAME": "project_name",
            "OS_TENANT_ID": "tenant_id",
            "OS_TENANT_NAME": "tenant_name",
            "OS_AUTH_URL": "http://127.0.0.1:5000/v3/",
            "OS_AUTH_TOKEN": "pass",
            "OS_CACERT": "/path/to/cacert",
            "OS_SERVICE_TYPE": "service_type",
            "OS_ENDPOINT_TYPE": "public",
            "OS_REGION_NAME": "test"
        }

        self.ceiloclient = mock.MagicMock()
        sys.modules["ceilometerclient"] = self.ceiloclient
        self.addCleanup(sys.modules.pop, "ceilometerclient", None)
        ceilo_modules = ["client", "exc", "shell"]
        for module in ceilo_modules:
            sys.modules["ceilometerclient.%s" % module] = getattr(
                self.ceiloclient, module)
            self.addCleanup(
                sys.modules.pop, "ceilometerclient.%s" % module, None)

    def tearDown(self):
        super(ShellTestCase, self).tearDown()
        os.environ = self.old_environment

    @mock.patch("sys.stdout", six.StringIO())
    @mock.patch("osprofiler.cmd.shell.OSProfilerShell")
    def test_shell_main(self, mock_shell):
        mock_shell.side_effect = exc.CommandError("some_message")
        shell.main()
        self.assertEqual("some_message\n", sys.stdout.getvalue())

    def run_command(self, cmd):
        shell.OSProfilerShell(cmd.split())

    def _test_with_command_error(self, cmd, expected_message):
        try:
            self.run_command(cmd)
        except exc.CommandError as actual_error:
            self.assertEqual(str(actual_error), expected_message)
        else:
            raise ValueError(
                "Expected: `osprofiler.cmd.exc.CommandError` is raised with "
                "message: '%s'." % expected_message)

    def test_username_is_not_presented(self):
        os.environ.pop("OS_USERNAME")
        msg = ("You must provide a username via either --os-username or "
               "via env[OS_USERNAME]")
        self._test_with_command_error("trace show fake-uuid", msg)

    def test_password_is_not_presented(self):
        os.environ.pop("OS_PASSWORD")
        msg = ("You must provide a password via either --os-password or "
               "via env[OS_PASSWORD]")
        self._test_with_command_error("trace show fake-uuid", msg)

    def test_auth_url(self):
        os.environ.pop("OS_AUTH_URL")
        msg = ("You must provide an auth url via either --os-auth-url or "
               "via env[OS_AUTH_URL]")
        self._test_with_command_error("trace show fake-uuid", msg)

    def test_no_project_and_domain_set(self):
        os.environ.pop("OS_PROJECT_ID")
        os.environ.pop("OS_PROJECT_NAME")
        os.environ.pop("OS_TENANT_ID")
        os.environ.pop("OS_TENANT_NAME")
        os.environ.pop("OS_USER_DOMAIN_ID")
        os.environ.pop("OS_USER_DOMAIN_NAME")

        msg = ("You must provide a project_id via either --os-project-id or "
               "via env[OS_PROJECT_ID] and a domain_name via either "
               "--os-user-domain-name or via env[OS_USER_DOMAIN_NAME] or a "
               "domain_id via either --os-user-domain-id or via "
               "env[OS_USER_DOMAIN_ID]")
        self._test_with_command_error("trace show fake-uuid", msg)

    def test_trace_show_ceilometrclient_is_missed(self):
        sys.modules["ceilometerclient"] = None
        sys.modules["ceilometerclient.client"] = None
        sys.modules["ceilometerclient.exc"] = None
        sys.modules["ceilometerclient.shell"] = None

        self.assertRaises(ImportError, shell.main,
                          "trace show fake_uuid".split())

    def test_trace_show_unauthorized(self):
        class FakeHTTPUnauthorized(Exception):
            http_status = 401

        self.ceiloclient.client.get_client.side_effect = FakeHTTPUnauthorized

        msg = "Invalid OpenStack Identity credentials."
        self._test_with_command_error("trace show fake_id", msg)

    def test_trace_show_unknown_error(self):
        class FakeException(Exception):
            pass

        self.ceiloclient.client.get_client.side_effect = FakeException
        msg = "Something has gone wrong. See logs for more details."
        self._test_with_command_error("trace show fake_id", msg)

    @mock.patch("osprofiler.parsers.ceilometer.get_notifications")
    @mock.patch("osprofiler.parsers.ceilometer.parse_notifications")
    def test_trace_show_no_selected_format(self, mock_notifications, mock_get):
        mock_get.return_value = "some_notificatios"
        msg = ("You should choose one of the following output-formats: "
               "--json or --html.")
        self._test_with_command_error("trace show fake_id", msg)

    @mock.patch("osprofiler.parsers.ceilometer.get_notifications")
    def test_trace_show_trace_id_not_found(self, mock_get):
        mock_get.return_value = None

        fake_trace_id = "fake_id"
        msg = ("Trace with UUID %s not found. There are 3 possible reasons: \n"
               " 1) You are using not admin credentials\n"
               " 2) You specified wrong trace id\n"
               " 3) You specified wrong HMAC Key in original calling"
               % fake_trace_id)

        self._test_with_command_error("trace show %s" % fake_trace_id, msg)

    @mock.patch("sys.stdout", six.StringIO())
    @mock.patch("osprofiler.parsers.ceilometer.get_notifications")
    @mock.patch("osprofiler.parsers.ceilometer.parse_notifications")
    def test_trace_show_in_json(self, mock_notifications, mock_get):
        mock_get.return_value = "some notification"
        notifications = {
            "info": {
                "started": 0, "finished": 0, "name": "total"}, "children": []}
        mock_notifications.return_value = notifications

        self.run_command("trace show fake_id --json")
        self.assertEqual("%s\n" % json.dumps(notifications),
                         sys.stdout.getvalue())

    @mock.patch("sys.stdout", six.StringIO())
    @mock.patch("osprofiler.parsers.ceilometer.get_notifications")
    @mock.patch("osprofiler.parsers.ceilometer.parse_notifications")
    def test_trace_show_in_html(self, mock_notifications, mock_get):
        mock_get.return_value = "some notification"

        notifications = {
            "info": {
                "started": 0, "finished": 0, "name": "total"}, "children": []}
        mock_notifications.return_value = notifications

        #NOTE(akurilin): to simplify assert statement, html-template should be
        # replaced.
        html_template = (
            "A long time ago in a galaxy far, far away..."
            "    some_data = $DATA"
            "It is a period of civil war. Rebel"
            "spaceships, striking from a hidden"
            "base, have won their first victory"
            "against the evil Galactic Empire.")

        with mock.patch("osprofiler.cmd.commands.open",
                        mock.mock_open(read_data=html_template), create=True):
            self.run_command("trace show fake_id --html")
        self.assertEqual("A long time ago in a galaxy far, far away..."
                         "    some_data = %s"
                         "It is a period of civil war. Rebel"
                         "spaceships, striking from a hidden"
                         "base, have won their first victory"
                         "against the evil Galactic Empire."
                         "\n" % json.dumps(notifications, indent=2),
                         sys.stdout.getvalue())

    @mock.patch("sys.stdout", six.StringIO())
    @mock.patch("osprofiler.parsers.ceilometer.get_notifications")
    @mock.patch("osprofiler.parsers.ceilometer.parse_notifications")
    def test_trace_show_write_to_file(self, mock_notifications, mock_get):
        mock_get.return_value = "some notification"
        notifications = {
            "info": {
                "started": 0, "finished": 0, "name": "total"}, "children": []}
        mock_notifications.return_value = notifications

        with mock.patch("osprofiler.cmd.commands.open",
                        mock.mock_open(), create=True) as mock_open:
            self.run_command("trace show fake_id --json --out='/file'")

            output = mock_open.return_value.__enter__.return_value
            output.write.assert_called_once_with(json.dumps(notifications))
