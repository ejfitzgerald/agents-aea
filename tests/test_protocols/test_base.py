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

"""This module contains the tests of the messages module."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple, Type
from unittest.mock import MagicMock

import pytest

from aea import AEA_DIR
from aea.configurations.constants import DEFAULT_PROTOCOL
from aea.helpers.dialogue.base import DialogueLabel
from aea.mail.base import Envelope
from aea.protocols.base import JSONSerializer, Message, ProtobufSerializer, Protocol
from aea.protocols.default.dialogues import DefaultDialogue, DefaultDialogues
from aea.protocols.signing.dialogues import SigningDialogue, SigningDialogues
from aea.protocols.state_update.dialogues import (
    StateUpdateDialogue,
    StateUpdateDialogues,
)

from tests.conftest import UNKNOWN_PROTOCOL_PUBLIC_ID


DIALOGUE_CLASSES: List[Tuple[Type, Type]] = [
    (DefaultDialogue, DefaultDialogues),
    (SigningDialogue, SigningDialogues),
    (StateUpdateDialogue, StateUpdateDialogues),
]


class TestMessageProperties:
    """Test that the base serializations work."""

    @classmethod
    def setup_class(cls):
        cls.body = {"body_1": "1", "body_2": "2"}
        cls.kwarg = 1
        cls.message = Message(cls.body, kwarg=cls.kwarg)

    def test_message_properties(self):
        for key, value in self.body.items():
            assert self.message.get(key) == value
        assert self.message.get("kwarg") == self.kwarg
        assert not self.message.has_sender
        assert not self.message.has_counterparty
        assert not self.message.has_to
        assert not self.message.is_incoming


class TestBaseSerializations:
    """Test that the base serializations work."""

    @classmethod
    def setup_class(cls):
        """Set up the use case."""
        cls.message = Message(content="hello")
        cls.message2 = Message(body={"content": "hello"})

    def test_default_protobuf_serialization(self):
        """Test that the default Protobuf serialization works."""
        message_bytes = ProtobufSerializer().encode(self.message)
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = ProtobufSerializer().decode(expected_envelope.message)
        actual_msg = self.message
        assert expected_msg == actual_msg

    def test_default_json_serialization(self):
        """Test that the default JSON serialization works."""
        message_bytes = JSONSerializer().encode(self.message)
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = JSONSerializer().decode(expected_envelope.message)
        actual_msg = self.message
        assert expected_msg == actual_msg

    def test_set(self):
        """Test that the set method works."""
        key, value = "temporary_key", "temporary_value"
        assert self.message.get(key) is None
        self.message.set(key, value)
        assert self.message.get(key) == value

    def test_unset(self):
        """Test the unset function of the message."""
        self.message2.unset("content")
        assert "content" not in self.message2.body.keys()

    def test_body_setter(self):
        """Test the body setter."""
        m_dict = {"Hello": "World"}
        self.message2.body = m_dict
        assert "Hello" in self.message2.body.keys()


class TestProtocolFromDir:
    """Test the 'Protocol.from_dir' method."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_protocol_load_positive(self):
        """Test protocol loaded correctly."""
        default_protocol = Protocol.from_dir(Path(AEA_DIR, "protocols", "default"))
        assert str(default_protocol.public_id) == str(
            DEFAULT_PROTOCOL
        ), "Protocol not loaded correctly."

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestMessageAttributes:
    """Test some message attributes."""

    def test_performative(self):
        """Test message performative."""

        class SomePerformative(Message.Performative):
            value = "value"

        message = Message(performative=SomePerformative.value)
        assert message.performative == SomePerformative.value
        assert str(message.performative) == "value"

    def test_to(self):
        """Test the 'to' attribute getter and setter."""
        message = Message()
        with pytest.raises(AssertionError, match="To must not be None."):
            message.to

        message.to = "to"
        assert message.to == "to"

        with pytest.raises(AssertionError, match="To already set."):
            message.to = "to"

    def test_dialogue_reference(self):
        """Test the 'dialogue_reference' attribute."""
        message = Message(dialogue_reference=("x", "y"))
        assert message.dialogue_reference == ("x", "y")

    def test_message_id(self):
        """Test the 'message_id' attribute."""
        message = Message(message_id=1)
        assert message.message_id == 1

    def test_target(self):
        """Test the 'target' attribute."""
        message = Message(target=1)
        assert message.target == 1


@pytest.mark.parametrize("dialogue_classes", DIALOGUE_CLASSES)
def test_dialogue(dialogue_classes):
    """Test dialogue initialization."""
    dialogue_class, _ = dialogue_classes
    dialogue = dialogue_class(DialogueLabel(("x", "y"), "opponent_addr", "starer_addr"))
    assert dialogue.is_valid(MagicMock())


@pytest.mark.parametrize("dialogues_classes", DIALOGUE_CLASSES)
def test_default_dialogues(dialogues_classes):
    """Test default dialogues initialization."""
    dialogue_class, dialogues_class = dialogues_classes
    dialogues = dialogues_class("agent_address")

    dialogue = dialogues.create_dialogue(
        DialogueLabel(("x", "y"), "opponent_addr", "starter_addr"),
        next(iter(dialogue_class.Role)),
    )
    assert isinstance(dialogue, dialogue_class)
