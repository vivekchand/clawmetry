"""A session title never leaves the machine in a form the service can read.

`sync.py::split_session_title` is the mechanism (shipped in #5150, released in
0.12.772). It returns a pair: a NEUTRAL identifier for the server-parsed row,
and the readable title sealed in an encrypted companion the cloud stores but
cannot open.

This file exists because the criteria below were briefly verified by a
DIFFERENT mechanism of mine, which was reverted as redundant. Drift Bot caught
that removing my implementation also removed the only tests holding these
criteria to anything, and it was right to. The criteria did not go away with my
code; they belong to the mechanism that actually ships, so they are verified
against that:

* AC-OBS-RSO-032.1 -- a title is never transmitted in a readable form.
* AC-OBS-RSO-032.2 -- titles ride the encrypted path, matchable to their session.
* AC-OBS-RSO-032.3 -- no title of its own means carry nothing, not an id.
* AC-OBS-RSO-032.4 -- a failure degrades to no title, never to a broken push.
"""

from __future__ import annotations

import base64

from clawmetry.sync import decrypt_payload, split_session_title

# A real 32-byte urlsafe-b64 key, the shape `clawmetry connect` writes.
KEY = base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip('=')

# The failure mode this whole area exists to prevent: a runtime that gives a
# session no title of its own, so the daemon falls back to the user's words.
USER_WORDS = 'how needed is the network drive mounting here?'
SESSION_ID = 'claude_code:11111111-2222-3333-4444-555555555555'


def test_the_readable_row_never_carries_the_title():
    """AC-OBS-RSO-032.1"""
    clear, blob = split_session_title(USER_WORDS, KEY, SESSION_ID)
    assert clear == SESSION_ID
    assert USER_WORDS not in clear
    assert blob and USER_WORDS not in blob


def test_the_title_survives_the_round_trip_and_stays_matchable():
    """AC-OBS-RSO-032.2

    The cleartext half must remain the session's own identifier: that is what
    lets a reader match a decrypted title back to the row it belongs to. A
    neutral-but-arbitrary label would be private and useless.
    """
    clear, blob = split_session_title(USER_WORDS, KEY, SESSION_ID)
    assert decrypt_payload(blob, KEY) == {'display_name': USER_WORDS}
    assert clear == SESSION_ID


def test_a_session_with_no_title_of_its_own_carries_nothing():
    """AC-OBS-RSO-032.3 -- an identifier is not a title, and must not be
    dressed up as one by sealing it into the companion field."""
    assert split_session_title(SESSION_ID, KEY, SESSION_ID) == (SESSION_ID, None)
    assert split_session_title('', KEY, SESSION_ID) == (SESSION_ID, None)
    assert split_session_title('   ', KEY, SESSION_ID) == (SESSION_ID, None)


def test_a_machine_with_no_key_sends_the_fallback_and_never_the_title():
    """AC-OBS-RSO-032.4, and the sharpest edge in the whole design.

    'No key' must degrade to NO TITLE. Degrading to a readable title would be
    the exact defect the mechanism exists to remove, reintroduced by the
    error path rather than the happy path.
    """
    for missing in (None, ''):
        clear, blob = split_session_title(USER_WORDS, missing, SESSION_ID)
        assert clear == SESSION_ID
        assert blob is None


def test_a_broken_key_loses_the_title_rather_than_leaking_it():
    """AC-OBS-RSO-032.4 -- encryption that cannot run must not fall back to
    plaintext. Losing a title is a cosmetic bug; leaking one is not."""
    clear, blob = split_session_title(USER_WORDS, 'not-a-valid-key!!', SESSION_ID)
    assert clear == SESSION_ID
    assert blob is None or USER_WORDS not in blob
