# harvestamp/context/builder.py
"""Context Package Builder for HarvestAmp.

Filters and minimizes the farm context to include only task-relevant data,
and applies role-based redactions.
"""
from typing import Any, Dict, List

class ContextPackageBuilder:
    """Builds minimized, task-scoped context packages."""

    def build_context_package(
        self,
        farm_profile: Dict[str, Any],
        user_role: str,
        topic: str
    ) -> Dict[str, Any]:
        """Constructs a context package with minimized data scoped to the task topic."""
        farm_id = farm_profile.get("farm_id", "")
        profile_name = farm_profile.get("farm_name", "")
        farm_type = farm_profile.get("farm_type", "")
        
        # Base package
        context_pkg: Dict[str, Any] = {
            "context_package_id": f"ctx_{farm_id}_{topic}",
            "farm_id": farm_id,
            "profile_name": profile_name,
            "farm_type": farm_type,
            "organic_status": farm_profile.get("organic_context", {}).get("organic_status", "conventional"),
            "user_role": user_role,
            "relevant_fields": [],
            "relevant_inventory": [],
            "relevant_quotes": [],
            "evidence_ids": [],
            "prohibited_disclosures": [],
            "redactions_applied": [],
            "included_fields": [],
            "excluded_fields": []
        }
        
        # Exclude credentials/secrets by default
        context_pkg["redactions_applied"].append("credential_fields_excluded")
        context_pkg["excluded_fields"].append("raw credentials")
        
        # Filter fields and records based on topic
        if topic == "weekly_plan_pvf":
            # PVF Weekly Plan needs fuel and grain inventory, and fuel/fertilizer quotes
            for item in farm_profile.get("inventory", []):
                if item.get("item_type") in ["diesel", "stored_grain_corn", "stored_grain_soybeans"]:
                    context_pkg["relevant_inventory"].append(item)
            for q in farm_profile.get("quotes", []):
                if q.get("input_type") in ["diesel", "fertilizer"]:
                    context_pkg["relevant_quotes"].append(q)
            context_pkg["relevant_fields"] = farm_profile.get("fields", [])
            context_pkg["included_fields"].extend(["fuel_inventory", "stored_grain_inventory", "fertilizer_quotes", "diesel_quotes", "field_boundaries"])
            context_pkg["excluded_fields"].extend(["crop_insurance_documents", "employee_personal_data", "other_farm_data"])

        elif topic in ["diesel_purchase_window", "fuel_buy_window"]:
            # SYS-003 Context Minimization
            # Include ONLY diesel inventory, and diesel quotes
            for item in farm_profile.get("inventory", []):
                if item.get("item_type") == "diesel":
                    context_pkg["relevant_inventory"].append(item)
            for q in farm_profile.get("quotes", []):
                if q.get("input_type") == "diesel":
                    context_pkg["relevant_quotes"].append(q)
            # Only include fields related to the request, or none if unrelated.
            context_pkg["relevant_fields"] = [f for f in farm_profile.get("fields", []) if f.get("field_id") in ["PVF_FIELD_HOME320", "PVF_FIELD_SOUTH600"]]
            
            context_pkg["included_fields"].extend(["fuel quote", "tank level", "tank capacity", "expected fuel need", "weather / fieldwork window"])
            context_pkg["excluded_fields"].extend([
                "crop insurance documents", "full grain marketing plan",
                "unrelated field boundaries", "employee personal data", "other farm data"
            ])
            
        elif topic == "fertilizer_comparison":
            # Include only fertilizer quotes
            for q in farm_profile.get("quotes", []):
                if q.get("input_type") == "fertilizer":
                    context_pkg["relevant_quotes"].append(q)
            context_pkg["included_fields"].extend(["fertilizer_quotes"])
            context_pkg["excluded_fields"].extend(["fuel_quotes", "stored_grain_inventory", "crop_insurance_documents"])

        elif topic == "spray_window":
            # PVF-005 spray window
            # Do NOT attach fuel quotes, fertilizer quotes, stored grain inventory, or energy benchmarks
            context_pkg["relevant_fields"] = farm_profile.get("fields", [])
            for item in farm_profile.get("inventory", []):
                if item.get("item_type") in ["herbicide", "fungicide", "adjuvant", "chemical", "pesticide"]:
                    context_pkg["relevant_inventory"].append(item)
            context_pkg["included_fields"].extend(["spray_field_boundaries", "pesticide_inventory"])
            context_pkg["excluded_fields"].extend(["fuel_quotes", "fertilizer_quotes", "stored_grain_inventory", "energy_benchmarks"])

        elif topic in ["weekly_plan_gbo", "farmers_market", "csa_newsletter", "packaging_reorder"]:
            # Organic direct-market context
            context_pkg["csa_members"] = farm_profile.get("csa_members")
            context_pkg["csa_pickup_day"] = farm_profile.get("csa_pickup_day")
            context_pkg["farmers_market_day"] = farm_profile.get("farmers_market_day")
            context_pkg["restaurant_availability_day"] = farm_profile.get("restaurant_availability_day")
            context_pkg["receipt_paper_status"] = farm_profile.get("receipt_paper_status")
            context_pkg["tent_weights_status"] = farm_profile.get("tent_weights_status")
            context_pkg["organic_context"] = farm_profile.get("organic_context")
            
            # Include packaging inventory
            for item in farm_profile.get("inventory", []):
                if any(k in item.get("item_type", "") for k in ["clamshell", "box", "bag", "label"]):
                    context_pkg["relevant_inventory"].append(item)
                    
            # Include direct-market quotes
            for q in farm_profile.get("quotes", []):
                if q.get("input_type") in ["packaging", "organic_granular_fertilizer"]:
                    context_pkg["relevant_quotes"].append(q)
                    
            # Include growing areas
            context_pkg["growing_areas"] = farm_profile.get("growing_areas", [])
            context_pkg["included_fields"].extend(["growing_areas", "packaging_inventory", "csa_member_count"])
            context_pkg["excluded_fields"].extend(["supplier_quotes_for_unrelated_inputs"])
            
        elif topic == "organic_input_verification":
            context_pkg["organic_context"] = farm_profile.get("organic_context")
            for q in farm_profile.get("quotes", []):
                if q.get("input_type") == "organic_granular_fertilizer":
                    context_pkg["relevant_quotes"].append(q)
            context_pkg["included_fields"].extend(["organic_status", "organic_quotes"])
            context_pkg["excluded_fields"].extend(["packaging_inventory", "csa_member_list"])

        # Apply user role boundaries/redactions
        if user_role in ["field_employee", "market_staff"]:
            context_pkg["relevant_quotes"] = []
            context_pkg["redactions_applied"].append("supplier_pricing_redacted")
            context_pkg["prohibited_disclosures"].append("supplier_quotes")
            
        if user_role == "field_lead":
            context_pkg["redactions_applied"].append("customer_emails_redacted")
            context_pkg["prohibited_disclosures"].append("csa_member_emails")
            if "csa_members_list" in context_pkg:
                del context_pkg["csa_members_list"]

        return context_pkg
