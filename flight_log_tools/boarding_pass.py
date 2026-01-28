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
        # 17. Field Size of Following Structured Message - Repeated
        {'num': 17, 'length': 2},
        # 142. Airline Numeric Code
        {'num': 142, 'length': 3},
        # 143. Document Form/Serial Number
        {'num': 143, 'length': 10},
        # 18. Selectee Indicator
        {'num': 18, 'length': 1},
        # 108. International Documentation Verification
        {'num': 108, 'length': 1},
        # 19. Marketing Carrier Designator
        {'num': 19, 'length': 3},
        # 20. Frequent Flier Airline Designator
        {'num': 20, 'length': 3},
        # 236. Frequent Flier Number
        {'num': 236, 'length': 16},
        # 89. ID/AD Indicator
        {'num': 89, 'length': 1},
        # 118. Free Baggage Allowance
        {'num': 118, 'length': 3},
        # 254. Fast Track
        {'num': 254, 'length': 1},
    ],
    "airline_repeated": [
        # 4. For Individual Airline Use (variable length)
        {'num': 4, 'length': None},
    ],
    "security": [
        # 25. Beginning of Security Data
        {'num': 25, 'length': 1},
        # 28. Type of Security Data
        {'num': 28, 'length': 1},
        # 29. Length of Security Data
        {'num': 29, 'length': 2},
        # 30. Security Data (variable length)
        {'num': 30, 'length': None}
    ]
}

class BoardingPass():
    """Represents a Bar-Coded Boarding Pass (BCBP)."""
    def __init__(self, bcbp_str):
        self.bcbp_str = bcbp_str
        self.data_len = len(self.bcbp_str)
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
            leg_data = {}
            # MANDATORY REPEATED
            mand_r_parse = self.__parse_mand_r(cursor)
            if mand_r_parse is None:
                return None
            mand_r = mand_r_parse['data']
            leg_data['mandatory'] = mand_r
            try:
                cond_air_len = int(mand_r[6], 16)
            except ValueError:
                return None
            # Set cursor to end of this leg's mand_r block.
            cursor += mand_r_parse['length']
            leg_end = cursor + cond_air_len

            if cond_air_len == 0:
                # No conditional or airline items
                continue

            if leg == 0:
                # CONDITIONAL UNIQUE
                cond_u_parse = self.__parse_cond_u(cursor)
                if cond_u_parse is None:
                    return None
                cond_u = cond_u_parse['data']
                cursor += cond_u_parse['length']
                if cond_air_len == cond_u_parse['length']:
                    # No repeated conditional or airline items
                    continue

            # CONDITIONAL REPEAT
            cond_r_parse = self.__parse_cond_r(cursor)
            if cond_r_parse is None:
                return None
            cond_r = cond_r_parse['data']
            leg_data['conditional'] = cond_r
            # Set cursor to end of this leg's cond_r block:
            cursor += cond_r_parse['length']

            if cursor > leg_end:
                # Boarding pass data had invalid lengths.
                return None
            if cursor < leg_end:
                # Airline data exists.
                leg_data['airline'] = self.__parse_airline(cursor, leg_end)

            # Set cursor to leg end and save leg data.
            cursor = leg_end
            legs.append(leg_data)

        # SECURITY
        security = None
        if cursor > self.data_len:
            # Boarding pass data had invalid lengths.
            return None
        if cursor < self.data_len:
            security_parse = self.__parse_security(cursor)
            security = security_parse['data']
            # Set cursor to end of security.
            cursor += security_parse['length']

        # LEFTOVER UNKNOWN DATA
        unknown = None
        if cursor < self.data_len:
            unknown = {0: self.bcbp_str[cursor:self.data_len]}

        # Build fields dict.
        fields = {}
        fields['mandatory'] = mand_u
        if cond_u is not None:
            fields['conditional'] = cond_u
        fields['legs'] = legs
        if security is not None:
            fields['security'] = security
        if unknown is not None:
            fields['unknown'] = unknown
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
        return self.__parse_cond(
            offset,
            _BCBP_FIELDS['conditional_unique'],
            10, # Field Size of Following Structured Message - Unique
        )

    def __parse_cond_r(self, offset):
        """Parses a conditional repeat block starting at offset."""
        return self.__parse_cond(
            offset,
            _BCBP_FIELDS['conditional_repeated'],
            17, # Field Size of Following Structured Message - Unique
        )

    def __parse_cond(self, offset, fields, following_length_field_id):
        """
        Parses a conditional block.

        Conditional blocks have a field (identified by
        following_field_length_id) indicating the length of the block
        after it. Fields are populated in order until the length is
        reached.
        """
        raw = self.bcbp_str
        cond = {}
        lengths = [v['length'] for v in fields]
        fol_offset = None # Start of "following" block
        fol_len = None # Length of "following" block
        for i, f in enumerate(fields):
            start = offset + sum(lengths[0:i])
            stop = start + f['length']
            if fol_len is not None:
                remaining_size = fol_offset + fol_len - start
                if remaining_size <= 0:
                    # No size remains.
                    break
                if remaining_size < f['length']:
                    # Field is longer than remaining size; truncate.
                    stop = start + remaining_size
            value_str = raw[start:stop]
            cond[f['num']] = value_str
            if f['num'] == following_length_field_id:
                # Parse the following field size.
                try:
                    fol_len = int(value_str, 16)
                    fol_offset = stop
                except ValueError:
                    return None
        return {'length': (fol_offset - offset) + fol_len, 'data': cond}

    def __parse_airline(self, offset_start, offset_end):
        """Parses airline data."""
        raw = self.bcbp_str
        field_id = _BCBP_FIELDS['airline_repeated'][0]['num']
        return {field_id: raw[offset_start:offset_end]}

    def __parse_security(self, offset):
        """Parses security data."""
        raw = self.bcbp_str
        security = {}
        fields = _BCBP_FIELDS['security']
        if raw[offset:offset+1] == "^":
            # Properly formatted security data.
            lengths = [v['length'] for v in fields if v['length'] is not None]
            for i, f in enumerate(fields[0:3]):
                start = offset + sum(lengths[0:i])
                stop = start + f['length']
                security[f['num']] = raw[start:stop]
            # Get security data length from field 29.
            try:
                sec_data_len = int(security[29], 16)
            except ValueError:
                return None
            sec_offset = offset + sum(lengths)
            if sec_offset + sec_data_len > self.data_len:
                sec_data_len = self.data_len - sec_offset
            security[fields[-1]['num']] = raw[
                sec_offset:sec_offset+sec_data_len
            ]
            length = (sec_offset - offset) + sec_data_len
        else:
            # Improperly formatted security data. Treat the rest of the
            # boarding pass as security data.
            security[fields[-1]['num']] = raw[offset:self.data_len]
            length = self.data_len - offset
        return {'length': length, 'data': security}
