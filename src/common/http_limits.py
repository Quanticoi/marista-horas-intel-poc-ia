from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app, max_bytes=65536):
        self.app=app
        self.max_bytes=max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type']!='http' or scope['method'] not in ('POST','PUT','PATCH'):
            return await self.app(scope,receive,send)
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect':
                return
            body.extend(message.get('body',b''))
            if len(body)>self.max_bytes:
                response=JSONResponse(status_code=413,content=dict(code='PAYLOAD_TOO_LARGE',message=f'Maximum body: {self.max_bytes} bytes',correlation_id=''))
                return await response(scope,receive,send)
            if not message.get('more_body',False):
                break
        sent=False
        async def replay():
            nonlocal sent
            if sent:
                return await receive()
            sent=True
            return {'type':'http.request','body':bytes(body),'more_body':False}
        await self.app(scope,replay,send)
