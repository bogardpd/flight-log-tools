"""Tools for interacting with boarding passes."""

_BCBP_FIELDS = {
    "mandatory_unique": [
        # 1. Format Code
        {'num': 1, 'length': 1},
        # 5. Number of Legs Encoded
        {'num': 5, 'length': 1},
        # 11. Passenger Name
        {'num': 11, 'length': 20},
        # 253. Electronic Ticket Indicator
        {'num': 253, 'length': 1},
    ],
    "mandatory_repeated": [
         # 7. Operating carrier PNR Code
        {'num': 7, 'length': 7},
        # 26. From City Airport Code
        {'num': 26, 'length': 3},
        # 38. To City Airport Code
        {'num': 38, 'length': 3},
        # 42. Operating carrier Designator
        {'num': 42, 'length': 3},
        # 43. Flight Number
        {'num': 43, 'length': 5},
        # 46. Date of Flight (Julian Date)
        {'num': 46, 'length': 3},
        # 71. Compartment Code
        {'num': 71, 'length': 1},
        # 104. Seat Number
        {'num': 104, 'length': 4},
        # 107. Check-in Sequence Number
        {'num': 107, 'length': 5},
        # 113. Passenger Status
        {'num': 113, 'length': 1},
        # 6. Field size of variable size field (Conditional + Airline
        # item 4) in hexadecimal
        {'num': 6, 'length': 2},
    ],
    "conditional_unique": [
        # 8. Beginning of Version Number
        {'num': 8, 'length': 1},
        # 9. Version Number
        {'num': 9, 'length': 1},
        # 10. Field Size of Following Structured Message - Unique
        {'num': 10, 'length': 2},
        # 15. Passenger Description
        {'num': 15, 'length': 1},
        # 12. Source of Check-in
        {'num': 12, 'length': 1},
        # 14. Source of Boarding Pass Issuance
        {'num': 14, 'length': 1},
        # 22. Date of Issue of Boarding Pass (Julian Date)
        {'num': 22, 'length': 4},
        # 16. Document type
        {'num': 16, 'length': 1},
        # 21. Airline Designator of Boarding Pass Issuer
        {'num': 21, 'length': 3},
        # 23. Baggage Tag License Plate Number
        {'num': 23, 'length': 13},
        # 31. 1st Non-Consecutive Baggage Tag License Plate
        # Number
        {'num': 31, 'length': 13},
        # 31. 2nd Non-Consecutive Baggage Tag License Plate
        # Number
        {'num': 32, 'length': 13},
    ],
    "conditional_repeated": [

    ]
}

class BoardingPass():
    """Represents a Bar-Coded Boarding Pass (BCBP)."""
    def __init__(self, bcbp_str):
        self.bcbp_str = bcbp_str
        self.data = self.__parse()

    def __str__(self):
        return self.bcbp_str.replace(" ", "·")

    def __parse(self):
        """Parses a boarding pass and returns a dict."""
        # Keep track of start of current block throughout parsing.
        cursor = 0

        # MANDATORY UNIQUE
        mand_u_parse = self.__parse_mand_u()
        mand_u = mand_u_parse['data']
        try:
            self.leg_count = int(mand_u[5])
        except ValueError:
            return None
        # Set offset to end of mand_u block.
        cursor = mand_u_parse['length']

        cond_u = None
        legs = []
        for leg in range(self.leg_count):
            # MANDATORY REPEATED
            mand_r_parse = self.__parse_mand_r(cursor)
            mand_r = mand_r_parse['data']
            try:
                cond_air_len = int(mand_r[6], 16)
            except ValueError:
                return None
            # Set cursor to end of this leg's mand_r block.
            cursor += mand_r_parse['length']

            if cond_air_len == 0:
                # No conditional or airline items
                continue

            if leg == 0:
                # CONDITIONAL UNIQUE
                cond_u_parse = self.__parse_cond_u(cursor)
                if cond_u_parse is None:
                    return None
                cond_u = cond_u_parse['data']
                cond_u_size = cond_u_parse['length']
            else:
                # No conditional unique.
                cond_u_size = 0


            legs.append({'mandatory': mand_r})


        # Build fields dict
        fields = {}
        fields['mandatory'] = mand_u
        if cond_u is not None:
            fields['conditional'] = cond_u
        fields['legs'] = legs
        return fields

    def __parse_mand_u(self):
        """Parses the mandatory unique block."""
        raw = self.bcbp_str
        mand_u = {}
        fields = _BCBP_FIELDS['mandatory_unique']
        lengths = [v['length'] for v in fields]
        for i, f in enumerate(fields):
            start = sum(lengths[0:i])
            stop = start + f['length']
            mand_u[f['num']] = raw[start:stop]
        return {'length': sum(lengths), 'data': mand_u}

    def __parse_mand_r(self, offset):
        """Parses a mandatory repeat block starting at the offset."""
        raw = self.bcbp_str
        mand_r = {}
        fields = _BCBP_FIELDS['mandatory_repeated']
        lengths = [v['length'] for v in fields]
        for i, f in enumerate(fields):
            start = offset + sum(lengths[0:i])
            stop = start + f['length']
            mand_r[f['num']] = raw[start:stop]
        return {'length': sum(lengths), 'data': mand_r}

    def __parse_cond_u(self, offset):
        """Parses a conditional unique block starting at offset."""
        raw = self.bcbp_str
        cond_u = {}

        fields = _BCBP_FIELDS['conditional_unique']
        lengths = [v['length'] for v in fields]
        fol_offset = None
        fol_len = None
        for i, f in enumerate(fields):
            start = offset + sum(lengths[0:i])
            if fol_len is not None and start >= fol_offset + fol_len:
                break
            stop = start + f['length']
            value_str = raw[start:stop]
            cond_u[f['num']] = value_str
            if f['num'] == 10:
                # Try to parse following field size.
                try:
                    fol_len = int(value_str, 16)
                    fol_offset = stop
                except ValueError:
                    return None
                valid_fol_lens = [
                    sum(lengths[i+1:j]) for j in range(i+1,len(lengths))
                ]
                if fol_len not in valid_fol_lens:
                    return None

        return {'length': sum(lengths), 'data': cond_u}
