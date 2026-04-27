import asyncio
import json
import re

from fastapi import Request
from fastapi.responses import Response


def attach_request_middleware(app, logger, llm_delay_seconds: int = 10):
    @app.middleware("http")
    async def request_logging_and_delay(request: Request, call_next):
        request_meta = {}
        if request.method.upper() == "POST" and request.url.path == "/run":
            try:
                raw = await request.body()
                payload = json.loads(raw.decode("utf-8")) if raw else {}
                request_meta = {
                    "app_name": payload.get("app_name"),
                    "user_id": payload.get("user_id"),
                    "session_id": payload.get("session_id"),
                }

                async def receive():
                    return {"type": "http.request", "body": raw, "more_body": False}

                request = Request(request.scope, receive)
            except Exception as e:
                logger.warning(f"[REQUEST] Failed parsing /run payload metadata: {e}")

        if request_meta:
            logger.info(
                "[REQUEST] %s %s app=%s user=%s session=%s",
                request.method,
                request.url.path,
                request_meta.get("app_name"),
                request_meta.get("user_id"),
                request_meta.get("session_id"),
            )
        else:
            logger.info(f"[REQUEST] {request.method} {request.url.path}")

        if request.url.path == "/run" and llm_delay_seconds > 0:
            logger.info("[REQUEST] Applying %ss delay before /run for rate-limit control.", llm_delay_seconds)
            await asyncio.sleep(llm_delay_seconds)

        response = await call_next(request)

        if request.url.path == "/run":
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            text = body.decode("utf-8")
            match = re.search(r'LOG_DATA:\s*(\{.*?\})\s*(?:\\n|$)', text, re.DOTALL)
            if match:
                try:
                    raw_text_clean = match.group(1).replace("'", '"')
                    log_json = json.loads(raw_text_clean)
                    logger.info(f"[AGENT OUTPUT]\n{json.dumps(log_json, indent=2)}")
                except Exception as e:
                    logger.warning(f"[AGENT OUTPUT] Could not parse LOG_DATA: {e}")

                text = re.sub(r"\nLOG_DATA:.*?(\n|$)", "", text, flags=re.DOTALL)

            return Response(
                content=text.encode("utf-8"),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response

