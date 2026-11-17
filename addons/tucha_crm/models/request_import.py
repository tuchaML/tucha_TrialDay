import base64
import binascii

from odoo import fields, models
from odoo.exceptions import ValidationError


class TuchaRequestImport(models.TransientModel):
    _name = "tucha.request.import"
    _description = "Импорт заявки из Excel"

    filename = fields.Char(required=True)
    file_data = fields.Binary(required=True, attachment=False)

    def _source_bytes(self) -> bytes:
        """Реальная ошибка лимита сохранена как Junior-задача."""
        self.ensure_one()
        if not self.filename or not self.filename.casefold().endswith(".xlsx"):
            raise ValidationError("Выберите файл .xlsx по шаблону компании.")

        try:
            # Декодируем Base64 с проверкой корректности символов.
            decoded_data = base64.b64decode(
                self.file_data,
                validate=True,
            )

        except (binascii.Error, ValueError):
            # Превращаем техническую ошибку Python
            # в понятное сообщение пользователю Odoo.
            raise ValidationError(
                "Не удалось прочитать содержимое файла."
            ) from None

        if not self.file_data or len(decoded_data) > 10 * 1024 * 1024:
            raise ValidationError("Выберите файл Excel размером не более 10 МБ.")

        try:
            return base64.b64decode(self.file_data, validate=True)
        except (binascii.Error, ValueError):
            raise ValidationError("Не удалось прочитать содержимое файла.") from None

    def action_validate_file(self) -> dict:
        """Даёт кандидату воспроизводимую точку входа через интерфейс."""
        self._source_bytes()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Файл принят",
                "message": "Размер файла не превышает лимит.",
                "type": "success",
                "sticky": False,
            },
        }
