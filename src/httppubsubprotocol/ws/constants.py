from enum import IntEnum, IntFlag, auto


class PubSubWSMessageFlags(IntFlag):
    MINIMAL_HEADERS = 1 << 0
    """Our websocket message bodies include a headers section. This is not
    related to the headers within the HTTP / WS protocol. Our headers take one
    of two formats, depending on if this flag is set or not.

    If this flag is set, the broadcaster and subscriber agree on the headers
    that should be sent in each packet, and only send the values.

    If this flag is not set, the sender expresses the headers with (key, value)
    pairs, allowing more flexibility for a version mismatch but also more
    overhead.

    Typically it's helpful to turn this off when in the process of updating the
    server and clients, then turn it on when all broadcasters and subscribers
    are on the same version.

    Individual header names and values are always restricted to no more than
    65535 bytes.
    """


class SubscriberToBroadcasterWSMessageType(IntEnum):
    """Assigns a unique integer to each type of message that a subscriber can
    send to a broadcaster.
    """

    CONFIGURE = auto()
    """The first packet sent over the wire. Provides additional information to
    the broadcaster for how to handle the connection, as well as facilitating
    the generation of a shared public key, required for some authorization
    protocols. This shared public key is referred to as a `connection nonce`
    or just `nonce` in the future and is generated by 
    `SHA256(subscriber_nonce CONCAT broadcaster_nonce)`

    
    ### headers 
    - x-subscriber-nonce: 32 random bytes representing the subscriber's contribution
        to the nonce. The broadcaster will provide its contribution in the response.
    - x-enable-zstd: 1 byte, big-endian, unsigned. 0 to disable zstandard compression,
        1 to indicate the client is willing to receive zstandard compressed messages.
    - x-enable-training: 1 byte, big-endian, unsigned. 0 to indicate the client will not
      accept custom compression dictionaries, 1 to indicate the client may accept them.
    - x-initial-dict: 2 bytes, big-endian, unsigned. 0 to indicate the client does not
      have a specific preset dictionary in mind to use, otherwise, the id of the preset
      dictionary the client thinks is a good fit for this connection

    ### body
    none
    """

    SUBSCRIBE_EXACT = auto()
    """Indicates the subscriber wants to receive messages on a specific topic. If
    already subscribed, the broadcaster will disconnect the subscriber.
    
    ### headers 
    - authorization (url: websocket:<nonce>:<ctr>)
    - x-topic: the topic to subscribe to

    ### body
    none
    """

    SUBSCRIBE_GLOB = auto()
    """Indicates the subscriber wants to receive messages to any topic matching the pattern. If
    already subscribed to this exact glob, the broadcaster will disconnect the subscriber.
    
    ### headers
    - authorization (url: websocket:<nonce>:<ctr>)
    - x-glob: the glob pattern to subscribe to (must be valid utf-8)

    ### body
    none
    """

    UNSUBSCRIBE_EXACT = auto()
    """Undoes the effect of a previous SUBSCRIBE_EXACT message. If not subscribed,
    the broadcaster will disconnect the subscriber.
    
    ### headers 
    - authorization (url: websocket:<nonce>:<ctr>)
    - x-topic: the topic to unsubscribe from

    ### body
    none
    """

    UNSUBSCRIBE_GLOB = auto()
    """Undoes the effect of a previous SUBSCRIBE_GLOB message. If not subscribed,
    the broadcaster will disconnect the subscriber.

    ### headers
    - authorization (url: websocket:<nonce>:<ctr>)
    - x-glob: the glob pattern to unsubscribe from

    ### body
    none
    """

    NOTIFY = auto()
    """Informs the broadcaster of a new message to be sent to subscribers of a 
    particular topic. The entire message must go within a single websocket frame
    for this message type; use NOTIFY_STREAM for larger messages

    
    ### headers
    - authorization (url: websocket:<nonce>:<ctr>, see below)
    - x-identifier identifies the notification so the broadcaster can confirm it
    - x-topic is the topic of the notification
    - x-compressor is a big-endian unsigned integer representing one of the previous
      compression methods enabled by the broadcaster
    - x-compressed-length the total length of the compressed body, big-endian, unsigned, max 8 bytes
    - x-decompressed-length the total length of the decompressed body, big-endian, unsigned, max 8 bytes
    - x-compressed-sha512 the sha-512 hash of the compressed content once all parts are concatenated, 64 bytes

    ### body

    the message to send. must have the same hash as the provided hash
    """

    NOTIFY_STREAM = auto()
    """Like notify, asks the broadcaster to send a message to subscribers of a
    particular topic, but allows the message to be split into multiple websocket
    messages (which are themselves potentially split into multiple frames).

    Splitting websocket messages is theoretically redundant as it's already
    handled by the protocol, but in practice websocket message sizes are limited
    to relatively small values (e.g., 16mb) as each step in the process is expecting
    to hold them in memory (often resulting in multiple copies at once)

    NOTE: Notifications may never be weaved. Each notify must complete normally before
    the next can be started or the broadcaster will disconnect the subscriber.

    ### headers

    The following 3 headers are always required, and when using minimal headers, they
    always appear first and in this order:

    - authorization (url: websocket:<nonce>:<ctr>)
    - x-identifier relates the different websocket messages. arbitrary blob, max 64 bytes
    - x-part-id starts at 0 and increments by 1 for each part. unsigned, big-endian, max 8 bytes
    
    If `x-part-id` is 0, the following headers are also required, and when using minimal headers,
    they always appear after the first 3 headers and in this order:

    - x-topic the topic of the notification
    - x-compressor identifiers which compressor (if any) was used for the body. 0 for no compression.
      big-endian, unsigned, max 8 bytes
    - x-compressed-length the total length of the compressed body, big-endian, unsigned, max 8 bytes
    - x-decompressed-length the total length of the decompressed body, big-endian, unsigned, max 8 bytes
    - x-compressed-sha512 the sha-512 hash of the compressed content once all parts are concatenated, 64 bytes

    ### body

    blob of data to append to the compressed notification body
    """

    CONTINUE_RECEIVE = auto()
    """Indicates that the subscriber is ready to receive more data for a notification

    ### headers
    - x-identifier: the identifier of the notification the subscriber needs more parts for
    - x-part-id: the part id that the subscriber received up to, big-endian, unsigned, max 8 bytes

    ### body
    none
    """

    CONFIRM_RECEIVE = auto()
    """Indicates that the subscriber received the notification and finished processing it.

    ### headers
    - x-identifier: the identifier of the notification that was received

    ### body
    none
    """


