from app.models.schemas import LeadCreate, PaymentIntentCreate
from app.services.lead_store import create_lead
from app.services.payment_store import create_payment_intent, find_package, package_with_payment


def test_upi_payment_intent_for_quick_report():
    intent = create_payment_intent(PaymentIntentCreate(package_id="quick-risk-report", customer_name="Test User", project_name="Demo Token"))
    assert intent.id.startswith("pay_")
    assert intent.amount_inr == 999
    assert intent.upi_deep_link and intent.upi_deep_link.startswith("upi://pay")
    assert intent.manual_verification_required is True
    assert intent.status == "created"


def test_subscription_package_supports_monthly_cycle():
    package = find_package("builder-monthly")
    enriched = package_with_payment(package)
    assert package["category"] == "subscription"
    assert "monthly" in package["billing_cycles"]
    assert enriched["upi_payment"]["manual_verification_required"] is True


def test_lead_creation_sets_payment_pending_for_paid_package(tmp_path, monkeypatch):
    # Isolate lead storage from repository sample data.
    from app.core import config
    monkeypatch.setattr(config.settings, "leads_file", str(tmp_path / "leads.jsonl"))
    lead = create_lead(LeadCreate(
        name="Neeraj Kumar",
        email="neeraj@example.com",
        contact="telegram:@nk148026",
        project_name="Demo Launch",
        selected_package="quick-risk-report",
        package_id="quick-risk-report",
        payment_reference="UPI123456",
        authorization_confirmed=True,
        consent_confirmed=True,
        preferred_language="Hinglish",
    ))
    assert lead.status == "Payment Pending"
    assert lead.payment_status == "reference_submitted"
    assert lead.payment_amount_inr == 999
    assert lead.package_id == "quick-risk-report"
