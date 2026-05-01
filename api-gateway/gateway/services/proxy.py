from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request, Response


async def forward_request(
    request: Request,
    upstream_base: str,
    subpath: str = "",
    *,
    timeout_seconds: float = 10.0,
) -> Response:
    path = f"/{subpath}" if subpath else ""
    query_string = urlencode(request.query_params.multi_items())
    url = f"{upstream_base}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }

    logger = request.app.state.logger
    request_id = getattr(request.state, "request_id", None)

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            upstream_response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=request.stream(),
            )
    except httpx.TimeoutException as exc:
        logger.warning(
            "upstream_timeout",
            request_id=request_id,
            method=request.method,
            upstream_url=url,
            timeout_seconds=timeout_seconds,
        )
        raise HTTPException(status_code=504, detail="Upstream service timeout") from exc
    except httpx.RequestError as exc:
        logger.warning(
            "upstream_unavailable",
            request_id=request_id,
            method=request.method,
            upstream_url=url,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="Upstream service unavailable") from exc

    if upstream_response.status_code >= 500:
        logger.warning(
            "upstream_server_error",
            request_id=request_id,
            method=request.method,
            upstream_url=url,
            upstream_status=upstream_response.status_code,
        )
        raise HTTPException(status_code=502, detail="Upstream service error")

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers={
            key: value
            for key, value in upstream_response.headers.items()
            if key.lower() in {"content-type", "x-request-id"}
        },
    )
