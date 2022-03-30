# See LICENSE file for full copyright and licensing details.
from odoo import models, fields
import requests
import json
from datetime import datetime
from odoo.tools.mimetypes import guess_mimetype
import html2text
import base64
import threading


class PosOrder(models.Model):
    """Inherit POS Order."""

    _inherit = "pos.order"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company)
    current_user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user)

    def send_order_status(self):
        """Send Message to Customer."""
        thread_start = threading.Thread(target=self.send_message())
        thread_start.start()
        return True

    def send_message(self):
        for rec in self:
            if (
                rec
                and rec.partner_id
                and rec.partner_id.is_whatsapp_number
                and rec.session_id
                and rec.session_id.config_id
                and rec.session_id.config_id.is_send_whatsapp
            ):
                templated_id = rec.session_id.config_id.templated_id
                company_id = self.env.user and self.env.user.company_id or False
                company_id.check_auth()
                path = (
                    company_id
                    and company_id.authenticate
                    and company_id.api_url + str(company_id.instance_no)
                )

                if (
                    path
                    and rec.partner_id.country_id
                    and rec.partner_id.mobile
                    and templated_id
                ):
                    mobile = rec.partner_id._formatting_mobile_number()
                    url_path = path + "/sendMessage"
                    token_value = {"token": company_id.api_token}
                    template = templated_id.generate_email(rec.id)
                    body = template.get("body")
                    body_msg = html2text.html2text(body)
                    message_data = {"phone": mobile, "body": body_msg}
                    rec.send_pdf(
                        url_path, token_value, message_data, rec.partner_id, body_msg
                    )
                    url_path = path + "/sendFile"
                    report = template.get("attachments")
                    mimetype = guess_mimetype(base64.b64decode(report[0][1]))
                    str_mimetype = "data:" + mimetype + ";base64,"
                    pdf_title = rec.pos_reference + ".pdf"
                    attachment_new = str_mimetype + str(report[0][1].decode("utf-8"))
                    message_data = {
                        "phone": mobile,
                        "body": attachment_new + body_msg,
                        "filename": pdf_title,
                        "caption": rec.name,
                    }
                    rec.send_pdf(
                        url_path, token_value, message_data, rec.partner_id, body_msg
                    )

    def send_pdf(self, url_path, token_value, message_data, partner_id, body_msg):
        """Send Message on whatsapp."""
        whatsapp_log_obj = self.env["whatsapp.message.log"]
        data = json.dumps(message_data)
        request_meeting = requests.post(
            url_path,
            data=data,
            params=token_value,
            headers={"Content-Type": "application/json"},
        )
        message_dict = {
            "name": self.partner_id.name or False,
            "msg_date": datetime.now(),
            "link": url_path,
            "data": data,
            "message": request_meeting.text,
            "message_body": body_msg,
        }
        if request_meeting.status_code == 200:
            data = json.loads(request_meeting.text)
            chat_id = data.get("id") and data.get("id").split("_")
            message_dict.update({"chat_id": chat_id[1], "status": "send"})
        else:
            message_dict.update({"status": "error"})
        whatsapp_log_obj.create(message_dict)
