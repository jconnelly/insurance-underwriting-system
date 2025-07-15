"""
Application evaluation page for the Streamlit underwriting application.

This page provides a comprehensive form for entering application data and
performing AI-enhanced underwriting evaluations.
"""

import streamlit as st
import asyncio
import time
import json
from datetime import datetime
from typing import Optional

from underwriting.core.ai_engine import AIEnhancedUnderwritingEngine
from underwriting.core.engine import UnderwritingEngine
from underwriting.core.models import Application
from underwriting.streamlit_app.components.forms import (
    create_driver_form,
    create_vehicle_form,
    create_violations_form,
    create_claims_form,
    create_application_metadata_form,
    validate_application_form,
    create_complete_application
)

def show_evaluation_page():
    """Display the application evaluation page."""
    
    st.markdown("## 📝 Application Evaluation")
    st.markdown("""
    Use this form to enter application details and get an AI-enhanced underwriting decision.
    All fields marked with * are required.
    """)
    
    # Initialize session state
    if "evaluation_result" not in st.session_state:
        st.session_state.evaluation_result = None
    if "current_application" not in st.session_state:
        st.session_state.current_application = None
    
    # Evaluation mode selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        evaluation_mode = st.radio(
            "Evaluation Mode",
            options=["AI-Enhanced (Recommended)", "Rules Only", "AI Only"],
            horizontal=True,
            help="Choose the evaluation approach"
        )
    
    with col2:
        rule_set = st.selectbox(
            "Rule Set",
            options=["standard", "conservative", "liberal"],
            help="Select the rule set to use"
        )
    
    st.markdown("---")
    
    # Create tabs for form sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Driver", "🚗 Vehicle", "🚨 Violations", "💰 Claims", "📋 Details"
    ])
    
    # Driver information tab
    with tab1:
        driver = create_driver_form("eval_driver")
        
        if driver:
            st.success("✅ Driver information is valid")
        else:
            st.warning("⚠️ Please complete driver information")
    
    # Vehicle information tab
    with tab2:
        vehicle = create_vehicle_form("eval_vehicle")
        
        if vehicle:
            st.success("✅ Vehicle information is valid")
        else:
            st.warning("⚠️ Please complete vehicle information")
    
    # Violations tab
    with tab3:
        violations = create_violations_form("eval_violations")
        
        if violations:
            st.info(f"📝 {len(violations)} violation(s) recorded")
        else:
            st.info("✅ No violations recorded")
    
    # Claims tab
    with tab4:
        claims = create_claims_form("eval_claims")
        
        if claims:
            st.info(f"📝 {len(claims)} claim(s) recorded")
        else:
            st.info("✅ No claims recorded")
    
    # Application details tab
    with tab5:
        metadata = create_application_metadata_form("eval_metadata")
        st.success("✅ Application details completed")
    
    st.markdown("---")
    
    # Evaluation actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(
            "🧠 Evaluate Application",
            type="primary",
            help="Perform underwriting evaluation",
            disabled=not (driver and vehicle)
        ):
            st.session_state.eval_driver_submit = True
            st.session_state.eval_vehicle_submit = True
            
            if validate_application_form(driver, vehicle):
                with st.spinner("Evaluating application..."):
                    application = create_complete_application(
                        driver, vehicle, violations, claims, metadata
                    )
                    
                    # Perform evaluation
                    result = asyncio.run(evaluate_application(
                        application, evaluation_mode, rule_set
                    ))
                    
                    st.session_state.evaluation_result = result
                    st.session_state.current_application = application
                    st.rerun()
    
    with col2:
        if st.button("🔄 Clear Form", help="Clear all form data"):
            clear_form_data()
            st.rerun()
    
    with col3:
        if st.button("📋 Load Sample", help="Load sample application data"):
            load_sample_data()
            st.rerun()
    
    with col4:
        if st.session_state.current_application:
            if st.button("💾 Save Application", help="Save application as JSON"):
                save_application_json(st.session_state.current_application)
    
    # Display results if available
    if st.session_state.evaluation_result:
        display_evaluation_results(st.session_state.evaluation_result)

