from aiohttp import web

from config import SERVER_PORT


async def hello_world_handler(request):
    name = request.match_info.get('name', 'Anonymous')
    text = 'Hello, ' + name
    return web.Response(text=text)


app = web.Application()
app.add_routes([web.get('/', hello_world_handler), web.get('/{name}', hello_world_handler)])


if __name__ == '__main__':
    web.run_app(app, port=SERVER_PORT)
