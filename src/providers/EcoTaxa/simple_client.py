import sys
import typing
from typing import Dict, Optional

from requests import Session
from urllib3.exceptions import HTTPWarning


def detect_list_type(typ):
    """
    Internal method to detect whether an abstract type is a List-type, and if so
    returns the type of the list elements. Returns `None` otherwise.

    :param typ:  The abstract type to be analyzed.
    :return: The type of the list elements, or `None`.
    """

    # Read more about this issue here:
    # https://github.com/swagger-api/swagger-codegen/issues/8921

    if sys.version_info >= (3, 7):
        # noinspection PyProtectedMember,PyUnresolvedReferences
        if type(typ) is typing._GenericAlias and typ._name == "List":  # type:ignore
            return typ.__args__[0]

    elif sys.version_info >= (3, 0):
        try:
            if type(typ) is typing.GenericMeta and (
                hasattr(typ, "__extra__") and typ.__extra__ is list
            ):
                return typ.__args__[0]
        except AttributeError:
            pass

        if hasattr(typ, "__origin__") and typ.__origin__ is typing.List:
            return typ.__args__[0]


class SimpleClient(object):
    """
    An http client based on Requests.
    """

    def __init__(self, base_url: str):
        self.url = base_url
        self.session = Session()
        # Workaround certificate issues, in case
        # self.session.verify = False
        # import urllib3
        # urllib3.disable_warnings()
        # Now OK after https://github.com/ecotaxa/ecotaxa_dev/issues/613#issuecomment-926383293
        self.token: Optional[str] = None

    def _url_headers_args(self, entry_point: str, kwargs: Dict):
        url = self.url + "/api" + entry_point
        if self.token is not None:
            headers = {"Authorization": "Bearer " + self.token}
        else:
            headers = {}
        for an_arg, a_val in kwargs.items():
            if hasattr(a_val, "to_dict"):
                kwargs[an_arg] = a_val.to_dict()
            elif hasattr(a_val, "dict"):
                kwargs[an_arg] = a_val.dict()
        return url, headers

    def get(self, model, entry_point: str, **kwargs):
        url, headers = self._url_headers_args(entry_point, kwargs)
        rsp = self.session.get(url, timeout=30, headers=headers, **kwargs)
        if rsp.status_code == 200:
            if model == typing.IO:
                return rsp.content
            else:
                json_rsp = rsp.json()
                inside = detect_list_type(model)
                if inside:
                    if inside == str:
                        return json_rsp
                    else:
                        return [inside.parse_obj(an_obj) for an_obj in json_rsp]
                else:
                    if model == str:
                        return json_rsp
                    else:
                        return model.parse_obj(json_rsp)
        else:
            raise HTTPWarning("Call failed %d %s", rsp.status_code, rsp.text)

    def post(self, model, entry_point: str, **kwargs):
        url, headers = self._url_headers_args(entry_point, kwargs)
        rsp = self.session.post(url, timeout=60, headers=headers, **kwargs)
        if rsp.status_code == 200:
            json_rsp = rsp.json()
            if model not in (str, int):
                json_rsp = rsp.json()
                inside = detect_list_type(model)
                if inside:
                    return [inside.parse_obj(an_obj) for an_obj in json_rsp]
                else:
                    return model.parse_obj(json_rsp)
            else:
                return json_rsp
        else:
            raise HTTPWarning("Call failed %d %s", rsp.status_code, rsp.text)

    def put(self, entry_point: str, **kwargs):
        url, headers = self._url_headers_args(entry_point, kwargs)
        rsp = self.session.put(url, headers=headers, **kwargs)
        if rsp.status_code == 200:
            pass
        else:
            raise HTTPWarning("Call failed %d %s", rsp.status_code, rsp.text)

    def delete(self, entry_point: str, **kwargs):
        url, headers = self._url_headers_args(entry_point, kwargs)
        rsp = self.session.delete(url, headers=headers, **kwargs)
        if rsp.status_code == 200:
            pass
        else:
            raise HTTPWarning("Call failed %d %s", rsp.status_code, rsp.text)
