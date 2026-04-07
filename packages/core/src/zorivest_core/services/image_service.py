"""ImageService — chart/screenshot attach, retrieve, thumbnail.

Source: 03-service-layer.md §ImageService
Uses: AttachImage command (commands.py)
"""

from __future__ import annotations

from zorivest_core.application.commands import AttachImage
from zorivest_core.application.ports import UnitOfWork
from zorivest_core.domain.entities import ImageAttachment
from zorivest_core.domain.exceptions import NotFoundError


class ImageService:
    """Chart/screenshot management: attach, retrieve, thumbnail."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def attach_image(self, command: AttachImage) -> int:
        """Attach an image to an owner (trade, report, plan).

        Uses AttachImage command with owner_type/owner_id/data fields
        (not spec's trade_id/image_data aliases).

        Raises:
            NotFoundError: If owner entity does not exist (for trade owners).
        """
        with self.uow:
            # Validate owner exists (for trade owners)
            if command.owner_type.value == "trade":
                trade = self.uow.trades.get(command.owner_id)
                if trade is None:
                    raise NotFoundError(f"Trade not found: {command.owner_id}")

            image = ImageAttachment(
                id=0,  # assigned by repository
                owner_type=command.owner_type,
                owner_id=command.owner_id,
                data=command.data,
                width=command.width,
                height=command.height,
                file_size=len(command.data),
                created_at=__import__("datetime").datetime.now(),
                mime_type=command.mime_type,
                caption=command.caption,
                thumbnail=command.thumbnail,
            )
            image_id = self.uow.images.save(
                command.owner_type.value, command.owner_id, image
            )
            self.uow.commit()
            return image_id

    def get_trade_images(self, trade_id: str) -> list[ImageAttachment]:
        """Get all images attached to a trade."""
        with self.uow:
            return self.uow.images.get_for_owner("trade", trade_id)

    def get_thumbnail(self, image_id: int, max_size: int = 200) -> bytes:
        """Get a thumbnail of an image.

        Raises:
            NotFoundError: If image does not exist.
        """
        with self.uow:
            image = self.uow.images.get(image_id)
            if image is None:
                raise NotFoundError(f"Image not found: {image_id}")
            return self.uow.images.get_thumbnail(image_id, max_size)

    def get_image(self, image_id: int) -> ImageAttachment:
        """Retrieve image metadata by ID.

        Raises:
            NotFoundError: If image does not exist.
        """
        with self.uow:
            image = self.uow.images.get(image_id)
            if image is None:
                raise NotFoundError(f"Image not found: {image_id}")
            return image

    def get_full_image(self, image_id: int) -> bytes:
        """Get full image bytes (not thumbnail)."""
        with self.uow:
            return self.uow.images.get_full_data(image_id)

    def get_images_for_owner(
        self, owner_type: str, owner_id: str
    ) -> list[ImageAttachment]:
        """Get all images attached to an owner (trade, account, etc.)."""
        with self.uow:
            return self.uow.images.get_for_owner(owner_type, owner_id)

    def delete_image(self, image_id: int) -> None:
        """Delete an image by ID.

        Raises:
            NotFoundError: If image does not exist.
        """
        with self.uow:
            image = self.uow.images.get(image_id)
            if image is None:
                raise NotFoundError(f"Image not found: {image_id}")
            self.uow.images.delete(image_id)
            self.uow.commit()
