import asyncio
import json
import os
import random
import re
import time
import uuid

from fastapi import Request
from fastapi.responses import Response


# Global throttling + metrics for ADK invoke endpoints.
# ADK can run via JSON (/run) or SSE (/run_sse). We must throttle both.

_MAX_CONCURRENT_RUNS = int(os.getenv("LLM_MAX_CONCURRENT_RUNS", "1"))
_RUN_SEMAPHORE = asyncio.Semaphore(max(_MAX_CONCURRENT_RUNS, 1))

_METRICS = {
    "adk_requests_total": 0,
    "adk_in_flight": 0,
    "adk_status_counts": {},
    "adk_429_total": 0,
    "adk_last_429_at": None,
    "adk_total_ms": 0.0,
    "adk_avg_ms": 0.0,
    "adk_last_ms": None,
}


def get_llm_metrics_snapshot() -> dict:
    return {
        "max_concurrent_runs": _MAX_CONCURRENT_RUNS,
        **_METRICS,
        "adk_status_counts": dict(_METRICS.get("adk_status_counts") or {}),
    }


def _is_adk_invoke(request: Request) -> tuple[bool, bool]:
    if request.method.upper() != "POST":
        return False, False
    path = request.url.path or ""
    if path.endswith("/run_sse"):
        return True, True
    if path.endswith("/run"):
        return True, False
    return False, False


def attach_request_middleware(app, logger, llm_delay_seconds: float = 5.0):
    @app.middleware("http")
    async def request_logging_and_delay(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        started_at = time.perf_counter()

        trace_id = request.headers.get("x-nexus-trace-id")
        request_meta = {"trace_id": trace_id} if trace_id else {}

        is_adk, is_sse = _is_adk_invoke(request)

        # Best-effort payload parse for logging (without breaking request body)
        if request.method.upper() == "POST" and (is_adk or request.url.path == "/api/rfq"):
            try:
                raw = await request.body()
                payload = json.loads(raw.decode("utf-8")) if raw else {}

                if is_adk:
                    request_meta.update(
                        {
                            "app_name": payload.get("appName") or payload.get("app_name"),
                            "user_id": payload.get("userId") or payload.get("user_id"),
                            "session_id": payload.get("sessionId") or payload.get("session_id"),
                            "message_count": len(payload.get("messages") or []),
                        }
                    )
                else:
                    request_meta.update(
                        {
                            "buyer_id": payload.get("buyer_id"),
                            "delivery_region": payload.get("delivery_region"),
                            "item_count": len(payload.get("items") or []),
                        }
                    )

                async def receive():
                    return {"type": "http.request", "body": raw, "more_body": False}

                request = Request(request.scope, receive)
            except Exception as e:
                logger.warning("[%s] Failed parsing payload for %s: %s", request_id, request.url.path, e)

        logger.info(
            "[%s] [REQUEST] %s %s meta=%s",
            request_id,
            request.method,
            request.url.path,
            request_meta,
        )

        # Delay + jitter (prevents bursty request patterns)
        if is_adk and llm_delay_seconds and llm_delay_seconds > 0:
            try:
                jitter = float(os.getenv("LLM_DELAY_JITTER_SECONDS", "0.5"))
            except Exception:
                jitter = 0.5

            total_delay = float(llm_delay_seconds) + (random.random() * max(jitter, 0.0))
            logger.info(
                "[%s] [REQUEST] Applying %.2fs delay before %s",
                request_id,
                total_delay,
                request.url.path,
            )
            await asyncio.sleep(total_delay)

        acquired = False
        release_in_finally = True

        if is_adk:
            _METRICS["adk_requests_total"] += 1
            _METRICS["adk_in_flight"] += 1
            await _RUN_SEMAPHORE.acquire()
            acquired = True

        try:
            response = await call_next(request)

            # Non-ADK requests: fast path
            if not is_adk:
                duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
                logger.info("[%s] [RESPONSE] status=%s duration_ms=%s", request_id, response.status_code, duration_ms)
                return response

            # --- ADK invoke handling ---
            status = int(getattr(response, "status_code", 0) or 0)

            def _finish_metrics():
                duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
                _METRICS["adk_total_ms"] = float(_METRICS.get("adk_total_ms") or 0.0) + float(duration_ms)
                _METRICS["adk_last_ms"] = float(duration_ms)
                _METRICS["adk_avg_ms"] = round(
                    float(_METRICS["adk_total_ms"]) / max(int(_METRICS["adk_requests_total"]) or 1, 1),
                    2,
                )

                status_counts = _METRICS.get("adk_status_counts") or {}
                status_counts[str(status)] = int(status_counts.get(str(status), 0)) + 1
                _METRICS["adk_status_counts"] = status_counts

                if status == 429:
                    _METRICS["adk_429_total"] = int(_METRICS.get("adk_429_total") or 0) + 1
                    _METRICS["adk_last_429_at"] = time.time()

                logger.info(
                    "[%s] [RESPONSE] status=%s duration_ms=%s path=%s",
                    request_id,
                    status,
                    duration_ms,
                    request.url.path,
                )

            if is_sse:
                # IMPORTANT: do NOT buffer SSE. Wrap iterator so we hold the semaphore
                # until the stream completes.
                release_in_finally = False

                original_iter = response.body_iterator

                async def wrapped_iterator():
                    nonlocal acquired
                    try:
                        async for chunk in original_iter:
                            yield chunk
                    finally:
                        try:
                            _finish_metrics()
                        finally:
                            _METRICS["adk_in_flight"] = max(int(_METRICS.get("adk_in_flight") or 0) - 1, 0)
                            if acquired:
                                _RUN_SEMAPHORE.release()
                                acquired = False

                response.body_iterator = wrapped_iterator()
                return response

            # JSON /run: buffer so we can log + keep semaphore until complete.
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            text = body.decode("utf-8", errors="replace")

            match = re.search(r"LOG_DATA:\s*(\{.*?\})\s*(?:\\n|$)", text, re.DOTALL)
            if match:
                try:
                    raw_text_clean = match.group(1).replace("'", '"')
                    log_json = json.loads(raw_text_clean)
                    logger.info("[%s] [AGENT OUTPUT] %s", request_id, json.dumps(log_json, indent=2))
                except Exception as e:
                    logger.warning("[%s] [AGENT OUTPUT] Could not parse LOG_DATA: %s", request_id, e)
                text = re.sub(r"\nLOG_DATA:.*?(\n|$)", "", text, flags=re.DOTALL)

            _finish_metrics()

            return Response(
                content=text.encode("utf-8"),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        except Exception:
            if is_adk:
                status_counts = _METRICS.get("adk_status_counts") or {}
                status_counts["exception"] = int(status_counts.get("exception", 0)) + 1
                _METRICS["adk_status_counts"] = status_counts
            logger.exception("[%s] [MIDDLEWARE_ERROR] path=%s", request_id, request.url.path)
            raise

        finally:
            if is_adk and release_in_finally:
                _METRICS["adk_in_flight"] = max(int(_METRICS.get("adk_in_flight") or 0) - 1, 0)
                if acquired:
                    _RUN_SEMAPHORE.release()
