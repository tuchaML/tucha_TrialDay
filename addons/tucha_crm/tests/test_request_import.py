
import base64

# Ошибка валидации, которую выдаёт Odoo при неправильных данных.
from odoo.exceptions import ValidationError

# Базовый класс для тестов, работающих с базой Odoo.
from odoo.tests.common import TransactionCase


class TestRequestImport(TransactionCase):

    # Максимальный допустимый размер файла — 10 MiB.
    MAX_SIZE = 10 * 1024 * 1024

    def _make_import(self, data, filename="test.xlsx"):
        """
        Вспомогательный метод для создания тестовой
        записи загрузки файла.

        data — содержимое в Base64.
        filename — имя файла.
        """

        # Создаём временную запись модели импорта Odoo.
        return self.env["tucha.request.import"].create({
            "filename": filename,
            "file_data": data,
        })

    def test_exactly_10_mib_is_accepted(self):
        """Файл ровно 10 MiB должен проходить проверку."""

        # Создаём 10 485 760 байт.
        # Буква A используется только для заполнения файла.
        original = b"A" * self.MAX_SIZE

        # Имитируем передачу файла через Base64.
        encoded = base64.b64encode(original)

        # Создаём тестовую запись импорта.
        wizard = self._make_import(encoded)

        # Вызываем метод, который мы исправили.
        result = wizard._source_bytes()

        # Проверяем, что метод вернул исходные байты.
        self.assertEqual(result, original)

    def test_10_mib_plus_one_byte_is_rejected(self):
        """Файл 10 MiB + 1 байт должен отклоняться."""

        # Создаём файл на один байт больше лимита.
        original = b"A" * (self.MAX_SIZE + 1)

        # Кодируем его в Base64.
        encoded = base64.b64encode(original)

        wizard = self._make_import(encoded)

        # Ожидаем ошибку ValidationError.
        # Дополнительно проверяем, что в сообщении есть "10 MiB".
        with self.assertRaises(ValidationError):
            wizard._source_bytes()

    def test_invalid_base64_is_rejected(self):
        """Некорректный Base64 должен вызывать понятную ошибку."""

        # Символы @ не входят в допустимый алфавит Base64.
        wizard = self._make_import(b"@@@@")

        # Проверяем, что программа не падает с технической ошибкой.
        with self.assertRaisesRegex(
            ValidationError, "Не удалось прочитать"
        ):
            wizard._source_bytes()

    def test_small_file_is_accepted(self):
        """Небольшой корректный файл принимается."""

        original = b"Test Excel data"

        # Кодируем тестовые данные.
        encoded = base64.b64encode(original)

        wizard = self._make_import(encoded)

        # Проверяем точное совпадение исходных
        # и возвращённых байтов.
        self.assertEqual(
            wizard._source_bytes(),
            original,
        )

    def test_wrong_extension_is_rejected(self):
        """Файл с расширением .txt должен отклоняться."""

        encoded = base64.b64encode(b"Test data")

        # Передаём имя с неправильным расширением.
        wizard = self._make_import(
            encoded,
            filename="test.txt",
        )

        # Ожидаем ошибку с упоминанием .xlsx.
        with self.assertRaisesRegex(
            ValidationError, r"\.xlsx"
        ):
            wizard._source_bytes()
