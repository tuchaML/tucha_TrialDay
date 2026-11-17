from odoo import fields, models
from odoo.exceptions import UserError


class TuchaRequest(models.Model):
    _inherit = "tucha.request"

    correction_state = fields.Selection(
        [
            ("none", "Не требуется"),
            ("requested", "Запрошена"),
            ("received", "Получена"),
            ("verified", "Проверена"),
        ],
        default="none",
        readonly=True,
        copy=False,
    )
    correction_requested_at = fields.Datetime(readonly=True, copy=False)
    correction_received_at = fields.Datetime(readonly=True, copy=False)
    correction_verified_at = fields.Datetime(readonly=True, copy=False)

    def action_request_correction(self) -> None:
        self.check_access("write")
        self.write({
            "correction_state": "requested",
            "correction_requested_at": fields.Datetime.now(),
        })

    def action_receive_correction(self) -> None:
        self.check_access("write")
        if any(request.correction_state != "requested" for request in self):
            raise UserError("Сначала запросите корректировку.")
        self.write({
            "correction_state": "received",
            "correction_received_at": fields.Datetime.now(),
        })

    def action_verify_correction(self) -> None:
        self.check_access("write")
        if any(request.correction_state != "received" for request in self):
            raise UserError("Сначала отметьте получение корректировки.")
        self.write({
            "correction_state": "verified",
            "correction_verified_at": fields.Datetime.now(),
        })

    def action_reopen_correction(self) -> None:
        self.check_access("write")
        if not self.env.user.has_group("tucha_crm.group_tucha_manager"):
            raise UserError("Вернуть заявку на корректировку может только менеджер.")
        if any(request.correction_state not in ("received", "verified") for request in self):
            raise UserError("Заявка не находится на проверке корректировки.")
        # Реальная ошибка сохранена для задания: даты старого цикла не очищаются.
        self.write({
            "correction_state": "requested",
            "correction_requested_at": fields.Datetime.now(),
            "correction_received_at": False,
            "correction_verified_at": False
        })

    def action_take(self) -> None:
        self.check_access("write")
        for request in self:
            if request.taken_by == self.env.user:
                raise UserError("Вы уже взяли эту заявку.")
            if request.taken_by and not self.env.user.has_group(
                "tucha_crm.group_tucha_manager"
            ):
                raise UserError("Заявку уже взял другой оператор.")
        self.write({"taken_by": self.env.uid, "taken_at": fields.Datetime.now()})

    def action_release(self) -> None:
        if not self.env.user.has_group("tucha_crm.group_tucha_manager"):
            raise UserError("Снять заявку с оператора может только менеджер.")
        self.write({"taken_by": False, "taken_at": False})
