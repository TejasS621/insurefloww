"""Startup data seeder for the provider backend.

Seeds providers, insurance plans, and add-ons into the database on first boot.
All operations are idempotent â€” existing records are never overwritten.
"""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.provider_backend.core.models.addon_model import AddOn, AddOnStatus
from backend.provider_backend.core.models.insurance_plan_model import InsurancePlan, InsurancePlanStatus
from backend.provider_backend.core.models.provider_model import Provider, ProviderStatus
from backend.provider_backend.core.models.shared import InsuranceType

import logging

logger = logging.getLogger(__name__)

PROVIDERS = [
    {
        "provider_code": "DEMO_PROVIDER",
        "provider_name": "InsureFlow Demo Provider",
        "company_name": "InsureFlow Demo Provider",
        "contact_email": "support@demo-provider.in",
        "contact_phone": "9800000001",
        "supported_insurance_types": ["HEALTH", "VEHICLE", "TRAVEL", "HOME"],
        "supported_regions": ["PAN_INDIA"],
        "serviceable_products": ["Retail Policies", "Family Floaters"],
        "notes": "Default seeded provider used for local demo flows.",
        "webhook_url": "http://127.0.0.1:8001/api/v1/provider/webhook",
        "status": ProviderStatus.ACTIVE,
    },
    {
        "provider_code": "HDFC_ERGO",
        "provider_name": "HDFC ERGO Health Insurance",
        "company_name": "HDFC ERGO General Insurance Company Limited",
        "contact_email": "support@hdfcergo.com",
        "contact_phone": "9800000002",
        "supported_insurance_types": ["HEALTH"],
        "supported_regions": ["PAN_INDIA"],
        "serviceable_products": ["Retail Health", "Family Health"],
        "webhook_url": "http://127.0.0.1:8001/api/v1/provider/webhook",
        "status": ProviderStatus.ACTIVE,
    },
    {
        "provider_code": "STAR_HEALTH",
        "provider_name": "Star Health & Allied Insurance",
        "company_name": "Star Health & Allied Insurance Co. Ltd.",
        "contact_email": "care@starhealth.in",
        "contact_phone": "9800000003",
        "supported_insurance_types": ["HEALTH"],
        "supported_regions": ["PAN_INDIA"],
        "serviceable_products": ["Individual Health", "Senior Citizen Health"],
        "webhook_url": "http://127.0.0.1:8001/api/v1/provider/webhook",
        "status": ProviderStatus.ACTIVE,
    },
    {
        "provider_code": "LIC_INDIA",
        "provider_name": "Life Insurance Corporation of India",
        "company_name": "Life Insurance Corporation of India",
        "contact_email": "info@licindia.in",
        "contact_phone": "9800000004",
        "supported_insurance_types": ["LIFE"],
        "supported_regions": ["PAN_INDIA"],
        "serviceable_products": ["Term Life", "Savings Plans"],
        "webhook_url": "http://127.0.0.1:8001/api/v1/provider/webhook",
        "status": ProviderStatus.ACTIVE,
    },
]

