#
# SinglePlatform is a single platform to publish your menu and business information everywhere it needs to be.
# https://www.singleplatform.com/
#
# A Python 3.6 implementation of the SinglePlatform API described here:
# https://s3-us-west-1.amazonaws.com/fetchy-public/SinglePlatformRestAPI.pdf
#
# This is meant to be a replacement for the Python 2 example given by SinglePlatform found here:
#   http://docs.singleplatform.com/spv3/attachments/signing.py
#
# The API for getting locations with the `/updated_since/` endpoint is purposely ignored since this
# endpoint filters on *all* locations managed by SinglePlatform and not just the ones your organization
# manages.
#
# Additional links:
# - http://docs.singleplatform.com/spv3/
#

import base64
import hashlib
import hmac
import requests
from enum import Enum, unique
from urllib.parse import urlencode


@unique
class SinglePlatformImageType(Enum):
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    ITEM = "item"
    LOGO = "logo"
    UNCATEGORIZED = "uncategorized"


class SinglePlatformLocationAPI:
    _HOST = "https://publishing-api.singleplatform.com"

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

    def _generate_signature(self, uri) -> str:
        key = self._client_secret.encode()
        path = uri.encode()
        data = hmac.new(key, path, hashlib.sha1).digest()
        return base64.b64encode(data)

    def _generate_url(self, path, params: dict) -> str:
        uri = "{path}?{params}".format(path=path, params=urlencode(params))
        params["signature"] = self._generate_signature(uri)
        url = "{host}{uri}?{params}".format(host=self._HOST, uri=path, params=urlencode(params))
        print("generated url: {}".format(url))
        return url

    def _recurse_locations(self, parent: dict) -> list:
        """ recursively parses the response from location_ids(...) and returns a list of just location JSON """
        locations = []
        if parent.get("node_type") == "location":
            return [parent]
        for child in parent.get("nodes", []):
            locations.extend(self._recurse_locations(child))

        return locations

    def managed_locations(self, business_id: str, cookie: str) -> list:
        """ return all locations managed by your business, as JSON.

        IMPORTANT: This is not a public/supported/documented endpoint. This method of pulling just your locations was
        found by inspecting the network requests made when loading the SinglePlatform web dashboard at
        https://my2.singleplatform.com/business/list_my_locations. A request is made to
        https://my2.singleplatform.com/hierarchy/list/business/<business_id>/ which returns a single JSON containing
        location data. Authentication for this endpoint is handled by the `Cookie` request header. You'll have to use
        the network inspector in Chrome or Firefox to discover this value. The cookie seems to have a long* validity
        period.

        NOTE: I'm assuming the id value is a business/account id. I have no idea what it really is or how unique it is.

        NOTE 2: I have no long how long the cookie is valid.

        NOTE 3: My cookie had this format: csrftoken=xxxxx; sessionid=xxxxxx; SnapABugHistory=xxxx; SnapABugVisit=xxxxx
        """

        url = "https://my2.singleplatform.com/hierarchy/list/business/{business_id}/".format(business_id=business_id)
        headers = {
            "Cookie": cookie
        }

        response = requests.get(url, headers=headers)
        data = response.json().get("root_tier", {})
        return self._recurse_locations(data)

    def summary(self, location_id: str, complete: bool = False) -> dict:
        """ return summary information, as JSON, about a single location. if `complete` is set to True then all data is
        returned for the given location, including location details, product details, and photos """

        flag = "all/" if complete else ""
        path = "/locations/{id}/{all}".format(id=location_id, all=flag)
        params = {
            "client": self._client_id
        }

        url = self._generate_url(path, params)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(response.text)

    def menu(self, location_id: str, short: bool = False) -> dict:
        """ return all product / menu information, as JSON, for the given location. if `short` is set to `True` then
        up to 5 representative sample items from each section are returned. """

        path = "/locations/{id}/menus/".format(id=location_id)
        params = {
            "client": self._client_id
        }
        if short:
            params["format"] = "short"

        url = self._generate_url(path, params)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(response.text)

    def photos(self, location_id: str, max_height: int = None, max_width: int = None,
               image_type: SinglePlatformImageType = None) -> dict:
        """ return photo metadata, as JSON, for the given location. The optional parameters allow you to filter the
        image metadata, these are self explanatory. Leaving them all `None` will cause this request to return metadata
        for all images """

        path = "/locations/{id}/photos/".format(id=location_id)
        params = {
            "client": self._client_id
        }

        if max_height:
            params["height"] = max_height

        if max_width:
            params["width"] = max_width

        if image_type:
            params["type"] = image_type.value

        url = self._generate_url(path, params)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(response.text)
