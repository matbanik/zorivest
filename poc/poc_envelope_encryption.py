"""
Envelope Encryption PoC — End-to-End Test

Demonstrates that a single SQLCipher database can be accessed independently
via user passphrase OR API key, using envelope encryption (key wrapping).

Tests:
1. Initialize DB with passphrase → CREATE table + INSERT data
2. READ data back using passphrase (verify round-trip)
3. Generate API key (while DB unlocked with passphrase)
4. Close connection entirely
5. Re-open DB using API key only → READ same data
6. UPDATE data using API key
7. Close connection entirely
8. Re-open DB using passphrase → READ updated data
9. DELETE data using passphrase
10. Verify API key can see the deletion
11. Revoke API key → verify it can no longer unlock DB
12. Verify passphrase still works after revocation
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent for key_vault import
sys.path.insert(0, str(Path(__file__).parent))

import sqlcipher3
from key_vault import KeyVault


# --- Helpers ---

def open_db(db_path: str, dek: bytes) -> sqlcipher3.Connection:
    """Open a SQLCipher database with the given DEK."""
    conn = sqlcipher3.connect(db_path)
    conn.execute(f"PRAGMA key=\"x'{dek.hex()}'\"")
    # Verify the key works
    conn.execute("SELECT count(*) FROM sqlite_master")
    return conn


def print_header(msg: str) -> None:
    """Print a styled test header."""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def print_pass(msg: str) -> None:
    print(f"  ✅ PASS: {msg}")


def print_fail(msg: str) -> None:
    print(f"  ❌ FAIL: {msg}")


# --- Main PoC ---

def main():
    # Use a temp directory so we don't pollute the project
    with tempfile.TemporaryDirectory(prefix="zorivest_poc_") as tmpdir:
        tmpdir = Path(tmpdir)
        bootstrap_path = tmpdir / "bootstrap.json"
        db_path = str(tmpdir / "zorivest_poc.db")

        vault = KeyVault(bootstrap_path)
        vault.config.db_path = db_path

        PASSPHRASE = "MyStr0ng!Passphrase#2026"
        results = []

        # ─────────────────────────────────────────────────────────
        # TEST 1: Initialize with passphrase + CREATE + INSERT
        # ─────────────────────────────────────────────────────────
        print_header("TEST 1: Initialize DB with passphrase → CREATE + INSERT")

        dek = vault.initialize_with_passphrase(PASSPHRASE)
        conn = open_db(db_path, dek)

        conn.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exec_id TEXT UNIQUE NOT NULL,
                instrument TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO trades (exec_id, instrument, action, quantity, price) "
            "VALUES (?, ?, ?, ?, ?)",
            ("T001", "AAPL", "BOT", 100, 189.50)
        )
        conn.execute(
            "INSERT INTO trades (exec_id, instrument, action, quantity, price) "
            "VALUES (?, ?, ?, ?, ?)",
            ("T002", "MSFT", "SLD", 50, 415.25)
        )
        conn.commit()

        rows = conn.execute("SELECT * FROM trades ORDER BY id").fetchall()
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        print_pass(f"Created table + inserted {len(rows)} trades")
        results.append(("1. Init + CREATE + INSERT", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 2: READ data back using passphrase
        # ─────────────────────────────────────────────────────────
        print_header("TEST 2: Re-open with passphrase → READ")

        dek2 = vault.unlock_with_passphrase(PASSPHRASE)
        assert dek == dek2, "DEK mismatch after passphrase unlock!"
        conn = open_db(db_path, dek2)
        rows = conn.execute("SELECT * FROM trades ORDER BY id").fetchall()
        assert len(rows) == 2
        assert rows[0][1] == "T001"
        assert rows[1][1] == "T002"
        print_pass(f"Read {len(rows)} trades: {rows[0][2]} ({rows[0][3]}), {rows[1][2]} ({rows[1][3]})")
        results.append(("2. Passphrase READ", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 3: Generate API key
        # ─────────────────────────────────────────────────────────
        print_header("TEST 3: Generate API key (while DB unlocked)")

        # Need DEK available to wrap it with the API key
        dek3 = vault.unlock_with_passphrase(PASSPHRASE)
        api_key = vault.generate_api_key(
            dek3,
            role="read-write",
            scopes=["mcp:read", "mcp:tools"],
        )
        assert api_key.startswith("zrv_sk_")
        print_pass(f"API key generated: {api_key[:15]}...{api_key[-4:]}")
        print(f"  📋 Full API key (shown once): {api_key}")
        results.append(("3. Generate API key", True))

        # Verify bootstrap.json now has 2 entries
        import json
        bootstrap = json.loads(bootstrap_path.read_text())
        assert len(bootstrap["wrapped_keys"]) == 2
        print_pass(f"bootstrap.json has {len(bootstrap['wrapped_keys'])} wrapped key entries")

        # ─────────────────────────────────────────────────────────
        # TEST 4: READ using API key (independent of passphrase!)
        # ─────────────────────────────────────────────────────────
        print_header("TEST 4: Open DB using API key → READ")

        # Fresh vault to prove we're not reusing state
        vault2 = KeyVault(bootstrap_path)
        dek_from_api = vault2.unlock_with_api_key(api_key)
        assert dek_from_api == dek, "DEK from API key doesn't match original!"
        print_pass("API key unwrapped the same DEK as passphrase")

        conn = open_db(db_path, dek_from_api)
        rows = conn.execute("SELECT * FROM trades ORDER BY id").fetchall()
        assert len(rows) == 2
        print_pass(f"API key read {len(rows)} trades successfully")
        results.append(("4. API key READ", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 5: UPDATE using API key
        # ─────────────────────────────────────────────────────────
        print_header("TEST 5: UPDATE data using API key")

        dek_api = vault2.unlock_with_api_key(api_key)
        conn = open_db(db_path, dek_api)
        conn.execute(
            "UPDATE trades SET price = ? WHERE exec_id = ?",
            (195.00, "T001")
        )
        conn.commit()
        row = conn.execute("SELECT price FROM trades WHERE exec_id = 'T001'").fetchone()
        assert row[0] == 195.00, f"Expected 195.00, got {row[0]}"
        print_pass(f"Updated AAPL price to {row[0]} via API key")
        results.append(("5. API key UPDATE", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 6: Passphrase READ sees API key's UPDATE
        # ─────────────────────────────────────────────────────────
        print_header("TEST 6: Passphrase READ sees API key's UPDATE")

        vault3 = KeyVault(bootstrap_path)
        dek_pass = vault3.unlock_with_passphrase(PASSPHRASE)
        conn = open_db(db_path, dek_pass)
        row = conn.execute("SELECT price FROM trades WHERE exec_id = 'T001'").fetchone()
        assert row[0] == 195.00
        print_pass(f"Passphrase confirms AAPL price = {row[0]} (updated by API key)")
        results.append(("6. Cross-credential consistency", True))

        # ─────────────────────────────────────────────────────────
        # TEST 7: DELETE using passphrase
        # ─────────────────────────────────────────────────────────
        print_header("TEST 7: DELETE data using passphrase")

        conn.execute("DELETE FROM trades WHERE exec_id = 'T002'")
        conn.commit()
        count = conn.execute("SELECT count(*) FROM trades").fetchone()[0]
        assert count == 1
        print_pass(f"Deleted T002, remaining trades: {count}")
        results.append(("7. Passphrase DELETE", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 8: API key sees the DELETE
        # ─────────────────────────────────────────────────────────
        print_header("TEST 8: API key sees passphrase's DELETE")

        vault4 = KeyVault(bootstrap_path)
        dek_api2 = vault4.unlock_with_api_key(api_key)
        conn = open_db(db_path, dek_api2)
        count = conn.execute("SELECT count(*) FROM trades").fetchone()[0]
        assert count == 1
        remaining = conn.execute("SELECT exec_id, instrument, price FROM trades").fetchone()
        print_pass(f"API key confirms 1 trade remaining: {remaining}")
        results.append(("8. Cross-credential DELETE visibility", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 9: INSERT via API key
        # ─────────────────────────────────────────────────────────
        print_header("TEST 9: INSERT via API key (full CRUD cycle)")

        conn = open_db(db_path, dek_api2)
        conn.execute(
            "INSERT INTO trades (exec_id, instrument, action, quantity, price) "
            "VALUES (?, ?, ?, ?, ?)",
            ("T003", "GOOG", "BOT", 25, 178.30)
        )
        conn.commit()
        count = conn.execute("SELECT count(*) FROM trades").fetchone()[0]
        assert count == 2
        print_pass(f"API key inserted T003 (GOOG), total trades: {count}")
        results.append(("9. API key INSERT", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 10: Revoke API key → verify it no longer works
        # ─────────────────────────────────────────────────────────
        print_header("TEST 10: Revoke API key → verify rejection")

        vault5 = KeyVault(bootstrap_path)
        # Find the API key entry
        api_entry = [e for e in vault5.config.wrapped_keys if e["key_type"] == "api_key"][0]
        revoked = vault5.revoke_api_key(api_entry["key_id"])
        assert revoked, "Revocation failed"
        print_pass(f"Revoked key: {api_entry['key_id']}")

        try:
            vault5.unlock_with_api_key(api_key)
            print_fail("API key should have been rejected after revocation!")
            results.append(("10. API key revocation", False))
        except ValueError as e:
            print_pass(f"API key correctly rejected: {e}")
            results.append(("10. API key revocation", True))

        # ─────────────────────────────────────────────────────────
        # TEST 11: Passphrase still works after API key revocation
        # ─────────────────────────────────────────────────────────
        print_header("TEST 11: Passphrase still works after API key revocation")

        dek_final = vault5.unlock_with_passphrase(PASSPHRASE)
        conn = open_db(db_path, dek_final)
        count = conn.execute("SELECT count(*) FROM trades").fetchone()[0]
        assert count == 2
        all_trades = conn.execute("SELECT exec_id, instrument, action, price FROM trades ORDER BY id").fetchall()
        for t in all_trades:
            print(f"    Trade: {t[0]} | {t[1]} | {t[2]} | ${t[3]:.2f}")
        print_pass(f"Passphrase reads {count} trades after API key revocation")
        results.append(("11. Passphrase after revocation", True))
        conn.close()

        # ─────────────────────────────────────────────────────────
        # TEST 12: Wrong passphrase → rejected
        # ─────────────────────────────────────────────────────────
        print_header("TEST 12: Wrong passphrase → rejection")

        try:
            vault5.unlock_with_passphrase("WrongPassword123")
            print_fail("Wrong passphrase should have been rejected!")
            results.append(("12. Wrong passphrase rejection", False))
        except ValueError as e:
            print_pass(f"Correctly rejected: {e}")
            results.append(("12. Wrong passphrase rejection", True))

        # ─────────────────────────────────────────────────────────
        # SUMMARY
        # ─────────────────────────────────────────────────────────
        print_header("SUMMARY")
        passed = sum(1 for _, ok in results if ok)
        total = len(results)
        for name, ok in results:
            status = "✅" if ok else "❌"
            print(f"  {status} {name}")
        print(f"\n  {passed}/{total} tests passed")

        if passed == total:
            print("\n  🎉 ENVELOPE ENCRYPTION PoC VERIFIED SUCCESSFULLY!")
            print("  Both passphrase and API key can independently CRUD the same DB.")
        else:
            print("\n  ⚠️  Some tests failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