async def evaluate_application(
    application: Application, 
    evaluation_mode: str, 
    rule_set: str
) -> dict:
    """Evaluate an application using the specified mode."""
    
    start_time = time.time()
    
    try:
        if evaluation_mode == "AI-Enhanced (Recommended)":
            engine = AIEnhancedUnderwritingEngine(ai_enabled=True)
            enhanced_decision = await engine.process_application_enhanced(
                application, rule_set
            )
            decision = enhanced_decision.final_decision
            ai_decision = enhanced_decision.ai_decision
            
        elif evaluation_mode == "Rules Only":
            engine = UnderwritingEngine()
            decision = engine.process_application(application, rule_set)
            ai_decision = None
            
        elif evaluation_mode == "AI Only":
            engine = AIEnhancedUnderwritingEngine(ai_enabled=True)
            enhanced_decision = await engine.process_application_enhanced(
                application, rule_set
            )
            # Use AI decision directly
            decision = enhanced_decision.final_decision
            ai_decision = enhanced_decision.ai_decision
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "decision": decision,
            "ai_decision": ai_decision,
            "evaluation_mode": evaluation_mode,
            "rule_set": rule_set,
            "processing_time": processing_time,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "error": str(e),
            "evaluation_mode": evaluation_mode,
            "rule_set": rule_set,
            "processing_time": processing_time,
            "timestamp": datetime.now()
        }

def display_evaluation_results(result: dict):
    """Display the evaluation results."""
    
    st.markdown("---")
    st.markdown("## 📊 Evaluation Results")
    
    if not result["success"]:
        st.error(f"❌ Evaluation failed: {result['error']}")
        return
    
    decision = result["decision"]
    
    # Debug: Check decision type
    if hasattr(decision, 'decision'):
        # It's an UnderwritingDecision object
        decision_value = decision.decision.value
        risk_score = decision.risk_score.overall_score
        reason = decision.reason
        triggered_rules = decision.triggered_rules
        additional_notes = decision.additional_notes
    else:
        # It's a DecisionType enum - this shouldn't happen but let's handle it
        st.error("⚠️ Received DecisionType instead of UnderwritingDecision")
        decision_value = decision.value
        risk_score = "N/A"
        reason = "No reason available"
        triggered_rules = []
        additional_notes = None
    
    # Main decision display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        decision_color = {
            "ACCEPT": "🟢",
            "DENY": "🔴",
            "ADJUDICATE": "🟡"
        }.get(decision_value, "O")
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-radius: 10px; margin-bottom: 1rem;">
            <h2>{decision_color} {decision_value}</h2>
            <p>Final Underwriting Decision</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric(
            "Risk Score",
            f"{risk_score}",
            help="Overall risk assessment score"
        )
        
        st.metric(
            "Processing Time",
            f"{result['processing_time']:.2f}s",
            help="Time taken to process the application"
        )
    
    with col3:
        st.metric(
            "Evaluation Mode",
            result["evaluation_mode"],
            help="Method used for evaluation"
        )
        
        st.metric(
            "Rule Set",
            result["rule_set"].title(),
            help="Rule set applied during evaluation"
        )
    
    # Detailed risk breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Risk Score Breakdown")
        
        risk_components = [
            ("Driver Risk", decision.risk_score.driver_risk),
            ("Vehicle Risk", decision.risk_score.vehicle_risk),
            ("History Risk", decision.risk_score.history_risk),
            ("Credit Risk", decision.risk_score.credit_risk)
        ]
        
        for component, score in risk_components:
            # Color-code the risk level
            if score >= 80:
                color = "🟢"
            elif score >= 60:
                color = "🟡"
            else:
                color = "🔴"
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; 
                        background: #f8f9fa; margin: 0.25rem 0; border-radius: 5px;">
                <span>{color} {component}</span>
                <strong>{score}</strong>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📋 Decision Details")
        
        st.markdown(f"**Reason:** {reason}")
        
        if triggered_rules:
            st.markdown("**Triggered Rules:**")
            for rule in triggered_rules:
                st.markdown(f"• {rule}")
        
        if additional_notes:
            st.markdown(f"**Additional Notes:** {additional_notes}")
    
    # AI Decision comparison (if available)
    if result.get("ai_decision") and result["evaluation_mode"] == "AI-Enhanced (Recommended)":
        st.markdown("### 🤖 AI vs Rules Comparison")
        
        ai_decision = result["ai_decision"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🤖 AI Decision**")
            ai_color = {
                "ACCEPT": "🟢",
                "DENY": "🔴", 
                "ADJUDICATE": "🟡"
            }.get(ai_decision.decision.value, "O")
            
            st.markdown(f"{ai_color} {ai_decision.decision.value}")
            st.markdown(f"Confidence: {ai_decision.confidence_level.value.title()}")
            st.markdown(f"Reasoning: {ai_decision.reasoning[:100]}...")
        
        with col2:
            st.markdown("**📏 Rules Decision**")
            rules_color = {
                "ACCEPT": "🟢",
                "DENY": "🔴",
                "ADJUDICATE": "🟡" 
            }.get(decision_value, "O")
            
            st.markdown(f"{rules_color} {decision_value}")
            st.markdown(f"Risk Score: {risk_score}")
            st.markdown(f"Reason: {reason[:100]}...")
    
    # Export results
    st.markdown("### 💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download JSON"):
            result_json = {
                "application_id": str(st.session_state.current_application.id),
                "timestamp": result["timestamp"].isoformat(),
                "evaluation_mode": result["evaluation_mode"],
                "rule_set": result["rule_set"],
                "decision": {
                    "decision": decision_value,
                    "risk_score": risk_score,
                    "reason": reason,
                    "triggered_rules": triggered_rules,
                    "additional_notes": additional_notes
                },
                "processing_time": result["processing_time"]
            }
            
            st.download_button(
                "Download Results",
                data=json.dumps(result_json, indent=2),
                file_name=f"evaluation_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 View Analytics"):
            st.info("📈 Analytics integration coming soon!")
    
    with col3:
        if st.button("🧪 Create A/B Test"):
            st.info("🔬 A/B test creation coming soon!")

def clear_form_data():
    """Clear all form session state data."""
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("eval_")]
    for key in keys_to_clear:
        del st.session_state[key]
    
    st.session_state.evaluation_result = None
    st.session_state.current_application = None

