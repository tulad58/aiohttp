import json

import bcrypt
from aiohttp import web
from sqlalchemy.exc import IntegrityError
from models import User, Ad, Session, engine, init_db

app = web.Application()


def get_http_error(error_class, message):
    error = error_class(
        body=json.dumps({"error": message}), content_type="application/json"
    )
    return error


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response


async def init_orm(app: web.Application):
    print("START")
    await init_db()
    yield
    await engine.dispose()
    print("FINISH")


app.cleanup_ctx.append(init_orm)
app.middlewares.append(session_middleware)


async def add_user(session: Session, user: User):
    try:
        session.add(user)
        await session.commit()
    except IntegrityError as error:
        raise get_http_error(web.HTTPConflict, "User already exists")
    return user


async def add_ad(session: Session, ad: Ad):
    try:
        session.add(ad)
        await session.commit()
    except IntegrityError as error:
        raise get_http_error(web.HTTPConflict, "Ad already exists")
    return ad


async def get_ad_by_id(session: Session, id: int):
    ad = await session.get(Ad, id)
    if ad is None:
        raise get_http_error(web.HTTPNotFound, f"User with id {id} not found")
    return ad


class UserView(web.View):
    @property
    def session(self) -> Session:
        return self.request.session

    async def get(self):
        pass

    async def post(self):
        json_data = await self.request.json()
        user = User(**json_data)
        user = await add_user(self.session, user)
        return web.json_response({"id": user.id})

    async def patch(self):
        pass

    async def delete(self):
        pass


class AdView(web.View):
    @property
    def ad_id(self):
        return int(self.request.match_info["ad_id"])

    @property
    def session(self) -> Session:
        return self.request.session

    async def get_current_ad(self):
        return await get_ad_by_id(self.request.session, self.ad_id)

    async def get(self):
        ad = await self.get_current_ad()
        return web.json_response(ad.dict)

    async def post(self):
        json_data = await self.request.json()
        ad = Ad(**json_data)
        ad = await add_ad(self.session, ad)
        return web.json_response({"id": ad.id})

    async def patch(self):
        ad = await self.get_current_ad()
        json_data = await self.request.json()
        for field, value in json_data.items():
            setattr(ad, field, value)
        return web.json_response(
            {"id": ad.id, "title": ad.title, "description": ad.description}
        )

    async def delete(self):
        ad = await self.get_current_ad()
        await self.session.delete(ad)
        await self.session.commit()
        return web.json_response({"deleted id": ad.id})


app.add_routes(
    [
        web.post("/user/", UserView),
        web.get(r"/user/{user_id:\d+}", UserView),
        web.patch(r"/user/{user_id:\d+}", UserView),
        web.delete(r"/user/{user_id:\d+}", UserView),
        web.post("/ad/", AdView),
        web.get(r"/ad/{ad_id:\d+}", AdView),
        web.patch(r"/ad/{ad_id:\d+}", AdView),
        web.delete(r"/ad/{ad_id:\d+}", AdView),
    ]
)

web.run_app(app)
