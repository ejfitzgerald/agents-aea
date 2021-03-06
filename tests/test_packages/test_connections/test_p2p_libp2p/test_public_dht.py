# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This test module contains integration tests for P2PLibp2p connection."""

import os
import shutil
import tempfile

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import (
    PUBLIC_DHT_DELEGATE_URI_1,
    PUBLIC_DHT_DELEGATE_URI_2,
    PUBLIC_DHT_P2P_MADDR_1,
    PUBLIC_DHT_P2P_MADDR_2,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)

DEFAULT_PORT = 10234
PUBLIC_DHT_MADDRS = [PUBLIC_DHT_P2P_MADDR_1, PUBLIC_DHT_P2P_MADDR_2]
PUBLIC_DHT_DELEGATE_URIS = [PUBLIC_DHT_DELEGATE_URI_1, PUBLIC_DHT_DELEGATE_URI_2]
AEA_DEFAULT_LAUNCH_TIMEOUT = 15
AEA_LIBP2P_LAUNCH_TIMEOUT = 660  # may downloads up to ~66Mb


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTRelay:
    """Test that public DHT's relay service is working properly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

    def test_connectivity(self):
        for maddr in PUBLIC_DHT_MADDRS:
            connection = _make_libp2p_connection(
                DEFAULT_PORT + 1, relay=False, entry_peers=[maddr]
            )
            multiplexer = Multiplexer([connection])
            self.log_files.append(connection.node.log_file)
            multiplexer.connect()

            try:
                assert (
                    connection.is_connected is True
                ), "Couldn't connect to public node {}".format(maddr)
            except Exception:
                raise
            finally:
                multiplexer.disconnect()

    def test_communication_direct(self):
        for maddr in PUBLIC_DHT_MADDRS:
            connection1 = _make_libp2p_connection(
                DEFAULT_PORT + 1, relay=False, entry_peers=[maddr]
            )
            multiplexer1 = Multiplexer([connection1])
            self.log_files.append(connection1.node.log_file)
            multiplexer1.connect()

            connection2 = _make_libp2p_connection(
                DEFAULT_PORT + 2, relay=False, entry_peers=[maddr]
            )
            multiplexer2 = Multiplexer([connection2])
            self.log_files.append(connection2.node.log_file)
            multiplexer2.connect()

            addr_1 = connection1.node.address
            addr_2 = connection2.node.address

            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            envelope = Envelope(
                to=addr_2,
                sender=addr_1,
                protocol_id=DefaultMessage.protocol_id,
                message=msg,
            )

            multiplexer1.put(envelope)
            delivered_envelope = multiplexer2.get(block=True, timeout=20)

            try:
                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message != envelope.message
                msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                assert envelope.message == msg
            except Exception:
                raise
            finally:
                multiplexer1.disconnect()
                multiplexer2.disconnect()

    def test_communication_indirect(self):
        assert len(PUBLIC_DHT_MADDRS) > 1, "Test requires at least 2 public dht node"

        for i in range(len(PUBLIC_DHT_MADDRS)):
            connection1 = _make_libp2p_connection(
                DEFAULT_PORT + 1, relay=False, entry_peers=[PUBLIC_DHT_MADDRS[i]]
            )
            multiplexer1 = Multiplexer([connection1])
            self.log_files.append(connection1.node.log_file)
            multiplexer1.connect()
            addr_1 = connection1.node.address

            for j in range(len(PUBLIC_DHT_MADDRS)):
                if j == i:
                    continue

                connection2 = _make_libp2p_connection(
                    DEFAULT_PORT + 2, relay=False, entry_peers=[PUBLIC_DHT_MADDRS[j]],
                )
                multiplexer2 = Multiplexer([connection2])
                self.log_files.append(connection2.node.log_file)
                multiplexer2.connect()

                addr_2 = connection2.node.address

                msg = DefaultMessage(
                    dialogue_reference=("", ""),
                    message_id=1,
                    target=0,
                    performative=DefaultMessage.Performative.BYTES,
                    content=b"hello",
                )
                envelope = Envelope(
                    to=addr_2,
                    sender=addr_1,
                    protocol_id=DefaultMessage.protocol_id,
                    message=msg,
                )

                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=20)

                try:
                    assert delivered_envelope is not None
                    assert delivered_envelope.to == envelope.to
                    assert delivered_envelope.sender == envelope.sender
                    assert delivered_envelope.protocol_id == envelope.protocol_id
                    assert delivered_envelope.message != envelope.message
                    msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                    assert envelope.message == msg
                except Exception:
                    multiplexer1.disconnect()
                    raise
                finally:
                    multiplexer2.disconnect()

            multiplexer1.disconnect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTDelegate:
    """Test that public DHT's delegate service is working properly"""

    def test_connectivity(self):
        for uri in PUBLIC_DHT_DELEGATE_URIS:
            connection = _make_libp2p_client_connection(uri=uri)
            multiplexer = Multiplexer([connection])
            multiplexer.connect()

            try:
                assert (
                    connection.is_connected is True
                ), "Couldn't connect to public node {}".format(uri)
            except Exception:
                raise
            finally:
                multiplexer.disconnect()

    def test_communication_direct(self):
        for uri in PUBLIC_DHT_DELEGATE_URIS:
            connection1 = _make_libp2p_client_connection(uri=uri)
            multiplexer1 = Multiplexer([connection1])
            multiplexer1.connect()

            connection2 = _make_libp2p_client_connection(uri=uri)
            multiplexer2 = Multiplexer([connection2])
            multiplexer2.connect()

            addr_1 = connection1.address
            addr_2 = connection2.address

            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            envelope = Envelope(
                to=addr_2,
                sender=addr_1,
                protocol_id=DefaultMessage.protocol_id,
                message=msg,
            )

            multiplexer1.put(envelope)
            delivered_envelope = multiplexer2.get(block=True, timeout=20)

            try:
                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message != envelope.message
                msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                assert envelope.message == msg
            except Exception:
                raise
            finally:
                multiplexer1.disconnect()
                multiplexer2.disconnect()

    def test_communication_indirect(self):
        assert (
            len(PUBLIC_DHT_DELEGATE_URIS) > 1
        ), "Test requires at least 2 public dht node"

        for i in range(len(PUBLIC_DHT_DELEGATE_URIS)):
            connection1 = _make_libp2p_client_connection(
                uri=PUBLIC_DHT_DELEGATE_URIS[i]
            )
            multiplexer1 = Multiplexer([connection1])
            multiplexer1.connect()

            addr_1 = connection1.address
            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )

            for j in range(len(PUBLIC_DHT_DELEGATE_URIS)):
                if j == i:
                    continue

                connection2 = _make_libp2p_client_connection(
                    uri=PUBLIC_DHT_DELEGATE_URIS[j]
                )
                multiplexer2 = Multiplexer([connection2])
                multiplexer2.connect()

                addr_2 = connection2.address
                envelope = Envelope(
                    to=addr_2,
                    sender=addr_1,
                    protocol_id=DefaultMessage.protocol_id,
                    message=msg,
                )

                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=20)

                try:
                    assert delivered_envelope is not None
                    assert delivered_envelope.to == envelope.to
                    assert delivered_envelope.sender == envelope.sender
                    assert delivered_envelope.protocol_id == envelope.protocol_id
                    assert delivered_envelope.message != envelope.message
                    msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                    assert envelope.message == msg
                except Exception:
                    multiplexer1.disconnect()
                    raise
                finally:
                    multiplexer2.disconnect()

            multiplexer1.disconnect()


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTRelayAEACli(AEATestCaseEmpty):
    """"Test that public DHT's relay service is working properly, using aea cli"""

    @libp2p_log_on_failure
    def test_connectivity(self):
        self.add_item("connection", "fetchai/p2p_libp2p:0.7.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.7.0")

        config_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.set_config(
            "{}.local_uri".format(config_path), "127.0.0.1:{}".format(DEFAULT_PORT)
        )
        self.force_set_config(
            "{}.entry_peers".format(config_path), PUBLIC_DHT_MADDRS,
        )

        # for logging
        log_file = "libp2p_node_{}.log".format(self.agent_name)
        log_file = os.path.join(os.path.abspath(os.getcwd()), log_file)
        self.set_config("{}.log_file".format(config_path), log_file)
        self.log_files = [log_file]

        process = self.run_agent()

        is_running = self.is_running(process, timeout=AEA_LIBP2P_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        check_strings = "My libp2p addresses: ["
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.terminate_agents()
        super(TestLibp2pConnectionPublicDHTRelayAEACli, cls).teardown_class()


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTDelegateAEACli(AEATestCaseEmpty):
    """Test that public DHT's delegate service is working properly, using aea cli"""

    def test_connectivity(self):
        self.add_item("connection", "fetchai/p2p_libp2p_client:0.5.0")
        config_path = "vendor.fetchai.connections.p2p_libp2p_client.config"
        self.force_set_config(
            "{}.nodes".format(config_path),
            [{"uri": "{}".format(uri)} for uri in PUBLIC_DHT_DELEGATE_URIS],
        )

        process = self.run_agent()
        is_running = self.is_running(process, timeout=AEA_DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.terminate_agents()
        super(TestLibp2pConnectionPublicDHTDelegateAEACli, cls).teardown_class()
