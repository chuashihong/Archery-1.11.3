# -*- coding: UTF-8 -*-
import base64
import simplejson as json
import psycopg2

from bson import Binary, Code
from decimal import Decimal
from datetime import datetime, date, timedelta
from functools import singledispatch
from ipaddress import IPv4Address, IPv6Address
from uuid import UUID
from bson.objectid import ObjectId
from bson.timestamp import Timestamp
from bson.decimal128 import Decimal128
from bson.regex import Regex

@singledispatch
def convert(o):
    raise TypeError("can not convert type")


@convert.register(datetime)
def _(o):
    return o.strftime("%Y-%m-%d %H:%M:%S")


@convert.register(date)
def _(o):
    return o.strftime("%Y-%m-%d")


@convert.register(timedelta)
def _(o):
    return o.__str__()


@convert.register(Decimal)
def _(o):
    return str(o)


@convert.register(memoryview)
def _(o):
    return str(o)


@convert.register(set)
def _(o):
    return list(o)


@convert.register(UUID)
def _(o):
    return str(o)


@convert.register(IPv4Address)
def _(o):
    return str(o)


@convert.register(IPv6Address)
def _(o):
    return str(o)


@convert.register(ObjectId)
def _(o):
    return str(o)


@convert.register(Timestamp)
def _(o):
    return str(o)


@convert.register(Decimal128)
def _(o):
    return str(o)


@convert.register(Regex)
def _(o):
    return str(o)


class MongoDBJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to a string
        elif isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO format
        elif isinstance(obj, Decimal128):
            return str(obj)  # Convert Decimal128 to a string
        elif isinstance(obj, Binary):
            return obj.hex()  # Convert binary data to a hex string (or use Base64 if needed)
        elif isinstance(obj, Timestamp):
            return int(obj.time)  # Convert Timestamp to integer seconds since epoch
        elif isinstance(obj, Regex):
            return obj.pattern  # Return regex pattern as a string
        elif isinstance(obj, Code):
            return str(obj)  # Convert Code to string representation
        else:
            return super().default(obj)
class ExtendJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return convert(obj)
        except TypeError:
            return super(ExtendJSONEncoder, self).default(obj)


class ExtendJSONEncoderFTime(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, psycopg2._range.DateTimeTZRange):
                return obj.lower.isoformat(" ") + "--" + obj.upper.isoformat(" ")
            elif isinstance(obj, datetime):
                return obj.isoformat(" ")
            else:
                return convert(obj)
        except TypeError:
            return super(ExtendJSONEncoderFTime, self).default(obj)


# 使用simplejson处理形如 b'\xaa' 的bytes类型数据会失败，但使用json模块构造这个对象时不能使用bigint_as_string方法
import json


class ExtendJSONEncoderBytes(json.JSONEncoder):
    def default(self, obj):
        try:
            # 使用convert.register处理会报错 ValueError: Circular reference detected
            # 不是utf-8格式的bytes格式需要先进行base64编码转换
            if isinstance(obj, bytes):
                try:
                    return o.decode("utf-8")
                except:
                    return base64.b64encode(obj).decode("utf-8")
            else:
                return convert(obj)
        except TypeError:
            print(type(obj))
            return super(ExtendJSONEncoderBytes, self).default(obj)
