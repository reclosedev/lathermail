# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from tests.utils import BaseTestCase, smtp_send_email, send_email_plain, prepare_send_to_field, SendEmailError,\
    InvalidStatus
from lathermail.utils import utcnow


class ApiTestCase(BaseTestCase):

    def test_send_and_search(self):
        to_tuple = [("Rcpt1", "rcpt1@example.com"), ("Rcpt2", "rcpt2@example.com"), ("", "rcpt3@example.com")]
        emails = [t[1] for t in to_tuple]
        to = prepare_send_to_field(to_tuple)
        n = 3
        body_fmt = "you you привет {} \n\naaa\nbbb\n<a href='aaa'>zz</a>"
        subject_fmt = "Test subject хэллоу {}"
        file_content = "file content"
        sender_name = "Me"
        sender_addr = "asdf@exmapl.com"

        for i in range(n):
            smtp_send_email(
                to, subject_fmt.format(i), "%s <%s>" % (sender_name, sender_addr), body_fmt.format(i),
                user=self.inbox, password=self.password, port=self.port, emails=emails,
                attachments=[("tасдest.txt", file_content)]
            )
        res = self.get("/messages/").json
        self.assertEquals(res["message_count"], n)

        msg = res["message_list"][0]
        self.assertEquals(len(msg["parts"]), 2)
        self.assertEquals(msg["parts"][0]["body"], body_fmt.format(n - 1))
        self.assertEquals(msg["parts"][0]["is_attachment"], False)
        self.assertEquals(msg["parts"][1]["is_attachment"], True)
        self.assertIsNone(msg["parts"][1]["body"])
        self.assertEquals(len(msg["recipients"]), len(to_tuple))
        self.assertEquals([(rcpt["name"], rcpt["address"]) for rcpt in msg["recipients"]], to_tuple)
        self.assertEquals(msg["sender"]["name"], sender_name)
        self.assertEquals(msg["sender"]["address"], sender_addr)

        def msg_count(params=None):
            return self.get("/messages/", params=params).json["message_count"]

        self.assertEquals(msg_count({"subject": subject_fmt.format(0)}), 1)
        self.assertEquals(msg_count({"subject_contains": "Test"}), n)
        self.assertEquals(msg_count({"subject_contains": "no such message"}), 0)

        before_send = utcnow()
        smtp_send_email("wwwww@wwwww.www", "wwwww", "www@wwwww.www", "wwwwwwww",
                        user=self.inbox, password=self.password, port=self.port)

        self.assertEquals(msg_count({"recipients.address": emails[0]}), n)
        self.assertEquals(msg_count({"recipients.address": "no_such_email@example.com"}), 0)
        self.assertEquals(msg_count({"recipients.address_contains": emails[0][3:]}), n)
        self.assertEquals(msg_count({"recipients.address_contains": emails[0][:3]}), n)
        self.assertEquals(msg_count({"recipients.name": "Rcpt1"}), n)
        self.assertEquals(msg_count({"recipients.name": "Rcpt"}), 0)
        self.assertEquals(msg_count({"recipients.name_contains": "Rcpt"}), n)
        self.assertEquals(msg_count({"sender.name": sender_name}), n)
        self.assertEquals(msg_count({"sender.name": "unknown"}), 0)
        self.assertEquals(msg_count({"sender.name": sender_name[0]}), 0)
        self.assertEquals(msg_count({"sender.name_contains": sender_name[0]}), n)
        self.assertEquals(msg_count({"sender.name_contains": sender_name[-1]}), n)
        self.assertEquals(msg_count({"sender.address": sender_addr}), n)
        self.assertEquals(msg_count({"sender.address": sender_addr[0]}), 0)
        self.assertEquals(msg_count({"sender.address_contains": sender_addr[0]}), n)
        self.assertEquals(msg_count({"sender.address_contains": sender_addr[-1]}), n)

        now = utcnow()
        self.assertEquals(msg_count({"created_at_lt": before_send}), n)
        self.assertEquals(msg_count({"created_at_gt": before_send}), 1)
        self.assertEquals(msg_count({"created_at_lt": now}), n + 1)
        self.assertEquals(msg_count({"created_at_gt": now}), 0)

    def test_different_boxes_and_deletion(self):
        password1 = "pass1"
        password2 = "pass2"
        user = "inbox"
        n = 5

        def message_count(user, password):
            return self.get("/messages/", headers=auth(user, password)).json["message_count"]

        for i in range(n):
            self.send(user, password1)
            self.send(user, password2)

        self.assertEquals(message_count(user, password1), n)
        self.assertEquals(message_count(user, password2), n)

        one_message = self.get("/messages/", headers=auth(user, password1)).json["message_list"][0]
        self.delete("/messages/{}".format(one_message["_id"]), headers=auth(user, password1))
        self.assertEquals(
            self.delete("/messages/{}".format(one_message["_id"]),
                        headers=auth(user, password1), raise_errors=False).status_code,
            404
        )
        self.assertEquals(message_count(user, password1), n - 1)
        self.delete("/messages/", headers=auth(user, password1))
        self.assertEquals(message_count(user, password1), 0)

        n_new = 2
        new_subject = "new subject"
        for i in range(n_new):
            self.send(user, password2, subject=new_subject)

        self.assertEquals(message_count(user, password2), n + n_new)
        self.delete("/messages/", headers=auth(user, password2), params={"subject": new_subject})
        self.assertEquals(message_count(user, password2), n)

    def test_read_flag(self):
        n_read = 5
        n_unread = 3
        subject_read = "read emails"
        subject_unread = "unread emails"

        for i in range(n_read):
            self.send(subject=subject_read)
        for i in range(n_unread):
            self.send(subject=subject_unread)

        self.assertEquals(self.get("/messages/", {"subject": subject_read}).json["message_count"], n_read)
        self.assertEquals(self.get("/messages/", {"read": False}).json["message_count"], n_unread)
        self.assertEquals(self.get("/messages/", {"read": False}).json["message_count"], 0)
        self.assertEquals(self.get("/messages/").json["message_count"], n_unread + n_read)

    def test_get_inboxes(self):
        inboxes = ["first", "second", "third"]
        for inbox in inboxes:
            self.send(inbox)
        self.send("another_inbox", "another_password")
        retreived = self.get("/inboxes/", headers=auth(None, self.password)).json["inbox_list"]
        self.assertEquals(sorted(retreived), sorted(inboxes))
        self.assertEquals(self.get("/inboxes/", headers=auth(None, "unknown")).json["inbox_count"], 0)

    def test_binary_attach(self):
        binary_data = b"%PDF\x93"
        smtp_send_email(
            "test@example.com", "Binary test", "Test <asdf@exmapl.com>", "Text body да",
            user=self.inbox, password=self.password, port=self.port,
            attachments=[("filename.pd", binary_data)]
        )
        msg = self.get("/messages/").json["message_list"][0]
        self.assertEquals(self.get("/messages/{}/attachments/{}".format(msg["_id"], 1),
                                   parse_json=False).data, binary_data)

    def test_html_alternative_and_attach(self):
        binary_data = b"%PDF\x93"
        html_body = "<html><body><h1>hello</h1></body></html>"
        text_body = "Text body да"
        smtp_send_email(
            "test@example.com", "Binary test", "Test <asdf@exmapl.com>", text_body,
            user=self.inbox, password=self.password, port=self.port,
            attachments=[("filename.pd", binary_data)],
            html_body=html_body
        )
        msg = self.get("/messages/").json["message_list"][0]
        self.assertEqual(len(msg["parts"]), 3)
        self.assertEqual(msg["parts"][0]["body"], text_body)
        self.assertEqual(msg["parts"][1]["body"], html_body)
        self.assertIsNone(msg["parts"][2]["body"])
        self.assertEquals(self.get("/messages/{}/attachments/{}".format(msg["_id"], 2),
                                   parse_json=False).data, binary_data)

    def test_get_single_message(self):
        self.send()
        msg = self.get("/messages/").json["message_list"][0]
        msg2 = self.get("/messages/{0}".format(msg["_id"])).json["message_info"]

        msg.pop("read")
        msg2.pop("read")
        self.assertEquals(msg2, msg)

    def test_not_found(self):
        self.send()
        wrong_id = "56337fb2b2c79a71698baaaa"
        with self.assertRaises(InvalidStatus) as e:
            self.get("/messages/" + wrong_id)
        self.assertEquals(e.exception.response.status_code, 404)

        msg = self.get("/messages/").json["message_list"][0]

        for part in 0, 1, 2:
            with self.assertRaises(InvalidStatus):
                self.get("/messages/{0}/attachments/{1}".format(msg["_id"], part))
            self.assertEquals(e.exception.response.status_code, 404)

        with self.assertRaises(InvalidStatus) as e:
            self.get("/messages/{0}/attachments/1".format(wrong_id))
        self.assertEquals(e.exception.response.status_code, 404)

    def test_wrong_smtp_credentials(self):
        with self.assertRaises(SendEmailError) as e:
            self.send(user="\0\0")
        self.assertEquals(e.exception.args[0].smtp_code, 535)

        with self.assertRaises(SendEmailError) as e:
            smtp_send_email("to@example.com", "no credentials", "from@example.com", "body", port=self.port)
        self.assertEquals(e.exception.args[0].smtp_code, 530)

    def test_send_plain_message(self):
        text_body = "Text body"
        to = "asdf@exmapl.com"
        sender = "test@example.com"
        send_email_plain(
            sender, to, text_body.encode("utf-8"),
            user=self.inbox, password=self.password, port=self.port,
        )
        msg = self.get("/messages/").json["message_list"][0]
        self.assertEqual(msg["message_raw"], text_body)
        self.assertEqual(msg["recipients_raw"], to)
        self.assertEqual(msg["sender_raw"], sender)


def auth(user, password):
    return {"X-Mail-Inbox": user, "X-Mail-Password": password}
