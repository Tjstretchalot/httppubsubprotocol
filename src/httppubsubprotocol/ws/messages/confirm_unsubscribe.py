from typing import TYPE_CHECKING, Collection, List, Literal, Type, Union

from httppubsubprotocol.sync_io import SyncReadableBytesIO
from httppubsubprotocol.ws.constants import (
    BroadcasterToSubscriberWSMessageType,
    PubSubWSMessageFlags,
)
from httppubsubprotocol.compat import fast_dataclass
from httppubsubprotocol.ws.generic_parser import B2S_MessageParser
from httppubsubprotocol.ws.parser_helpers import parse_simple_headers
from httppubsubprotocol.ws.serializer_helpers import (
    MessageSerializer,
    serialize_simple_message,
)


@fast_dataclass
class B2S_ConfirmUnsubscribeExact:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_EXACT]
    """discriminator value"""

    topic: bytes
    """the topic the subscriber is no longer subscribed to"""


_exact_headers: Collection[str] = ("x-topic",)


class B2S_ConfirmUnsubscribeExactParser:
    """Satisfies B2S_MessageParser[B2S_ConfirmUnsubscribeExact]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberWSMessageType]:
        return [BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_EXACT]

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: BroadcasterToSubscriberWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_ConfirmUnsubscribeExact:
        assert type == BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_EXACT

        headers = parse_simple_headers(flags, payload, _exact_headers)
        topic = headers["x-topic"]
        return B2S_ConfirmUnsubscribeExact(
            type=type,
            topic=topic,
        )


if TYPE_CHECKING:
    _: Type[B2S_MessageParser[B2S_ConfirmUnsubscribeExact]] = (
        B2S_ConfirmUnsubscribeExactParser
    )


def serialize_b2s_confirm_unsubscribe_exact(
    msg: B2S_ConfirmUnsubscribeExact, /, *, minimal_headers: bool
) -> Union[bytes, bytearray, memoryview]:
    """Satisfies MessageSerializer[B2S_ConfirmUnsubscribeExact]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_exact_headers,
        header_values=(msg.topic,),
        minimal_headers=minimal_headers,
        payload=b"",
    )


if TYPE_CHECKING:
    __: MessageSerializer[B2S_ConfirmUnsubscribeExact] = (
        serialize_b2s_confirm_unsubscribe_exact
    )


@fast_dataclass
class B2S_ConfirmUnsubscribeGlob:
    """
    B2S = Broadcaster to Subscriber
    See the type enum documentation for more information on the fields
    """

    type: Literal[BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_GLOB]
    """discriminator value"""

    glob: str
    """the glob pattern the subscriber is no longer subscribed to"""


_glob_headers: Collection[str] = ("x-glob",)


class B2S_ConfirmUnsubscribeGlobParser:
    """Satisfies B2S_MessageParser[B2S_ConfirmUnsubscribeGlob]"""

    @classmethod
    def relevant_types(cls) -> List[BroadcasterToSubscriberWSMessageType]:
        return [BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_GLOB]

    @classmethod
    def parse(
        cls,
        flags: PubSubWSMessageFlags,
        type: BroadcasterToSubscriberWSMessageType,
        payload: SyncReadableBytesIO,
    ) -> B2S_ConfirmUnsubscribeGlob:
        assert type == BroadcasterToSubscriberWSMessageType.CONFIRM_UNSUBSCRIBE_GLOB

        headers = parse_simple_headers(flags, payload, _glob_headers)
        glob = headers["x-glob"].decode("utf-8")
        return B2S_ConfirmUnsubscribeGlob(
            type=type,
            glob=glob,
        )


if TYPE_CHECKING:
    ___: Type[B2S_MessageParser[B2S_ConfirmUnsubscribeGlob]] = (
        B2S_ConfirmUnsubscribeGlobParser
    )


def serialize_b2s_confirm_unsubscribe_glob(
    msg: B2S_ConfirmUnsubscribeGlob, /, *, minimal_headers: bool
) -> Union[bytes, bytearray, memoryview]:
    """Satisfies MessageSerializer[B2S_ConfirmUnsubscribeGlob]"""
    return serialize_simple_message(
        type=msg.type,
        header_names=_glob_headers,
        header_values=(msg.glob.encode("utf-8"),),
        minimal_headers=minimal_headers,
        payload=b"",
    )


if TYPE_CHECKING:
    ____: MessageSerializer[B2S_ConfirmUnsubscribeGlob] = (
        serialize_b2s_confirm_unsubscribe_glob
    )


B2S_ConfirmUnsubscribe = Union[B2S_ConfirmUnsubscribeExact, B2S_ConfirmUnsubscribeGlob]
