from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from loguru import logger as log

from wwricu.domain.enum import WebDavMethodsEnum

webdav_api = APIRouter(prefix='/webdav', tags=['Webdav API'])


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.PROPFIND], response_class=Response)
async def webdav_propfind(request: Request):
    log.info(request.method)
    log.info(request.url.path)
    log.info(request.headers)
    log.info(await request.body())

    resp = '''
    <?xml version="1.0" encoding="utf-8" ?>
    <ns0:multistatus xmlns:ns0="DAV:">
        <ns0:response>
            <ns0:href>/</ns0:href>
            <ns0:propstat>
                <ns0:prop>
                    <ns0:resourcetype>
                        <ns0:collection/>
                    </ns0:resourcetype>
                    <ns0:creationdate>2025-07-27T07:59:44Z</ns0:creationdate>
                    <ns0:quota-used-bytes>1566717497344</ns0:quota-used-bytes>
                    <ns0:quota-available-bytes>480696344576</ns0:quota-available-bytes>
                    <ns0:getlastmodified>Tue, 09 Sep 2025 14:21:46 GMT</ns0:getlastmodified>
                    <ns0:displayname>misc</ns0:displayname>
                    <ns0:lockdiscovery/>
                    <ns0:supportedlock>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:exclusive/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:shared/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                    </ns0:supportedlock>
                </ns0:prop>
                <ns0:status>HTTP/1.1 200 OK</ns0:status>
            </ns0:propstat>
        </ns0:response>
        <ns0:response>
            <ns0:href>/performance.py</ns0:href>
            <ns0:propstat>
                <ns0:prop>
                    <ns0:resourcetype/>
                    <ns0:creationdate>2025-07-27T07:59:53Z</ns0:creationdate>
                    <ns0:getcontentlength>85</ns0:getcontentlength>
                    <ns0:getcontenttype>text/x-python</ns0:getcontenttype>
                    <ns0:getlastmodified>Sun, 24 Aug 2025 06:48:24 GMT</ns0:getlastmodified>
                    <ns0:displayname>performance.py</ns0:displayname>
                    <ns0:getetag>7b227185f298b5fa439ac6c2c70c5bdd-1756018104-85</ns0:getetag>
                    <ns0:lockdiscovery/>
                    <ns0:supportedlock>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:exclusive/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:shared/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                    </ns0:supportedlock>
                </ns0:prop>
                <ns0:status>HTTP/1.1 200 OK</ns0:status>
            </ns0:propstat>
        </ns0:response>
        <ns0:response>
            <ns0:href>/test/</ns0:href>
            <ns0:propstat>
                <ns0:prop>
                    <ns0:resourcetype>
                        <ns0:collection/>
                    </ns0:resourcetype>
                    <ns0:creationdate>2025-09-09T14:21:46Z</ns0:creationdate>
                    <ns0:quota-used-bytes>1566717497344</ns0:quota-used-bytes>
                    <ns0:quota-available-bytes>480696344576</ns0:quota-available-bytes>
                    <ns0:getlastmodified>Tue, 09 Sep 2025 14:21:52 GMT</ns0:getlastmodified>
                    <ns0:displayname>test</ns0:displayname>
                    <ns0:lockdiscovery/>
                    <ns0:supportedlock>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:exclusive/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:shared/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                    </ns0:supportedlock>
                </ns0:prop>
                <ns0:status>HTTP/1.1 200 OK</ns0:status>
            </ns0:propstat>
        </ns0:response>
        <ns0:response>
            <ns0:href>/webdav.bat</ns0:href>
            <ns0:propstat>
                <ns0:prop>
                    <ns0:resourcetype/>
                    <ns0:creationdate>2025-09-09T14:20:57Z</ns0:creationdate>
                    <ns0:getcontentlength>72</ns0:getcontentlength>
                    <ns0:getcontenttype>text/plain</ns0:getcontenttype>
                    <ns0:getlastmodified>Tue, 09 Sep 2025 14:21:08 GMT</ns0:getlastmodified>
                    <ns0:displayname>webdav.bat</ns0:displayname>
                    <ns0:getetag>49fb204e339c746cca6132f9cee2c683-1757427668-72</ns0:getetag>
                    <ns0:lockdiscovery/>
                    <ns0:supportedlock>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:exclusive/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                        <ns0:lockentry>
                            <ns0:lockscope>
                                <ns0:shared/>
                            </ns0:lockscope>
                            <ns0:locktype>
                                <ns0:write/>
                            </ns0:locktype>
                        </ns0:lockentry>
                    </ns0:supportedlock>
                </ns0:prop>
                <ns0:status>HTTP/1.1 200 OK</ns0:status>
            </ns0:propstat>
        </ns0:response>
    </ns0:multistatus>
    '''
    return Response(status_code=207, content=resp.encode('utf-8'), media_type='application/xml; charset=utf-8')


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.PROPPATCH])
async def webdav_proppatch(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.MKCOL])
async def webdav_mkcol(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())



@webdav_api.api_route('/', methods=[WebDavMethodsEnum.COPY])
async def webdav_copy(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.MOVE])
async def webdav_move(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.COPY])
async def webdav_copy(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.DELETE])
async def webdav_delete(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.PUT])
async def webdav_put(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.HEAD])
async def webdav_head(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.LOCK])
async def webdav_lock(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.UNLOCK])
async def webdav_unlock(request: Request, response: Response):
    log.info(request.method)
    log.info(await request.body())
