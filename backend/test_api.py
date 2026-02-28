"""
Comprehensive test suite for TAM Backend API.
Tests all endpoints + verifies API key configuration.
Run: python test_api.py
"""

import requests
import json
import sys
import os
import time

BASE = "http://localhost:8000/api"
PASS = 0
FAIL = 0
RESULTS = []


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        RESULTS.append(("PASS", name))
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL += 1
        RESULTS.append(("FAIL", name, str(e)))
        print(f"  FAIL  {name}  ->  {e}")


# ============================================================
# 1. HEALTH CHECK
# ============================================================
def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data['status']}"
    assert "version" in data, "Missing 'version' field"


# ============================================================
# 2. API KEY CONFIGURATION
# ============================================================
def test_api_key_loaded():
    """Verify the Anthropic API key is loaded in config."""
    sys.path.insert(0, os.path.dirname(__file__))
    from config import settings
    assert settings.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY is empty"
    assert settings.ANTHROPIC_API_KEY.startswith("sk-ant-"), \
        f"API key doesn't start with 'sk-ant-': {settings.ANTHROPIC_API_KEY[:10]}..."
    assert " " not in settings.ANTHROPIC_API_KEY, "API key contains spaces (likely .env formatting issue)"


def test_anthropic_client_init():
    """Verify the Anthropic client can be initialized."""
    from services.claude_service import _get_client
    try:
        client = _get_client()
        assert client is not None, "Client is None"
    except ValueError as e:
        raise AssertionError(f"Client init failed: {e}")


# ============================================================
# 3. DEALS CRUD
# ============================================================
def test_list_deals():
    r = requests.get(f"{BASE}/deals")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "deals" in data, "Missing 'deals' key"
    assert isinstance(data["deals"], list), "'deals' is not a list"
    # Should have at least the seed deal
    assert len(data["deals"]) >= 1, "No deals found (seed data missing?)"


def test_get_seed_deal():
    """Get the seeded demo deal."""
    r = requests.get(f"{BASE}/deals")
    deals = r.json()["deals"]
    seed = next((d for d in deals if d["target_company"] == "Apex Cloud Solutions"), None)
    assert seed is not None, "Seed deal 'Apex Cloud Solutions' not found"
    assert seed["status"] == "completed", f"Seed deal status: {seed['status']}"
    assert seed["deal_size"] == 45000000, f"Seed deal size: {seed['deal_size']}"
    return seed["id"]


def test_get_deal_detail():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["target_company"] == "Apex Cloud Solutions"
    assert "documents" in data, "Missing 'documents'"
    assert "analyses" in data, "Missing 'analyses'"
    assert len(data["analyses"]) >= 5, f"Expected >=5 analyses, got {len(data['analyses'])}"


