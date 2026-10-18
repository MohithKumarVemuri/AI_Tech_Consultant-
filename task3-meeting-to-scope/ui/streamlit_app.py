import streamlit as st
import json
import os
import asyncio
from pathlib import Path
import sys

# Ensure task3 root is on path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.analyst import analyst_agent
from agents.feasibility import feasibility_agent
from agents.scope import scope_agent
from agents.estimator import estimator_agent
from agents.proposal import proposal_agent
from scope_diff.diff_engine import diff_engine
from scope_diff.approval import approval_manager
from app.schemas import Proposal

st.set_page_config(
    page_title="Meeting -> Scope (T3)",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Task 3: Meeting Transcripts → Scope, Estimate & Proposal")
st.caption("5 Autonomous Agents, T1 Feasibility Verification over HTTP, Baseline Diff Engine & Approval Gate")

# Global Session State
if "baseline_proposal" not in st.session_state:
    st.session_state.baseline_proposal = None
if "current_proposal" not in st.session_state:
    st.session_state.current_proposal = None
if "diff_report" not in st.session_state:
    st.session_state.diff_report = None

# Sidebar Transcript Selector
st.sidebar.header("📁 Meeting Transcripts")
transcript_option = st.sidebar.selectbox(
    "Select Transcript File:",
    [
        "Transcript A: Search, Filters & Mobile (PRJ-ALPHA)",
        "Transcript B: E-Commerce & Subscriptions (PRJ-BETA)",
        "Transcript C: Follow-up to A (PRJ-ALPHA Diff)"
    ]
)

transcripts_dir = BASE_DIR / "transcripts"
if "Transcript A" in transcript_option:
    selected_file = transcripts_dir / "transcript_A.json"
elif "Transcript B" in transcript_option:
    selected_file = transcripts_dir / "transcript_B.json"
else:
    selected_file = transcripts_dir / "transcript_C.json"

transcript_data = json.loads(selected_file.read_text(encoding="utf-8"))

st.sidebar.markdown(f"**Project:** {transcript_data.get('project_id')}")
st.sidebar.markdown(f"**Client:** {transcript_data.get('client_name')}")
st.sidebar.markdown(f"**Date:** {transcript_data.get('meeting_date')}")

# Execution Button
if st.sidebar.button("Run 5-Agent Analysis Pipeline", type="primary"):
    with st.spinner("Executing Analyst, Feasibility (T1 HTTP), Scope, Estimator & Proposal Agents..."):
        # 1. Analyst Agent
        raw_reqs = analyst_agent.analyze_transcript(transcript_data)
        
        # 2. Feasibility Agent (Queries T1 over HTTP)
        loop = asyncio.new_event_loop()
        evaluated_reqs = loop.run_until_complete(feasibility_agent.evaluate_requirements(raw_reqs))
        loop.close()

        # 3. Scope Agent
        scope_doc = scope_agent.generate_scope(
            project_id=transcript_data.get("project_id", "PRJ-001"),
            project_name=transcript_data.get("project_name", "Web Directory"),
            requirements=evaluated_reqs
        )

        # 4. Estimation Agent
        tasks, low_h, likely_h, high_h = estimator_agent.estimate_requirements(evaluated_reqs)

        # 5. Proposal Agent
        prop = proposal_agent.generate_proposal(
            project_id=transcript_data.get("project_id", "PRJ-001"),
            project_name=transcript_data.get("project_name", "Web Directory"),
            client_name=transcript_data.get("client_name", "Valued Client"),
            scope=scope_doc,
            tasks=tasks,
            total_low=low_h,
            total_likely=likely_h,
            total_high=high_h,
            version=1 if "Transcript A" in transcript_option else 2
        )

        st.session_state.current_proposal = prop

        # If analyzing Transcript C and baseline exists, calculate diff!
        if "Transcript C" in transcript_option and st.session_state.baseline_proposal:
            report, _, _ = diff_engine.compute_diff(
                approved_baseline=st.session_state.baseline_proposal,
                followup_requirements=evaluated_reqs,
                followup_version=2
            )
            st.session_state.diff_report = report
        else:
            st.session_state.diff_report = None

tab_overview, tab_reqs, tab_estimate, tab_diff, tab_approval = st.tabs([
    "🎙️ Dialogue & Overview",
    "📝 Requirements & Feasibility",
    "⏱️ 3-Point Estimate",
    "🔍 Follow-up Diff Report",
    "🛡️ Human Approval & Proposal"
])

with tab_overview:
    st.subheader(f"Meeting Transcript: {transcript_data.get('project_name')}")
    st.write(f"**Client:** {transcript_data.get('client_name')} | **Consultant:** {transcript_data.get('consultant_name')}")
    
    with st.expander("Show Raw Audio Transcript Dialogue", expanded=True):
        for d in transcript_data.get("dialogue", []):
            st.markdown(f"**`[{d.get('timestamp')}]` {d.get('speaker')}:** {d.get('text')}")

with tab_reqs:
    st.subheader("Extracted Technical Requirements & Feasibility Analysis")
    if st.session_state.current_proposal:
        reqs = st.session_state.current_proposal.scope.agreed_requirements
        for r in reqs:
            with st.container(border=True):
                colA, colB = st.columns([3, 1])
                with colA:
                    st.markdown(f"**{r.id}: {r.description}**")
                    st.caption(f"Source Quote: \"{r.source_quote}\" (Timestamp: `{r.timestamp}`)")
                    st.write(f"**Feasibility Rationale:** {r.existing_solution}")
                with colB:
                    status_color = "green" if r.feasibility_status == "existing_config" else "blue"
                    st.markdown(f"**Feasibility:** :{status_color}[{r.feasibility_status.upper()}]")
                    st.write(f"**Priority:** `{r.priority}`")
                    st.write(f"**Origin:** `{r.origin}`")
    else:
        st.info("Run the 5-Agent pipeline from the sidebar to extract requirements.")

with tab_estimate:
    st.subheader("Engineering Task Breakdown & 3-Point Estimation")
    if st.session_state.current_proposal:
        prop = st.session_state.current_proposal
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Low Hours Total", f"{prop.total_low_hours} hrs")
        c2.metric("Likely Hours Total", f"{prop.total_likely_hours} hrs")
        c3.metric("High Hours Total", f"{prop.total_high_hours} hrs")
        c4.metric("Likely Cost (at $125/hr)", f"${prop.total_likely_cost:,.2f}")

        st.markdown("#### Task Breakdown Table")
        task_table = [
            {
                "Task ID": t.task_id,
                "Requirement": t.requirement_id,
                "Task Title": t.title,
                "Low": f"{t.low_hours}h",
                "Likely": f"{t.likely_hours}h",
                "High": f"{t.high_hours}h",
                "Assumptions": ", ".join(t.assumptions)
            }
            for t in prop.tasks
        ]
        st.dataframe(task_table, use_container_width=True)
    else:
        st.info("No active estimate.")

with tab_diff:
    st.subheader("Follow-up Scope Change Report vs. Approved Baseline")
    if st.session_state.diff_report:
        report = st.session_state.diff_report
        st.success(f"Comparing Follow-up Meeting adjustments against Approved Baseline v{report.baseline_version}")
        
        m1, m2 = st.columns(2)
        m1.metric("Net Engineering Hours Delta", f"{report.net_hours_diff:+.1f} hrs")
        m2.metric("Net Cost Adjustment", f"${report.net_cost_diff:+,.2f}")

        # Out-of-Scope flags
        if report.out_of_scope:
            st.error("🚨 Out-of-Scope Client Requests Identified:")
            for item in report.out_of_scope:
                st.markdown(f"- **{item.description}**\n  _{item.detail}_")

        if report.added:
            st.markdown("#### ➕ Newly Added Requirements:")
            for a in report.added:
                st.markdown(f"- **{a.description}** (+{a.hours_impact} hrs)\n  _{a.detail}_")

        if report.removed:
            st.markdown("#### ➖ Removed / Dropped Requirements:")
            for rem in report.removed:
                st.markdown(f"- **{rem.description}** ({rem.hours_impact} hrs)\n  _{rem.detail}_")

        if report.modified:
            st.markdown("#### 🔄 Modified Requirements:")
            for m in report.modified:
                st.markdown(f"- **{m.description}**\n  _{m.detail}_")

    else:
        if not st.session_state.baseline_proposal:
            st.warning("⚠️ No approved baseline proposal exists yet. Please load Transcript A, run analysis, and approve it in the Human Approval tab to establish the baseline.")
        else:
            st.info("Load Transcript C and click 'Run 5-Agent Analysis Pipeline' to generate the diff change report against Baseline v1.")

with tab_approval:
    st.subheader("Human Approval Gate & Proposal Dispatch")
    if st.session_state.current_proposal:
        prop = st.session_state.current_proposal
        
        status_colors = {
            "draft": "gray",
            "in_review": "orange",
            "approved": "green",
            "sent": "blue"
        }
        st.markdown(f"**Proposal ID:** `{prop.proposal_id}` | **Status:** :{status_colors[prop.approval_status]}[{prop.approval_status.upper()}]")
        
        if prop.reviewer:
            st.caption(f"Reviewed & Approved by: **{prop.reviewer}** at `{prop.approved_at}`")

        colX, colY, colZ = st.columns(3)
        with colX:
            reviewer_name = st.text_input("Reviewer Full Name:", value="Tech Lead Sarah")
        with colY:
            if st.button("Approve Proposal (Set Baseline)", type="primary"):
                try:
                    updated = approval_manager.advance_status(prop, "approved", reviewer_name)
                    st.session_state.current_proposal = updated
                    # Save as baseline if Transcript A
                    if "Transcript A" in transcript_option:
                        st.session_state.baseline_proposal = updated
                        st.success(f"Proposal {updated.proposal_id} APPROVED and registered as baseline v{updated.version}!")
                    else:
                        st.success(f"Follow-up Proposal {updated.proposal_id} APPROVED!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with colZ:
            if st.button("Simulate Dispatch to Client"):
                try:
                    updated = approval_manager.advance_status(prop, "sent", reviewer_name)
                    st.session_state.current_proposal = updated
                    st.success(f"Proposal {prop.proposal_id} dispatched to client {prop.client_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"BLOCKED: {e}")

        st.markdown("---")
        st.markdown("### Client-Ready Proposal Preview")
        st.markdown(f"#### {prop.project_name} — Implementation Scope")
        st.markdown(prop.executive_summary)
        st.markdown(f"**Estimated Investment:** ${prop.total_likely_cost:,.2f} ({prop.total_likely_hours} likely engineering hours at ${prop.hourly_rate}/hr {prop.currency})")
        st.markdown(f"**Payment Terms:** {prop.payment_terms}")
        st.markdown(f"**Target Timeline:** {prop.timeline}")

        with st.expander("View Included Scope Deliverables", expanded=True):
            for d in prop.scope.deliverables:
                st.markdown(f"- {d}")

        with st.expander("View Explicit Contract Exclusions"):
            for exc in prop.scope.exclusions:
                st.markdown(f"- ⚠️ {exc}")

    else:
        st.info("No proposal generated yet.")