def load_sample_data():
    """Load sample application data into the form."""
    # Sample driver data
    st.session_state.eval_driver_first_name = "John"
    st.session_state.eval_driver_last_name = "Smith"
    st.session_state.eval_driver_age = 35
    st.session_state.eval_driver_gender = "male"
    st.session_state.eval_driver_marital_status = "married"
    st.session_state.eval_driver_license_number = "DL12345678"
    st.session_state.eval_driver_license_state = "CA"
    st.session_state.eval_driver_license_status = "valid"
    st.session_state.eval_driver_years_licensed = 15
    
    # Sample vehicle data
    st.session_state.eval_vehicle_year = 2020
    st.session_state.eval_vehicle_make = "Toyota"
    st.session_state.eval_vehicle_model = "Camry"
    st.session_state.eval_vehicle_vin = "1HGBH41JXMN109186"
    st.session_state.eval_vehicle_category = "sedan"
    st.session_state.eval_vehicle_value = 25000
    st.session_state.eval_vehicle_usage = "personal"
    st.session_state.eval_vehicle_annual_mileage = 12000
    st.session_state.eval_vehicle_anti_theft = True
    st.session_state.eval_vehicle_safety_rating = 5
    
    # Sample metadata
    st.session_state.eval_metadata_credit_score = 750
    st.session_state.eval_metadata_previous_insurance = True
    st.session_state.eval_metadata_coverage_lapse = False
    st.session_state.eval_metadata_payment_method = "monthly"
    st.session_state.eval_metadata_coverage = "full_coverage"
    st.session_state.eval_metadata_agent_id = "AGT-001"
    
    # No violations or claims for clean sample
    st.session_state.eval_violations_count = 0
    st.session_state.eval_claims_count = 0

def save_application_json(application: Application):
    """Save application data as JSON."""
    try:
        app_data = {
            "id": str(application.id),
            "timestamp": datetime.now().isoformat(),
            "applicant": {
                "first_name": application.applicant.first_name,
                "last_name": application.applicant.last_name,
                "age": application.applicant.age,
                "gender": application.applicant.gender.value,
                "marital_status": application.applicant.marital_status.value,
                "license_number": application.applicant.license_number,
                "license_state": application.applicant.license_state,
                "years_licensed": application.applicant.years_licensed
            },
            "vehicle": {
                "year": application.vehicle.year,
                "make": application.vehicle.make,
                "model": application.vehicle.model,
                "vin": application.vehicle.vin,
                "category": application.vehicle.category.value,
                "value": float(application.vehicle.value)
            },
            "credit_score": application.credit_score,
            "previous_insurance": application.previous_insurance,
            "coverage_lapse": application.coverage_lapse,
            "metadata": application.metadata
        }
        
        st.download_button(
            "💾 Download Application Data",
            data=json.dumps(app_data, indent=2),
            file_name=f"application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"Error saving application: {str(e)}")