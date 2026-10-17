# Ka-50 multi-position discrete audit

For each control, verify that the integer position index used in `Ka-50V2.py`
still selects the intended cockpit position under the canonical positionMap.
BIOS positions are listed in the order DCS BIOS enumerated them; canonical
positionMap (when present) reflects the new mapping order.
