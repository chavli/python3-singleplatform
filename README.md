SinglePlatform is a single platform to publish your menu and business information everywhere it needs to be.
https://www.singleplatform.com/

This repo contains a Python 3.6 wrapper of their API described here
https://s3-us-west-1.amazonaws.com/fetchy-public/SinglePlatformRestAPI.pdf

It's meant as an improvement and replacemente for their Python 2 example library found here:
http://docs.singleplatform.com/spv3/attachments/signing.py

The API for getting locations with the `/updated_since/` endpoint is purposely ignored since this
endpoint filters on *all* locations managed by SinglePlatform and not just the ones your organization
manages.

Additional links:
- http://docs.singleplatform.com/spv3/