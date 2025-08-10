from dicttoxml2 import dicttoxml
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from loguru import logger as log

from wwricu.domain.enum import WebDavMethodsEnum

webdav_api = APIRouter(prefix='/webdav', tags=['Webdav API'])


@webdav_api.api_route('/', methods=[WebDavMethodsEnum.PROPFIND])
async def webdav_propfind(request: Request, response: Response):
    log.info(request.method)
    log.info(request.headers)
    log.info(await request.body())

    resp_dict = {
        'D:multistatus': {
            '@xmlns:D': 'DAV:',
            'D:response': {
                'xmlns: R': "http://ns.example.com/boxschema/"
            }
        }
    }



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