class BroadcasterToSubscriberWSMessageType(IntEnum):
    """Assigns a unique integer to each type of message that a broadcaster can
    send to a subscriber.
    """

    CONFIRM_CONFIGURE = auto()
    """Indicates that the broadcaster has finished processing a configure message
    sent by the subscriber. Also includes the broadcasters contribution to the
    connections shared public key, required for some authorization protocols.

    ### headers
    - `x-broadcaster-nonce`: (32 bytes)
        the broadcasters contribution for random bytes to the nonce.
        the connection nonce is SHA256(subscriber_nonce CONCAT broadcaster_nonce),
        which is used in the url for generating the authorization header
        when the broadcaster sends a notification to the receiver over
        this websocket and when the subscriber subscribers to a topic over
        this websocket.

        the url is of the form `websocket:<nonce>:<ctr>`, where the ctr is
        a signed 8-byte integer that starts at 1 (or -1) and that depends on if it
        was sent by the broadcaster or subscriber. Both the subscriber and
        broadcaster keep track of both counters; the subscribers counter
        is always negative and decremented by 1 after each subscribe or unsubscribe
        request, the broadcasters counter is always positive and incremented by 1 after
        each notification sent. The nonce is base64url encoded, the ctr is
        hex encoded without a leading 0x and unpadded, e.g.,
        `websocket:abc123:10ffffffffffffff` or `websocket:abc123:-1a`. note that
        the counter changes every time an authorization header is provided,
        even within a single "operation", so e.g. a Notify Stream message broken
        into 6 parts will change the counter 6 times.
    
    ### body

    none
    """

    CONFIRM_SUBSCRIBE_EXACT = auto()
    """
    Indicates that the subscriber will receive notifications for the given topic

    ### headers
    - x-topic: the topic that the subscriber is now subscribed to

    ### body
    none
    """

    CONFIRM_SUBSCRIBE_GLOB = auto()
    """
    Indicates that the subscriber will receive notifications for topics that match
    the given glob pattern

    NOTE: 
        Glob patterns are considered independently. If you subscribe to foo/* and foo/bar/*,
        you will receive a confirmation of foo/* followed by foo/bar/*. On websockets,
        the notifications will be deduplicated so you will only receive one RECEIVE for
        `foo/bar/123` in this case.

    ### headers
    - x-glob: the glob pattern that the subscriber is now subscribed to

    ### body
    none
    """

    CONFIRM_UNSUBSCRIBE_EXACT = auto()
    """
    Indicates that the subscriber will no longer receive notifications for the given topic

    ### headers
    - x-topic: the topic that the subscriber is now unsubscribed from

    ### body
    none
    """

    CONFIRM_UNSUBSCRIBE_GLOB = auto()
    """
    Indicates that the subscriber will no longer receive notifications for topics that match
    the given glob pattern.

    NOTE: Glob patterns are considered independently

    ### headers
    - x-glob: the glob pattern that the subscriber is now unsubscribed from

    ### body
    none
    """

    CONFIRM_NOTIFY = auto()
    """
    Indicates that the broadcaster received the notification and finished processing it.
    This is sent in response to NOTIFY messages and the last NOTIFY STREAM message of
    a notification.

    ### headers
    - x-identifier: the identifier of the notification that was sent
    - x-subscribers: the number of subscribers that received the notification, big-endian,
        unsigned, max 8 bytes

    ### body
    none
    """

    CONTINUE_NOTIFY = auto()
    """
    Sent in response to a NOTIFY_STREAM message to indicate that the broadcaster
    is expecting more data for the notification.

    ### headers
    - x-identifier: the identifier of the notification the broadcaster needs more parts for
    - x-part-id: the part id that broadcaster received up to, big-endian, unsigned, max 8 bytes

    ### body
    none
    """

    RECEIVE_STREAM = auto()
    """Used to tell the subscriber about a message on a topic it is subscribed to,
    possibly over multiple websocket messages.

    NOTE: Notifications may never be weaved. Each notify must complete normally before
    the next can be started or the subscriber will disconnect. 

    ### headers

    The following 3 headers are always required, and when using minimal headers, they
    always appear first and in this order:

    - authorization (url: websocket:<nonce>:<ctr>)
    - x-identifier relates the different websocket messages. arbitrary blob, max 64 bytes
    - x-part-id starts at 0 and increments by 1 for each part. unsigned, big-endian, max 8 bytes
    
    If `x-part-id` is 0, the following headers are also required, and when using minimal headers,
    they always appear after the first 3 headers and in this order:

    - x-topic the topic of the notification
    - x-compressor identifiers which compressor (if any) was used for the body. 0 for no compression.
      big-endian, unsigned, max 8 bytes
    - x-compressed-length the total length of the compressed body, big-endian, unsigned, max 8 bytes
    - x-decompressed-length the total length of the decompressed body, big-endian, unsigned, max 8 bytes
    - x-compressed-sha512 the sha-512 hash of the compressed content once all parts are concatenated, 64 bytes

    ### body
    blob of data to append to the compressed notification body
    """

    ENABLE_ZSTD_PRESET = auto()
    """Indicates that the broadcaster may start sending, and will accept, data compressed
    using the given preset dictionary. The special dictionary id `1` is reserved to mean
    compression without a custom dictionary (i.e., the dictionary is sent alongside the
    data), and `0` is reserved to mean no compression and is never used in this message.

    A preset dictionary is one with, through some other means than this protocol, the
    broadcasters and subscribers can both agree on the contents of the dictionary without
    actually sending any data. This typically means they just have them on their local disk

    ### headers
    x-identifier: which compressor is enabled, unsigned, big-endian, max 2 bytes, min 1.
        A value of 1 means compression without a custom dictionary.
    x-compression-level: what compression level the broadcaster will use with
        this dictionary. signed, big-endian, max 2 bytes, max 22. the subscriber
        is free to choose a different compression level
    x-min-size: 4 bytes, big-endian, unsigned. a hint to the subscriber for the smallest
        payload the broadcaster will apply this compressor to. the subscriber can use this
        compressor on smaller messages if it wants
    x-max-size: 8 bytes, big-endian, unsigned. a hint to the susbcriber for the largest
        payload for which the broadcaster will use this compressor. uses 2**64-1 to indicate
        no upper bound. the client can use this compressor on larger messages if it wants

    ### body
    none
    """

    ENABLE_ZSTD_CUSTOM = auto()
    """Indicates that the broadcaster may start sending, and will accept, data compressed
    using a dictionary which it will send along with this message. The broadcaster generated
    this dictionary by training on the data that has been passed along the websocket so far.
    This dictionary is intended to utilize very specific properties of the messages as they
    are right now; for example, if timestamps are often included in the message in JSON, they 
    will probably all have the same starting prefix which will likely be in the dictionary.

    The broadcaster will retrain the dictionary with some regularity so it can continue to
    take advantage of the most recent data.

    The broadcaster will only accept at most the last 2 custom dictionaries and will only use
    the most recent one.

    ### headers
    x-identifier: the identifier assigned to the compressor formed with this dictionary.
        unsigned, big-endian, max 8 bytes, min 65536
    x-compression-level: what compression level the broadcaster will use with
        this dictionary. signed, big-endian, max 2 bytes, max 22. the subscriber
        is free to choose a different compression level
    x-min-size: 4 bytes, big-endian, unsigned. a hint to the subscriber for the smallest
        payload the broadcaster will apply this compressor to. the subscriber can use this
        compressor on smaller messages if it wants
    x-max-size: 8 bytes, big-endian, unsigned. a hint to the susbcriber for the largest
        payload for which the broadcaster will use this compressor. uses 2**64-1 to indicate
        no upper bound. the client can use this compressor on larger messages if it wants

    ### body
    the dictionary to use for compression
    """
