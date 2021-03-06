import struct

from .consts import FieldType


__all__ = ['Column']


class Column(object):
    """Definition of a column
    """

    def __init__(self, *args, **kwargs):
        self.data = {}
        if len(args) == 3:
            self._parse_column_definition(*args)
        else:
            self.data = kwargs

    def _parse_column_definition(self, column_type, column_schema, packet):
        self.data["type"] = column_type
        self.data["name"] = column_schema["COLUMN_NAME"]
        self.data["collation_name"] = column_schema["COLLATION_NAME"]
        self.data["character_set_name"] = column_schema["CHARACTER_SET_NAME"]
        self.data["comment"] = column_schema["COLUMN_COMMENT"]
        self.data["unsigned"] = False
        self.data["type_is_bool"] = False
        if column_schema["COLUMN_KEY"] == "PRI":
            self.data["is_primary"] = True
        else:
            self.data["is_primary"] = False

        if column_schema["COLUMN_TYPE"].find("unsigned") != -1:
            self.data["unsigned"] = True
        if self.type == FieldType.VAR_STRING or \
                self.type == FieldType.STRING:
            self._read_string_metadata(packet, column_schema)
        elif self.type == FieldType.VARCHAR:
            self.data["max_length"] = struct.unpack('<H', packet.read(2))[0]
        elif self.type == FieldType.BLOB:
            self.data["length_size"] = packet.read_uint8()
        elif self.type == FieldType.GEOMETRY:
            self.data["length_size"] = packet.read_uint8()
        elif self.type == FieldType.NEWDECIMAL:
            self.data["precision"] = packet.read_uint8()
            self.data["decimals"] = packet.read_uint8()
        elif self.type == FieldType.DOUBLE:
            self.data["size"] = packet.read_uint8()
        elif self.type == FieldType.FLOAT:
            self.data["size"] = packet.read_uint8()
        elif self.type == FieldType.BIT:
            bits = packet.read_uint8()
            bytes = packet.read_uint8()
            self.data["bits"] = (bytes * 8) + bits
            self.data["bytes"] = int((self.bits + 7) / 8)
        elif self.type == FieldType.TIMESTAMP2:
            self.data["fsp"] = packet.read_uint8()
        elif self.type == FieldType.DATETIME2:
            self.data["fsp"] = packet.read_uint8()
        elif self.type == FieldType.TIME2:
            self.data["fsp"] = packet.read_uint8()
        elif self.type == FieldType.TINY and \
                column_schema["COLUMN_TYPE"] == "tinyint(1)":
            self.data["type_is_bool"] = True

    def _read_string_metadata(self, packet, column_schema):
        metadata = (packet.read_uint8() << 8) + packet.read_uint8()
        real_type = metadata >> 8
        if real_type == FieldType.SET or real_type == FieldType.ENUM:
            self.data["type"] = real_type
            self.data["size"] = metadata & 0x00ff
            self.__read_enum_metadata(column_schema)
        else:
            self.data["max_length"] = (((metadata >> 4) & 0x300) ^ 0x300) \
                + (metadata & 0x00ff)

    def __read_enum_metadata(self, column_schema):
        enums = column_schema["COLUMN_TYPE"]
        if self.type == FieldType.ENUM:
            self.data["enum_values"] = enums.replace('enum(', '')\
                .replace(')', '').replace('\'', '').split(',')
        else:
            self.data["set_values"] = enums.replace('set(', '')\
                .replace(')', '').replace('\'', '').split(',')

    def __eq__(self, other):
        return self.data == other.data

    def __ne__(self, other):
        return not self.__eq__(other)

    def serializable_data(self):
        return self.data

    def __getattr__(self, item):
        try:
            return self.data[item]
        except KeyError:
            raise AttributeError("{0} not found".format(item))
