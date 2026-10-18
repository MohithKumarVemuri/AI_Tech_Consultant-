import streamlit as st
import httpx
import os
import json

st.set_page_config(
    page_title="Decisium - Knowledge Brain (T1)",
    page_icon="🧠",
    layout="wide"
)

KB_BASE_URL = os.getenv("KB_BASE_URL", "http://localhost:8000/v1")
KB_API_KEY = os.getenv("KB_API_KEY", "kb_secret_dev_key_2026")

headers = {"X-API-Key": KB_API_KEY}

st.title("🧠 Task 1: Knowledge Brain")
st.caption("RAG Question-Answering, Real-time Ingestion & Human Expert Escalation Queue")

tab_chat, tab_escalations, tab_ingestion = st.tabs(["💬 Ask Knowledge Brain", "🚨 Expert Escalation Queue", "🔄 Ingestion & Freshness"])

with tab_chat:
    st.subheader("Query Brilliant Directories Knowledge Base")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        question_input = st.text_input(
            "Enter your technical or configuration question:",
            placeholder="e.g. How do I configure recurring membership billing?"
        )
    with col2:
        top_k = st.slider("Max Sources", min_value=1, max_value=10, value=5)

    if st.button("Search & Consult", type="primary"):
        if not question_input.strip():
            st.warning("Please type a question.")
        else:
            with st.spinner("Retrieving evidence and consulting knowledge model..."):
                try:
                    with httpx.Client(base_url=KB_BASE_URL, headers=headers, timeout=30.0) as client:
                        resp = client.post("/query", json={"question": question_input, "top_k": top_k})
                        if resp.status_code == 200:
                            data = resp.json()
                            status = data["status"]
                            
                            if status == "answered":
                                st.success("✅ Grounded Answer Generated")
                                st.markdown(f"### Answer\n{data['answer']}")
                                
                                st.markdown("---")
                                st.markdown("#### 📚 Verified Documentation Sources")
                                for idx, src in enumerate(data.get("sources", []), 1):
                                    with st.expander(f"Source {idx}: {src['title']} (Score: {src['score']})"):
                                        st.write(f"**URL:** [{src['url']}]({src['url']})")
                                        if src.get("heading"):
                                            st.write(f"**Section:** {src['heading']}")
                                        if src.get("image_refs"):
                                            st.write("**Referenced UI Screenshots:**")
                                            for img in src["image_refs"]:
                                                st.image(img, caption=src["title"], width=400)

                            elif status == "insufficient_evidence":
                                st.error("⚠️ Insufficient Evidence in Knowledge Base")
                                st.info(
                                    f"The knowledge base does not have verifiable documentation to guarantee an answer. "
                                    f"An expert escalation task was created automatically: **ID: {data['escalation_id']}**"
                                )
                                st.write("Human review is required before delivering an answer.")
                        else:
                            st.error(f"API Error ({resp.status_code}): {resp.text}")
                except Exception as e:
                    st.error(f"Failed to communicate with Knowledge Brain API at {KB_BASE_URL}: {e}")

with tab_escalations:
    st.subheader("Human Escalation & Expert Resolution Queue")
    st.caption("Review unanswered user queries and provide verified expert resolutions to enrich the knowledge base.")

    try:
        with httpx.Client(base_url=KB_BASE_URL, headers=headers, timeout=10.0) as client:
            resp = client.get("/escalations?status=open")
            if resp.status_code == 200:
                escalations = resp.json()
                if not escalations:
                    st.success("🎉 No pending open escalations! All queries are grounded.")
                else:
                    for esc in escalations:
                        with st.container(border=True):
                            st.markdown(f"**Question:** {esc['question']}")
                            st.caption(f"ID: `{esc['id']}` | Created: {esc['created_at']}")
                            
                            exp_ans = st.text_area(f"Expert Resolution for {esc['id']}", key=f"ans_{esc['id']}")
                            reviewer = st.text_input("Reviewer Name:", value="Tech Lead Sarah", key=f"rev_{esc['id']}")
                            
                            if st.button("Submit & Index Resolution", key=f"btn_{esc['id']}", type="primary"):
                                if not exp_ans.strip():
                                    st.warning("Please provide an expert answer.")
                                else:
                                    r_resp = client.post(f"/escalations/{esc['id']}/resolve", json={
                                        "expert_answer": exp_ans,
                                        "reviewer": reviewer
                                    })
                                    if r_resp.status_code == 200:
                                        st.success("Resolution saved! The expert answer is now indexed into the Knowledge Brain.")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to resolve: {r_resp.text}")
            else:
                st.error("Failed to load escalations.")
    except Exception as e:
        st.error(f"Cannot load escalations: {e}")

with tab_ingestion:
    st.subheader("Site Crawler & Knowledge Freshness")
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown("#### Run Ingestion Job")
        mode = st.selectbox("Ingestion Mode", ["incremental", "full", "sample"])
        pages_limit = st.number_input("Max Pages Limit", min_value=1, max_value=200, value=15)
        
        if st.button("Trigger Ingestion Job", type="primary"):
            try:
                with httpx.Client(base_url=KB_BASE_URL, headers=headers, timeout=10.0) as client:
                    resp = client.post("/ingestion/run", json={"mode": mode, "max_pages": pages_limit})
                    if resp.status_code == 200:
                        st.success(f"Ingestion job started! Mode: {mode}")
                    else:
                        st.error(f"Error starting job: {resp.text}")
            except Exception as e:
                st.error(f"Error: {e}")

    with colB:
        st.markdown("#### Live Ingestion Status & Counts")
        try:
            with httpx.Client(base_url=KB_BASE_URL, headers=headers, timeout=10.0) as client:
                resp = client.get("/ingestion/status")
                if resp.status_code == 200:
                    status_data = resp.json()
                    st.metric("Total Indexed Pages", status_data.get("total_pages", 0))
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Added", status_data.get("added", 0))
                    c2.metric("Updated", status_data.get("updated", 0))
                    c3.metric("Removed", status_data.get("removed", 0))
                    c4.metric("Failed", status_data.get("failed", 0))
                    st.write(f"**Last Sync At:** {status_data.get('last_run_at', 'Never')}")
                    st.write(f"**Crawler Running:** {'Yes' if status_data.get('is_running') else 'No'}")
        except Exception as e:
            st.info("Status unavailable (API server may be offline).")