def test_create_deal():
    r = requests.post(f"{BASE}/deals", json={
        "name": "Test Deal",
        "target_company": "Test Corp",
        "industry": "Technology",
        "deal_size": 1000000,
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["name"] == "Test Deal"
    assert data["target_company"] == "Test Corp"
    assert data["status"] == "pending"
    return data["id"]


def test_delete_deal():
    deal_id = test_create_deal()
    r = requests.delete(f"{BASE}/deals/{deal_id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    # Verify deleted
    r2 = requests.get(f"{BASE}/deals/{deal_id}")
    assert r2.status_code == 404, f"Expected 404 after delete, got {r2.status_code}"


def test_deal_not_found():
    r = requests.get(f"{BASE}/deals/99999")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"


# ============================================================
# 4. DOCUMENTS
# ============================================================
def test_list_documents():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/documents")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "documents" in data, "Missing 'documents'"
    assert len(data["documents"]) >= 1, "No documents found"


def test_upload_document():
    deal_id = test_create_deal()
    # Create a test file
    test_content = b"Revenue: $10M\nNet Income: $2M\nTotal Assets: $50M"
    files = [("files", ("test_financials.txt", test_content, "text/plain"))]
    r = requests.post(f"{BASE}/deals/{deal_id}/documents", files=files)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "documents" in data, "Missing 'documents'"
    assert len(data["documents"]) == 1
    assert data["documents"][0]["filename"] == "test_financials.txt"
    # Cleanup
    requests.delete(f"{BASE}/deals/{deal_id}")
    return deal_id


# ============================================================
# 5. ANALYSIS
# ============================================================
def test_list_analyses():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "analyses" in data, "Missing 'analyses'"
    types = {a["analysis_type"] for a in data["analyses"]}
    expected = {"qoe", "working_capital", "ratios", "dcf", "red_flags"}
    missing = expected - types
    assert not missing, f"Missing analysis types: {missing}"


def test_get_qoe_analysis():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis/qoe")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["status"] == "completed"
    results = data["results"]
    assert results is not None, "QoE results are None"
    assert "reported_ebitda" in results or "adjusted_ebitda" in results, \
        f"QoE missing key fields, got: {list(results.keys())[:5]}"


def test_get_ratios_analysis():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis/ratios")
    assert r.status_code == 200
    data = r.json()
    assert data["results"] is not None, "Ratios results are None"


def test_get_dcf_analysis():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis/dcf")
    assert r.status_code == 200
    data = r.json()
    assert data["results"] is not None, "DCF results are None"


def test_get_red_flags():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis/red_flags")
    assert r.status_code == 200
    data = r.json()
    assert data["results"] is not None, "Red flags results are None"


def test_get_ai_insights():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis/ai_insights")
    assert r.status_code == 200
    data = r.json()
    results = data["results"]
    assert results is not None, "AI insights results are None"
    assert "executive_summary" in results, "Missing executive_summary"


def test_analysis_not_found():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/analysis/nonexistent")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"


# ============================================================
# 6. CHAT
# ============================================================
def test_chat_send_message():
    """Test chat endpoint (requires working Claude API key)."""
    deal_id = test_get_seed_deal()
    r = requests.post(f"{BASE}/deals/{deal_id}/chat", json={
        "message": "What is the revenue of Apex Cloud Solutions?"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["role"] == "assistant", f"Expected role 'assistant', got {data['role']}"
    assert len(data["content"]) > 0, "Empty response content"
    # If API key works, the response should NOT contain error messages
    content = data["content"].lower()
    assert "api key" not in content or "not set" not in content, \
        f"API key error in response: {data['content'][:100]}"
    return data


def test_chat_history():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/chat")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "messages" in data, "Missing 'messages'"


def test_clear_chat():
    deal_id = test_get_seed_deal()
    r = requests.delete(f"{BASE}/deals/{deal_id}/chat")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"


# ============================================================
# 7. REPORTS
# ============================================================
def test_list_reports():
    deal_id = test_get_seed_deal()
    r = requests.get(f"{BASE}/deals/{deal_id}/reports")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "reports" in data, "Missing 'reports'"


def test_trigger_report_generation():
    deal_id = test_get_seed_deal()
    r = requests.post(f"{BASE}/deals/{deal_id}/reports/iar")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "report_id" in data, "Missing 'report_id'"
    assert data["status"] == "generating"


# ============================================================
# 8. TRIGGER ANALYSIS PIPELINE
# ============================================================
def test_trigger_analysis():
    deal_id = test_create_deal()
    # Upload a doc first
    test_content = b"Revenue: $10M\nNet Income: $2M\nTotal Assets: $50M"
    files = [("files", ("financials.txt", test_content, "text/plain"))]
    requests.post(f"{BASE}/deals/{deal_id}/documents", files=files)

    r = requests.post(f"{BASE}/deals/{deal_id}/analyze")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["status"] == "analyzing"
    # Cleanup after a short wait
    time.sleep(1)
    requests.delete(f"{BASE}/deals/{deal_id}")


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TAM Backend Test Suite")
    print("=" * 60)

    # Check server is running
    try:
        requests.get(f"{BASE}/health", timeout=3)
    except requests.ConnectionError:
        print("\n  ERROR: Backend not running at http://localhost:8000")
        print("  Start it with: uvicorn main:app --reload")
        sys.exit(1)

    print("\n--- Health & Config ---")
    test("Health check", test_health)
    test("API key loaded in config", test_api_key_loaded)
    test("Anthropic client initializes", test_anthropic_client_init)

    print("\n--- Deals CRUD ---")
    test("List deals", test_list_deals)
    test("Get seed deal (Apex Cloud Solutions)", test_get_seed_deal)
    test("Get deal detail with documents & analyses", test_get_deal_detail)
    test("Create deal", test_create_deal)
    test("Delete deal", test_delete_deal)
    test("Deal not found (404)", test_deal_not_found)

    print("\n--- Documents ---")
    test("List documents for seed deal", test_list_documents)
    test("Upload document", test_upload_document)

    print("\n--- Analysis ---")
    test("List analyses for seed deal", test_list_analyses)
    test("Get QoE analysis", test_get_qoe_analysis)
    test("Get ratios analysis", test_get_ratios_analysis)
    test("Get DCF analysis", test_get_dcf_analysis)
    test("Get red flags", test_get_red_flags)
    test("Get AI insights", test_get_ai_insights)
    test("Analysis not found (404)", test_analysis_not_found)
    test("Trigger analysis pipeline", test_trigger_analysis)

    print("\n--- Chat (uses Anthropic API) ---")
    test("Send chat message", test_chat_send_message)
    test("Get chat history", test_chat_history)
    test("Clear chat", test_clear_chat)

    print("\n--- Reports ---")
    test("List reports", test_list_reports)
    test("Trigger report generation", test_trigger_report_generation)

    # Summary
    print("\n" + "=" * 60)
    print(f"  RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 60)

    if FAIL > 0:
        print("\n  Failed tests:")
        for r in RESULTS:
            if r[0] == "FAIL":
                print(f"    - {r[1]}: {r[2]}")

    print()
    sys.exit(0 if FAIL == 0 else 1)
