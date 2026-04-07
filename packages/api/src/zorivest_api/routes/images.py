"""Global image routes.

Source: 04a-api-trades.md §Image Routes (Global Access)
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from zorivest_core.domain.exceptions import NotFoundError
from zorivest_api.dependencies import get_image_service, require_unlocked_db

image_router = APIRouter(prefix="/api/v1/images", tags=["trades"])


class ImageMetadataResponse(BaseModel):
    id: int | None
    caption: str
    mime_type: str
    file_size: int | None
    width: int | None
    height: int | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


@image_router.get("/{image_id}", dependencies=[Depends(require_unlocked_db)])
async def get_image_metadata(image_id: int, service=Depends(get_image_service)):
    """Get image metadata."""
    try:
        img = service.get_image(image_id)
        return ImageMetadataResponse.model_validate(img)
    except NotFoundError:
        raise HTTPException(404, f"Image not found: {image_id}")


@image_router.get("/{image_id}/thumbnail", dependencies=[Depends(require_unlocked_db)])
async def get_image_thumbnail(
    image_id: int,
    max_size: int = 200,
    service=Depends(get_image_service),
):
    """Get image thumbnail."""
    try:
        thumb_bytes = service.get_thumbnail(image_id, max_size)
    except NotFoundError:
        raise HTTPException(404, f"Image not found: {image_id}")
    if thumb_bytes is None:
        raise HTTPException(404, f"Image not found: {image_id}")
    return Response(content=thumb_bytes, media_type="image/webp")


@image_router.get("/{image_id}/full", dependencies=[Depends(require_unlocked_db)])
async def get_image_full(image_id: int, service=Depends(get_image_service)):
    """Get full image data."""
    try:
        data = service.get_full_image(image_id)
    except NotFoundError:
        raise HTTPException(404, f"Image not found: {image_id}")
    if data is None:
        raise HTTPException(404, f"Image not found: {image_id}")
    return Response(content=data, media_type="image/webp")


@image_router.delete(
    "/{image_id}",
    status_code=204,
    dependencies=[Depends(require_unlocked_db)],
)
async def delete_image(image_id: int, service=Depends(get_image_service)):
    """Delete an image by ID.

    Returns 204 on success, 404 if image does not exist.
    """
    try:
        service.delete_image(image_id)
    except NotFoundError:
        raise HTTPException(404, f"Image not found: {image_id}")
