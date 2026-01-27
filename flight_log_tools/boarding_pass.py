"""Tools for interacting with boarding passes."""

class BoardingPass():
    """Represents a Bar-Coded Boarding Pass (BCBP)."""
    def __init__(self, bcbp_str):
        self.bcbp_str = bcbp_str
        self.data = self.__parse()

    def __str__(self):
        return self.bcbp_str.replace(" ", "·")

    def __parse(self):
        """Parses a boarding pass and returns a dict."""
        raw = self.bcbp_str

        fields = {}

        mand_u = {} # MANDATORY UNIQUE
        # 1. Format Code
        mand_u[1] = raw[0:1]
        # 5. Number of Legs Encoded
        mand_u[5] = raw[1:2]
        try:
            num_legs = int(mand_u[5])
        except ValueError:
            return None
        # 11. Passenger Name
        mand_u[11] = raw[2:22]
        # 253. Electronic Ticket Indicator
        mand_u[253] = raw[22:23]

        cond_u = {}
        legs = []
        chr_i = 23 # Track character index of start of current section
        for leg in range(num_legs):
            # TODO: Write __parse_mand_r(offset)
            mand_r = {} # MANDATORY REPEATED
            # 7. Operating carrier PNR Code
            mand_r[7] = raw[chr_i:chr_i+7]
            # 26. From City Airport Code
            mand_r[26] = raw[chr_i+7:chr_i+10]
            # 38. To City Airport Code
            mand_r[38] = raw[chr_i+10:chr_i+13]
            # 42. Operating carrier Designator
            mand_r[42] = raw[chr_i+13:chr_i+16]
            # 43. Flight Number
            mand_r[43] = raw[chr_i+16:chr_i+21]
            # 46. Date of Flight (Julian Date)
            mand_r[46] = raw[chr_i+21:chr_i+24]
            # 71. Compartment Code
            mand_r[71] = raw[chr_i+24:chr_i+25]
            # 104. Seat Number
            mand_r[104] = raw[chr_i+25:chr_i+29]
            # 107. Check-in Sequence Number
            mand_r[107] = raw[chr_i+29:chr_i+34]
            # 113. Passenger Status
            mand_r[113] = raw[chr_i+34:chr_i+35]
            # 6. Field size of variable size field (Conditional +
            # Airline item 4) in hexadecimal
            mand_r[6] = raw[chr_i+35:chr_i+37]
            try:
                size_cond_air = int(mand_r[6], 16)
            except ValueError:
                return None
            cond_u_offset = chr_i + 37

            if size_cond_air == 0:
                # No conditional or airline items
                chr_i = cond_u_offset # Update character index
                continue
            if leg == 0:
                # CONDITIONAL UNIQUE
                cond_u_parse = self.__parse_cond_u(cond_u_offset)
                if cond_u_parse is None:
                    return None
                cond_u = cond_u_parse['cond_u']
                cond_u_size = cond_u_parse['length']
            else:
                # No conditional unique.
                cond_u_size = 0

            cond_r_offset = chr_i + 37 + cond_u_size


            chr_i = chr_i + 37 + size_cond_air # Update character index
            legs.append({'mandatory': mand_r})


        # Build fields dict
        fields['mandatory'] = mand_u
        fields['conditional'] = cond_u
        fields['legs'] = legs
        return fields

    def __parse_cond_u(self, offset):
        """Parses a conditional unique block starting at offset."""
        raw = self.bcbp_str
        cond_u = {}
        cond_u_fields = [
            # 15. Passenger Description
            {"num": 15, "length": 1},
            # 12. Source of Check-in
            {"num": 12, "length": 1},
            # 14. Source of Boarding Pass Issuance
            {"num": 14, "length": 1},
            # 22. Date of Issue of Boarding Pass (Julian Date)
            {"num": 22, "length": 4},
            # 16. Document type
            {"num": 16, "length": 1},
            # 21. Airline Designator of Boarding Pass Issuer
            {"num": 21, "length": 3},
            # 23. Baggage Tag License Plate Number
            {"num": 23, "length": 13},
            # 31. 1st Non-Consecutive Baggage Tag License Plate
            # Number
            {"num": 31, "length": 13},
            # 31. 2nd Non-Consecutive Baggage Tag License Plate
            # Number
            {"num": 32, "length": 13},
        ]
        cond_u_lengths = [v['length'] for v in cond_u_fields]
        valid_cond_u_vals = [
            sum(cond_u_lengths[0:i]) for i in range(len(cond_u_fields))
        ]
        # 8. Beginning of Version Number
        cond_u[8] = raw[offset+0:offset+1]
        # 9. Version Number
        cond_u[9] = raw[offset+1:offset+2]
        # 10. Field Size of Following Structured Message -
        # Unique
        cond_u[10] = raw[offset+2:offset+4]
        print(cond_u)
        try:
            size_cond_u_fol = int(cond_u[10], 16)
        except ValueError:
            return None
        if (size_cond_u_fol) not in valid_cond_u_vals:
            return None

        for i, f in enumerate(cond_u_fields):
            position = sum(cond_u_lengths[0:i])
            if position >= size_cond_u_fol:
                break
            start = offset + 4 + position
            stop = start + f['length']
            cond_u[f['num']] = raw[start:stop]

        return {'length': size_cond_u_fol + 4, 'cond_u': cond_u}