PLANS = [
    # â”€â”€ HEALTH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "plan_code": "HLTH-BASIC-001",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "plan_name": "Health Shield Basic",
        "coverage_options": [300000.0, 500000.0, 750000.0],
        "base_premium_rules": {"base_rate": 0.025, "age_factor": 1.0},
        "benefits": [
            "Hospitalisation cover up to sum insured",
            "Pre & post hospitalisation (30/60 days)",
            "Day-care procedures",
            "Ambulance cover â‚¹2,000/claim",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "HLTH-PLUS-002",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "plan_name": "Health Shield Plus",
        "coverage_options": [500000.0, 1000000.0, 1500000.0],
        "base_premium_rules": {"base_rate": 0.028, "age_factor": 1.0},
        "benefits": [
            "All Basic benefits",
            "Maternity cover",
            "OPD cover â‚¹5,000/year",
            "No-claim bonus 10% per year",
            "Free annual health check-up",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "HLTH-MAX-003",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "plan_name": "Health Shield Max",
        "coverage_options": [1000000.0, 2000000.0, 5000000.0],
        "base_premium_rules": {"base_rate": 0.032, "age_factor": 1.1},
        "benefits": [
            "All Plus benefits",
            "International emergency cover",
            "Critical illness rider",
            "Mental wellness sessions",
            "Restoration benefit up to 100%",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    # â”€â”€ LIFE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "plan_code": "LIFE-TERM-001",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.LIFE,
        "plan_name": "SecureLife Term Plan",
        "coverage_options": [2500000.0, 5000000.0, 10000000.0],
        "base_premium_rules": {"base_rate": 0.008, "age_factor": 1.0},
        "benefits": [
            "Pure term life cover",
            "Death benefit to nominee",
            "Accidental death benefit (2Ã— SA)",
            "Premium waiver on disability",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "LIFE-ENDOW-002",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.LIFE,
        "plan_name": "SecureLife Endowment Plan",
        "coverage_options": [1000000.0, 2500000.0, 5000000.0],
        "base_premium_rules": {"base_rate": 0.045, "age_factor": 1.05},
        "benefits": [
            "Life cover + savings component",
            "Maturity benefit = sum assured",
            "Bonus additions every year",
            "Loan facility up to 90% of surrender value",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "LIFE-ULIP-003",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.LIFE,
        "plan_name": "SecureLife ULIP Growth",
        "coverage_options": [1000000.0, 3000000.0, 5000000.0],
        "base_premium_rules": {"base_rate": 0.05, "age_factor": 1.1},
        "benefits": [
            "Market-linked returns",
            "Life cover = 10Ã— annual premium",
            "Switch between 6 fund options",
            "Partial withdrawals after 5 years",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    # â”€â”€ VEHICLE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "plan_code": "VEH-3P-001",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.VEHICLE,
        "plan_name": "AutoShield Third Party",
        "coverage_options": [750000.0],
        "base_premium_rules": {"base_rate": 0.015, "age_factor": 1.0},
        "benefits": [
            "Third-party liability (mandatory)",
            "Personal accident cover â‚¹15 lakh",
            "Legal liability to paid driver",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "VEH-COMP-002",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.VEHICLE,
        "plan_name": "AutoShield Comprehensive",
        "coverage_options": [500000.0, 1000000.0, 2000000.0],
        "base_premium_rules": {"base_rate": 0.025, "age_factor": 1.0},
        "benefits": [
            "All third-party benefits",
            "Own damage cover",
            "Theft & natural calamities",
            "24Ã—7 roadside assistance",
            "Cashless repair at 3,000+ garages",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    # â”€â”€ TRAVEL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "plan_code": "TRVL-BASIC-001",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.TRAVEL,
        "plan_name": "JourneyGuard Basic",
        "coverage_options": [200000.0, 500000.0],
        "base_premium_rules": {"base_rate": 0.012, "age_factor": 1.0},
        "benefits": [
            "Emergency medical expenses",
            "Trip cancellation/interruption",
            "Baggage delay/loss",
            "Passport loss",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "TRVL-GLOBAL-002",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.TRAVEL,
        "plan_name": "JourneyGuard Global",
        "coverage_options": [500000.0, 1000000.0, 5000000.0],
        "base_premium_rules": {"base_rate": 0.018, "age_factor": 1.05},
        "benefits": [
            "All Basic benefits",
            "Medical evacuation",
            "Adventure sports cover",
            "Flight delay compensation",
            "Hijack distress allowance",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    # â”€â”€ HOME â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    {
        "plan_code": "HOME-BASIC-001",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HOME,
        "plan_name": "HomeGuard Essentials",
        "coverage_options": [1000000.0, 2000000.0],
        "base_premium_rules": {"base_rate": 0.005, "age_factor": 1.0},
        "benefits": [
            "Building structure cover",
            "Fire & allied perils",
            "Earthquake cover",
            "Burglary & theft",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
    {
        "plan_code": "HOME-PREMIUM-002",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HOME,
        "plan_name": "HomeGuard Premium",
        "coverage_options": [2000000.0, 5000000.0, 10000000.0],
        "base_premium_rules": {"base_rate": 0.007, "age_factor": 1.05},
        "benefits": [
            "All Essentials benefits",
            "Contents cover (furniture, electronics)",
            "Tenant liability",
            "Temporary accommodation expenses",
            "Home loan protector",
        ],
        "status": InsurancePlanStatus.ACTIVE,
    },
]

ADDONS = [
    # Health add-ons
    {
        "addon_code": "HLTH-ADDON-MATERNITY",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "addon_name": "Maternity Cover",
        "addon_description": "Covers normal & C-section delivery expenses up to â‚¹50,000.",
        "addon_price": 2500.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "HLTH-ADDON-DENTAL",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "addon_name": "Dental & Vision Care",
        "addon_description": "Annual OPD cover for dental check-ups and vision correction.",
        "addon_price": 1200.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "HLTH-ADDON-CRITILLNESS",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "addon_name": "Critical Illness Rider",
        "addon_description": "Lump-sum payout on diagnosis of 30+ critical illnesses.",
        "addon_price": 3500.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "HLTH-ADDON-PERSONAL-ACC",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HEALTH,
        "addon_name": "Personal Accident Cover",
        "addon_description": "Accidental death and permanent disability benefit â‚¹5 lakh.",
        "addon_price": 800.0,
        "status": AddOnStatus.ACTIVE,
    },
    # Life add-ons
    {
        "addon_code": "LIFE-ADDON-ACC-DEATH",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.LIFE,
        "addon_name": "Accidental Death Benefit",
        "addon_description": "Additional sum assured paid on accidental death.",
        "addon_price": 1500.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "LIFE-ADDON-WAIVER",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.LIFE,
        "addon_name": "Premium Waiver on Disability",
        "addon_description": "Future premiums waived on permanent total disability.",
        "addon_price": 900.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "LIFE-ADDON-CRIT",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.LIFE,
        "addon_name": "Critical Illness Cover",
        "addon_description": "Accelerated benefit on diagnosis of critical illness.",
        "addon_price": 2000.0,
        "status": AddOnStatus.ACTIVE,
    },
    # Vehicle add-ons
    {
        "addon_code": "VEH-ADDON-ZERO-DEP",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.VEHICLE,
        "addon_name": "Zero Depreciation Cover",
        "addon_description": "Full claim without depreciation deduction on parts.",
        "addon_price": 2000.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "VEH-ADDON-RSA",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.VEHICLE,
        "addon_name": "24Ã—7 Roadside Assistance",
        "addon_description": "Towing, fuel delivery, flat tyre & emergency keys.",
        "addon_price": 750.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "VEH-ADDON-ENGINE",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.VEHICLE,
        "addon_name": "Engine & Gearbox Protection",
        "addon_description": "Covers repair of engine and gearbox damage due to water ingression.",
        "addon_price": 1500.0,
        "status": AddOnStatus.ACTIVE,
    },
    # Travel add-ons
    {
        "addon_code": "TRVL-ADDON-SPORTS",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.TRAVEL,
        "addon_name": "Adventure Sports Cover",
        "addon_description": "Covers injuries from trekking, skiing, paragliding etc.",
        "addon_price": 1000.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "TRVL-ADDON-CANCEL",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.TRAVEL,
        "addon_name": "Trip Cancellation Premium",
        "addon_description": "Full non-refundable trip cost reimbursed on covered cancellations.",
        "addon_price": 800.0,
        "status": AddOnStatus.ACTIVE,
    },
    # Home add-ons
    {
        "addon_code": "HOME-ADDON-CONTENTS",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HOME,
        "addon_name": "Contents & Electronics Cover",
        "addon_description": "Covers furniture, white goods, laptops and mobiles.",
        "addon_price": 1800.0,
        "status": AddOnStatus.ACTIVE,
    },
    {
        "addon_code": "HOME-ADDON-FLOOD",
        "provider_code": "DEMO_PROVIDER",
        "insurance_type": InsuranceType.HOME,
        "addon_name": "Flood & Landslide Cover",
        "addon_description": "Extended cover for flood-related structural damage.",
        "addon_price": 2500.0,
        "status": AddOnStatus.ACTIVE,
    },
]


async def _backfill_legacy_provider_documents(engine: AIOEngine) -> None:
    """Populate newly-added provider fields on older MongoDB documents."""

    collection = engine.get_collection(Provider)
    await collection.update_many(
        {"company_name": {"$exists": False}},
        {"$set": {"company_name": None}},
    )
    await collection.update_many(
        {"supported_insurance_types": {"$exists": False}},
        {"$set": {"supported_insurance_types": []}},
    )
    await collection.update_many(
        {"supported_regions": {"$exists": False}},
        {"$set": {"supported_regions": []}},
    )
    await collection.update_many(
        {"serviceable_products": {"$exists": False}},
        {"$set": {"serviceable_products": []}},
    )
    await collection.update_many(
        {"notes": {"$exists": False}},
        {"$set": {"notes": None}},
    )


async def seed_catalog(engine: AIOEngine) -> None:
    """Seed providers, plans and add-ons.  Safe to call on every startup."""
    await _backfill_legacy_provider_documents(engine)

    # â”€â”€ Providers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for p in PROVIDERS:
        existing = await engine.find_one(Provider, Provider.provider_code == p["provider_code"])
        if not existing:
            await engine.save(Provider(**p))
            logger.info("Seeded provider: %s", p["provider_code"])

    # â”€â”€ Plans â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for pl in PLANS:
        existing = await engine.find_one(InsurancePlan, InsurancePlan.plan_code == pl["plan_code"])
        if not existing:
            await engine.save(InsurancePlan(**pl))
            logger.info("Seeded insurance plan: %s", pl["plan_code"])

    # â”€â”€ Add-ons â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for ao in ADDONS:
        existing = await engine.find_one(AddOn, AddOn.addon_code == ao["addon_code"])
        if not existing:
            await engine.save(AddOn(**ao))
            logger.info("Seeded add-on: %s", ao["addon_code"])
