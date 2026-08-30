import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from credits import HOURS_5, remaining_seconds
from db import connect, get_or_create_session, wallet
from pay import (
    PayError,
    claim,
    normalize_block_code,
    parse_charge_html,
    parse_contact,
    start_checkout,
)

URL_A = "https://app.conta.vc/pay/fuzzy/c/AAA111open"
URL_B = "https://app.conta.vc/pay/fuzzy/c/BBB222open"


def always_open(_url: str) -> dict:
    return {"status": "open"}


def always_closed(_url: str) -> dict:
    return {"status": "closed"}


class PayFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "t.sqlite")
        self.links = Path(self.tmp.name) / "links.txt"
        self.links.write_text(f"{URL_A}\n{URL_B}\n", encoding="utf-8")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def _session(self, token="token-pay-abcdefghijk", sid="sid-pay"):
        return get_or_create_session(self.conn, token, sid)

    def _checkout(self, session_id, inspect=always_open):
        return start_checkout(
            self.conn, session_id, inspect=inspect, links_file=self.links
        )

    def test_parse_contact_email_and_whatsapp(self):
        self.assertEqual(parse_contact("Você@Mail.com"), ("email", "você@mail.com"))
        self.assertEqual(parse_contact("11 98888-1234"), ("whatsapp", "5511988881234"))
        self.assertIsNone(parse_contact("  "))
        with self.assertRaises(PayError):
            parse_contact("abc")

    def test_normalize_block_code(self):
        self.assertEqual(normalize_block_code("wdtsot-7K2M"), "wdtsot-7K2M")
        self.assertEqual(normalize_block_code("WDTSOT-7k2m"), "wdtsot-7K2M")
        self.assertEqual(normalize_block_code("7K2M"), "wdtsot-7K2M")
        self.assertIsNone(normalize_block_code("xyz"))

    def test_parse_charge_html_open_and_closed(self):
        self.assertEqual(parse_charge_html('<span>Open</span> Generate PIX').get("status"), "open")
        self.assertEqual(parse_charge_html("<span>Closed</span>").get("status"), "closed")
        self.assertEqual(parse_charge_html('<span>Paid</span>').get("status"), "closed")
        self.assertEqual(parse_charge_html('<p>Link closed</p>').get("status"), "closed")

    def test_checkout_is_pending_and_does_not_credit(self):
        row = self._session()
        checkout = self._checkout(row["id"])
        self.assertTrue(checkout["block_code"].startswith("wdtsot-"))
        self.assertEqual(checkout["pay_url"], URL_A)
        self.assertEqual(checkout["status"], "pending")
        again = self._checkout(row["id"])
        self.assertEqual(again["block_code"], checkout["block_code"])
        self.assertEqual(again["pay_url"], URL_A)
        w = wallet(self.conn, row["id"])
        self.assertEqual(w["purchased_seconds"], 0)

    def test_two_sessions_get_different_open_links(self):
        a = self._session("token-a-abcdefghijklmn", "sid-a")
        b = get_or_create_session(self.conn, "token-b-abcdefghijklmn", "sid-b")
        first = self._checkout(a["id"])
        second = self._checkout(b["id"])
        self.assertEqual(first["pay_url"], URL_A)
        self.assertEqual(second["pay_url"], URL_B)
        self.assertNotEqual(first["block_code"], second["block_code"])

    def test_abandoned_checkout_leaves_zero_balance(self):
        row = self._session()
        self._checkout(row["id"])
        w = wallet(self.conn, row["id"])
        self.assertEqual(remaining_seconds(w["purchased_seconds"], w["consumed_seconds"]), 0)

    def test_claim_while_open_does_not_credit(self):
        row = self._session()
        checkout = self._checkout(row["id"])
        with self.assertRaises(PayError):
            claim(
                self.conn,
                row["id"],
                contact="ana@wdtsot.shop",
                code=checkout["block_code"],
                inspect=always_open,
            )
        w = wallet(self.conn, row["id"])
        self.assertEqual(w["purchased_seconds"], 0)

    def test_claim_with_code_credits_once_when_closed(self):
        row = self._session()
        checkout = self._checkout(row["id"])
        first = claim(
            self.conn,
            row["id"],
            contact="ana@wdtsot.shop",
            code=checkout["block_code"],
            inspect=always_closed,
        )
        self.assertTrue(first["paid"])
        self.assertEqual(first["remaining_seconds"], HOURS_5)
        self.assertEqual(first["block_code"], checkout["block_code"])
        second = claim(
            self.conn,
            row["id"],
            contact="ana@wdtsot.shop",
            code=checkout["block_code"],
            inspect=always_closed,
        )
        self.assertEqual(second["remaining_seconds"], HOURS_5)

    def test_cookie_claim_without_code_after_closed_charge(self):
        row = self._session()
        self._checkout(row["id"])
        result = claim(self.conn, row["id"], contact="11977776666", inspect=always_closed)
        self.assertTrue(result["paid"])
        self.assertEqual(result["remaining_seconds"], HOURS_5)

    def test_same_email_resumes_same_wallet(self):
        paid = self._session("token-a-abcdefghijklmn", "sid-a")
        checkout = self._checkout(paid["id"])
        claim(
            self.conn,
            paid["id"],
            contact="volta@wdtsot.shop",
            code=checkout["block_code"],
            inspect=always_closed,
        )

        other = get_or_create_session(self.conn, "token-b-abcdefghijklmn", "sid-b")
        resumed = claim(self.conn, other["id"], contact="volta@wdtsot.shop", inspect=always_open)
        self.assertEqual(resumed["session_id"], paid["id"])
        self.assertEqual(resumed["remaining_seconds"], HOURS_5)
        self.assertEqual(resumed["public_token"], paid["public_token"])
        other_wallet = wallet(self.conn, other["id"])
        self.assertEqual(other_wallet["purchased_seconds"], 0)

    def test_unknown_contact_without_purchase_fails(self):
        row = self._session()
        with self.assertRaises(PayError):
            claim(
                self.conn,
                row["id"],
                contact="ninguém@wdtsot.shop",
                inspect=always_open,
                links_file=self.links,
            )

    def test_unknown_code_fails(self):
        row = self._session()
        with self.assertRaises(PayError):
            claim(self.conn, row["id"], code="wdtsot-ZZZZ")

    def test_empty_open_stock_fails_checkout(self):
        row = self._session()
        self.links.write_text("", encoding="utf-8")
        with self.assertRaises(PayError):
            start_checkout(
                self.conn,
                row["id"],
                inspect=always_closed,
                links_file=self.links,
            )

    def test_orphan_closed_charge_claimed_with_contact(self):
        row = self._session()
        first = claim(
            self.conn,
            row["id"],
            contact="amigo@wdtsot.shop",
            inspect=lambda url: {"status": "closed" if url == URL_A else "open"},
            links_file=self.links,
        )
        self.assertTrue(first["paid"])
        self.assertEqual(first["remaining_seconds"], HOURS_5)
        self.assertTrue(first["block_code"].startswith("wdtsot-"))
        again = claim(
            self.conn,
            row["id"],
            contact="amigo@wdtsot.shop",
            inspect=always_open,
            links_file=self.links,
        )
        self.assertEqual(again["remaining_seconds"], HOURS_5)
        self.assertEqual(again["block_code"], first["block_code"])

    def test_orphan_closed_charge_claimed_with_pay_url(self):
        row = self._session()
        result = claim(
            self.conn,
            row["id"],
            contact="11966665555",
            pay_url=URL_B,
            inspect=lambda url: {"status": "closed" if url == URL_B else "open"},
            links_file=self.links,
        )
        self.assertTrue(result["paid"])
        self.assertEqual(result["remaining_seconds"], HOURS_5)

    def test_two_closed_orphans_require_the_paid_url(self):
        row = self._session()
        with self.assertRaises(PayError):
            claim(
                self.conn,
                row["id"],
                contact="dois@wdtsot.shop",
                inspect=always_closed,
                links_file=self.links,
            )
        result = claim(
            self.conn,
            row["id"],
            contact="dois@wdtsot.shop",
            code=URL_A,
            inspect=always_closed,
            links_file=self.links,
        )
        self.assertTrue(result["paid"])

    def test_block_code_wins_over_a_different_open_pay_url(self):
        owner = self._session("token-a-abcdefghijklmn", "sid-a")
        checkout = self._checkout(owner["id"])
        claim(
            self.conn,
            owner["id"],
            contact="dono@wdtsot.shop",
            code=checkout["block_code"],
            inspect=always_closed,
            links_file=self.links,
        )
        other = get_or_create_session(self.conn, "token-b-abcdefghijklmn", "sid-b")
        resumed = claim(
            self.conn,
            other["id"],
            contact="dono@wdtsot.shop",
            code=checkout["block_code"],
            pay_url=URL_B,
            inspect=always_open,
            links_file=self.links,
        )
        self.assertEqual(resumed["session_id"], owner["id"])
        self.assertEqual(resumed["remaining_seconds"], HOURS_5)

    def test_paid_url_cannot_be_claimed_twice_by_strangers(self):
        owner = self._session("token-a-abcdefghijklmn", "sid-a")
        claim(
            self.conn,
            owner["id"],
            contact="dono@wdtsot.shop",
            pay_url=URL_A,
            inspect=always_closed,
            links_file=self.links,
        )
        other = get_or_create_session(self.conn, "token-b-abcdefghijklmn", "sid-b")
        with self.assertRaises(PayError):
            claim(
                self.conn,
                other["id"],
                contact="outro@wdtsot.shop",
                pay_url=URL_A,
                inspect=always_closed,
                links_file=self.links,
            )


if __name__ == "__main__":
    unittest.main()
