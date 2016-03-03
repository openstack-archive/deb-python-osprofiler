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

import mock

from osprofiler._notifiers import base
from osprofiler.tests import test


class MessagingTestCase(test.TestCase):

    def test_init_and_notify(self):

        messaging = mock.MagicMock()
        context = "context"
        transport = "transport"
        project = "project"
        service = "service"
        host = "host"

        notify_func = base.Notifier.factory("Messaging", messaging, context,
                                            transport, project, service, host)

        messaging.Notifier.assert_called_once_with(
            transport, publisher_id=host, driver="messaging",
            topic="profiler", retry=0)

        info = {
            "a": 10
        }
        notify_func(info)

        expected_data = {"project": project, "service": service}
        expected_data.update(info)
        messaging.Notifier().info.assert_called_once_with(
            context, "profiler.%s" % service, expected_data)

        messaging.reset_mock()
        notify_func(info, context="my_context")
        messaging.Notifier().info.assert_called_once_with(
            "my_context", "profiler.%s" % service, expected_data)
