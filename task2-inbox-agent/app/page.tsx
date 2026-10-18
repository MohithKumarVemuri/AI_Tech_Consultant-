"use client";

import React, { useState, useEffect } from "react";
import {
  Inbox,
  Send,
  Edit3,
  XCircle,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Sliders,
  ExternalLink,
  ChevronRight,
  BookOpen,
} from "lucide-react";
import { EmailRecord, Category, CATEGORIES } from "@/email/types";

export default function InboxDashboard() {
  const [emails, setEmails] = useState<EmailRecord[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailRecord | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [currentDraft, setCurrentDraft] = useState<any>(null);
  const [editableReply, setEditableReply] = useState<string>("");
  const [editReason, setEditReason] = useState<string>("");
  const [autonomyStates, setAutonomyStates] = useState<any[]>([]);
  const [notification, setNotification] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"inbox" | "autonomy" | "prompts">("inbox");
  const [proposals, setProposals] = useState<any[]>([]);

  // Fetch emails
  useEffect(() => {
    fetch("/api/emails")
      .then((r) => r.json())
      .then((data) => {
        setEmails(data);
        if (data.length > 0) {
          handleSelectEmail(data[0]);
        }
      })
      .catch((err) => console.error(err));

    fetchAutonomy();
    fetchPrompts();
  }, []);

  const fetchAutonomy = () => {
    fetch("/api/autonomy")
      .then((r) => r.json())
      .then((data) => setAutonomyStates(data))
      .catch((e) => console.error(e));
  };

  const fetchPrompts = () => {
    fetch("/api/prompts")
      .then((r) => r.json())
      .then((data) => setProposals(data))
      .catch((e) => console.error(e));
  };

  const handleSelectEmail = async (email: EmailRecord) => {
    setSelectedEmail(email);
    setLoadingDraft(true);
    setCurrentDraft(null);
    setEditReason("");

    try {
      const res = await fetch("/api/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(email),
      });
      const data = await res.json();
      setCurrentDraft(data);
      setEditableReply(data.draft.reply);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDraft(false);
    }
  };

  const handleReviewAction = async (action: string) => {
    if (!selectedEmail || !currentDraft) return;

    if (action === "edit_send" && !editReason.trim()) {
      alert("Please provide a brief reason for editing the draft to train the feedback loop.");
      return;
    }

    try {
      const res = await fetch("/api/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          emailId: selectedEmail.id,
          category: currentDraft.draft.category,
          subcategory: selectedEmail.subcategory,
          originalDraft: currentDraft.draft.reply,
          finalReply: editableReply,
          action,
          editReason: action === "edit_send" ? editReason : undefined,
        }),
      });
      const result = await res.json();
      setNotification(`Action '${action}' saved. Similarity: ${result.diff.similarity} (Unchanged: ${result.diff.isUnchanged}). Simulated email sent!`);
      fetchAutonomy();

      setTimeout(() => setNotification(null), 6000);
    } catch (err: any) {
      alert("Error submitting review: " + err.message);
    }
  };

  const handleToggleAutonomy = async (subcategory: string, currentVal: boolean) => {
    const res = await fetch("/api/autonomy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subcategory, enable: !currentVal }),
    });
    const data = await res.json();
    alert(data.message);
    fetchAutonomy();
  };

  const handleRunOptimizer = async () => {
    const res = await fetch("/api/prompts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "run_optimization" }),
    });
    const data = await res.json();
    setProposals(data.proposals);
    alert(`Nightly optimizer completed! Generated ${data.proposals?.length || 0} prompt adjustment proposals.`);
  };

  const filteredEmails = emails.filter((em) => {
    if (selectedCategory === "all") return true;
    return em.expected_category === selectedCategory;
  });

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#F8FBFC]">
      {/* Top Header */}
      <header className="h-16 border-b border-[#E3E9E7] bg-white/80 backdrop-blur-md px-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald text-white flex items-center justify-center font-bold shadow-sm">
            T2
          </div>
          <div>
            <h1 className="text-base font-bold text-[#0B1F1B] leading-tight">
              Decisium — Inbox Triaging & Human Review Agent
            </h1>
            <p className="text-xs text-[#4B5A57]">
              Powered by Claude Haiku, Knowledge Brain (T1 HTTP), and Earned Autonomy
            </p>
          </div>
        </div>

        {/* Top Navigation Tabs */}
        <div className="flex items-center gap-2 bg-[#E1F5EE]/50 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab("inbox")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "inbox" ? "bg-white text-emerald-deep shadow-sm" : "text-[#4B5A57] hover:text-[#0B1F1B]"
            }`}
          >
            📬 Triaged Inbox ({emails.length})
          </button>
          <button
            onClick={() => setActiveTab("autonomy")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "autonomy" ? "bg-white text-emerald-deep shadow-sm" : "text-[#4B5A57] hover:text-[#0B1F1B]"
            }`}
          >
            🛡️ Autonomy Monitor
          </button>
          <button
            onClick={() => setActiveTab("prompts")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "prompts" ? "bg-white text-emerald-deep shadow-sm" : "text-[#4B5A57] hover:text-[#0B1F1B]"
            }`}
          >
            🧬 Prompt Learning Lab
          </button>
        </div>
      </header>

      {/* Notification Toast */}
      {notification && (
        <div className="bg-emerald-soft border-b border-emerald text-emerald-deep px-6 py-2.5 text-xs font-medium flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald font-bold">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {activeTab === "inbox" && (
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column: Email List */}
          <div className="w-[380px] border-r border-[#E3E9E7] flex flex-col bg-white">
            {/* Category Filter Pills */}
            <div className="p-3 border-b border-[#E3E9E7] flex gap-1.5 overflow-x-auto text-xs no-scrollbar">
              <button
                onClick={() => setSelectedCategory("all")}
                className={`px-2.5 py-1 rounded-full whitespace-nowrap transition ${
                  selectedCategory === "all" ? "bg-emerald text-white font-medium" : "bg-slate-100 text-[#4B5A57]"
                }`}
              >
                All ({emails.length})
              </button>
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-full whitespace-nowrap capitalize transition ${
                    selectedCategory === cat ? "bg-emerald text-white font-medium" : "bg-slate-100 text-[#4B5A57]"
                  }`}
                >
                  {cat.replace("_", " ")}
                </button>
              ))}
            </div>

            {/* Email List Items */}
            <div className="flex-1 overflow-y-auto divide-y divide-[#E3E9E7]">
              {filteredEmails.map((em) => {
                const isSelected = selectedEmail?.id === em.id;
                return (
                  <div
                    key={em.id}
                    onClick={() => handleSelectEmail(em)}
                    className={`p-3.5 cursor-pointer transition ${
                      isSelected ? "bg-[#E1F5EE]/40 border-l-4 border-emerald" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-[#0B1F1B] truncate max-w-[200px]">{em.sender}</span>
                      <span className="text-[10px] text-[#4B5A57]">
                        {new Date(em.received_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-[#0B1F1B] mb-1 line-clamp-1">{em.subject || "(No Subject)"}</div>
                    <div className="text-[11px] text-[#4B5A57] line-clamp-2 mb-2">{em.body || "(Empty Body)"}</div>
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-soft text-emerald-deep capitalize">
                        {em.expected_category.replace("_", " ")}
                      </span>
                      {em.risk === "high" && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-red-100 text-red-700 flex items-center gap-0.5">
                          <ShieldAlert className="w-3 h-3" /> High Risk
                        </span>
                      )}
                      {em.is_test_holdout && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-800">
                          Holdout
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Pane: Split Review Workspace */}
          <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
            {selectedEmail ? (
              <>
                {/* 1. Original Customer Email Card */}
                <div className="glass-card p-5 bg-white">
                  <div className="flex items-start justify-between border-b border-[#E3E9E7] pb-3 mb-3">
                    <div>
                      <h2 className="text-base font-bold text-[#0B1F1B]">{selectedEmail.subject || "(No Subject)"}</h2>
                      <p className="text-xs text-[#4B5A57]">
                        From: <span className="font-medium text-[#0B1F1B]">{selectedEmail.sender}</span> • Received:{" "}
                        {new Date(selectedEmail.received_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2.5 py-1 rounded-full font-semibold bg-slate-100 text-[#0B1F1B]">
                        Subcategory: {selectedEmail.subcategory}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-[#0B1F1B] whitespace-pre-wrap leading-relaxed">
                    {selectedEmail.body || "(Empty message content)"}
                  </p>
                </div>

                {/* 2. AI Triaging & Grounded Retrieval Status */}
                {loadingDraft ? (
                  <div className="p-8 text-center text-xs text-[#4B5A57] flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-emerald" />
                    Consulting Knowledge Brain (T1 HTTP) & generating grounded draft...
                  </div>
                ) : currentDraft ? (
                  <>
                    <div className="grid grid-cols-3 gap-4">
                      {/* Classification Badge */}
                      <div className="glass-card p-3.5 bg-white">
                        <div className="text-[11px] font-semibold text-[#4B5A57] mb-1">CLASSIFICATION</div>
                        <div className="text-sm font-bold text-emerald-deep capitalize">
                          {currentDraft.classification?.category.replace("_", " ")}
                        </div>
                        <div className="text-[11px] text-[#4B5A57] mt-1">
                          Urgency: <span className="font-semibold">{currentDraft.classification?.urgency}</span> • Risk:{" "}
                          <span className="font-semibold">{currentDraft.classification?.risk}</span>
                        </div>
                      </div>

                      {/* Knowledge Brain State */}
                      <div className="glass-card p-3.5 bg-white">
                        <div className="text-[11px] font-semibold text-[#4B5A57] mb-1">KNOWLEDGE BRAIN (T1)</div>
                        <div className="text-sm font-bold text-emerald-deep capitalize flex items-center gap-1.5">
                          <BookOpen className="w-4 h-4 text-emerald" />
                          {currentDraft.draft?.knowledge_state}
                        </div>
                        <div className="text-[11px] text-[#4B5A57] mt-1 truncate">
                          Sources: {currentDraft.draft?.sources?.length || 0} cited articles
                        </div>
                      </div>

                      {/* Human Safety Gate */}
                      <div className="glass-card p-3.5 bg-white">
                        <div className="text-[11px] font-semibold text-[#4B5A57] mb-1">APPROVAL REQUIREMENT</div>
                        <div className="text-sm font-bold flex items-center gap-1.5 text-amber-700">
                          <AlertTriangle className="w-4 h-4" />
                          {currentDraft.draft?.needs_human ? "Human Review Mandatory" : "Autonomy Eligible"}
                        </div>
                        <div className="text-[11px] text-[#4B5A57] mt-1">
                          Model: {currentDraft.draft?.prompt_version}
                        </div>
                      </div>
                    </div>

                    {/* Safety Violations Alert if blocked by validator */}
                    {currentDraft.validation?.violations?.length > 0 && (
                      <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800">
                        <div className="font-bold flex items-center gap-1.5 mb-1">
                          <ShieldAlert className="w-4 h-4 text-red-600" />
                          Safety Policy Guardrails Triggered:
                        </div>
                        <ul className="list-disc pl-5 space-y-0.5">
                          {currentDraft.validation.violations.map((v: string, idx: number) => (
                            <li key={idx}>{v}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* 3. Draft Reply & Live Edit Diff Workspace */}
                    <div className="glass-card p-5 bg-white space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-[#0B1F1B]">AI Drafted Response</h3>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-soft text-emerald-deep font-semibold">
                            Grounded in BD Help Center
                          </span>
                        </div>
                        <div className="text-xs text-[#4B5A57]">
                          Words: {editableReply.split(/\s+/).filter(Boolean).length}
                        </div>
                      </div>

                      <textarea
                        value={editableReply}
                        onChange={(e) => setEditableReply(e.target.value)}
                        rows={8}
                        className="w-full text-xs p-3.5 border border-[#E3E9E7] rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald/20 font-mono leading-relaxed"
                      />

                      {/* Edit Reason Input (if edited) */}
                      {editableReply !== currentDraft.draft.reply && (
                        <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-200 space-y-2">
                          <div className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
                            <Edit3 className="w-3.5 h-3.5" />
                            Why did you edit this response? (Improves prompt learning nightly):
                          </div>
                          <input
                            type="text"
                            value={editReason}
                            onChange={(e) => setEditReason(e.target.value)}
                            placeholder="e.g. Added explicit navigation path to Finance > Membership Plans tab"
                            className="w-full text-xs p-2 rounded-lg border border-amber-300 bg-white"
                          />
                        </div>
                      )}

                      {/* Human Action Buttons */}
                      <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleReviewAction("approve_send")}
                            className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5"
                          >
                            <Send className="w-3.5 h-3.5" />
                            Approve & Send
                          </button>

                          <button
                            onClick={() => handleReviewAction("edit_send")}
                            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-[#0B1F1B] flex items-center gap-1.5 transition"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                            Edit & Send
                          </button>

                          <button
                            onClick={() => handleReviewAction("reject_write_own")}
                            className="px-4 py-2 rounded-xl text-xs font-semibold bg-red-50 hover:bg-red-100 text-red-700 flex items-center gap-1.5 transition"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            Reject & Write Own
                          </button>
                        </div>

                        <button
                          onClick={() => handleReviewAction("escalate_expert")}
                          className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-amber-50 text-amber-800 hover:bg-amber-100 flex items-center gap-1.5 transition"
                        >
                          Mark for Expert Help
                        </button>
                      </div>
                    </div>
                  </>
                ) : null}
              </>
            ) : (
              <div className="p-12 text-center text-xs text-[#4B5A57]">
                Select an email from the left pane to begin triaging and drafting.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Autonomy Monitor View */}
      {activeTab === "autonomy" && (
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="glass-card p-5 bg-white">
            <h2 className="text-base font-bold text-[#0B1F1B] mb-1">Earned Autonomy Dashboard</h2>
            <p className="text-xs text-[#4B5A57] mb-4">
              Spec Rule: Subcategories require <strong>20 consecutive unchanged sent drafts</strong> before becoming
              autonomy-eligible. Even when eligible, auto-sending strictly requires low risk, verified sources, and
              human enablement.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-[#E3E9E7] rounded-xl overflow-hidden">
                <thead className="bg-[#E1F5EE]/40 text-[#0B1F1B] font-semibold border-b border-[#E3E9E7]">
                  <tr>
                    <th className="p-3">Subcategory</th>
                    <th className="p-3">Consecutive Unchanged</th>
                    <th className="p-3">Eligibility (≥20)</th>
                    <th className="p-3">Approved / Edited / Rejected</th>
                    <th className="p-3">Human Autonomy Status</th>
                    <th className="p-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E3E9E7]">
                  {autonomyStates.map((st) => (
                    <tr key={st.subcategory} className="hover:bg-slate-50">
                      <td className="p-3 font-semibold text-[#0B1F1B]">{st.subcategory}</td>
                      <td className="p-3">
                        <span className="font-bold text-emerald">{st.consecutiveUnchanged}</span> / 20
                      </td>
                      <td className="p-3">
                        {st.eligible ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald text-white">
                            ELIGIBLE
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-[#4B5A57]">
                            In Training
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-[#4B5A57]">
                        {st.totalApproved} / {st.totalEdited} / {st.totalRejected}
                      </td>
                      <td className="p-3">
                        {st.enabledByHuman ? (
                          <span className="text-emerald font-bold">Auto-Send Active</span>
                        ) : (
                          <span className="text-[#4B5A57]">Human Guarded</span>
                        )}
                      </td>
                      <td className="p-3">
                        <button
                          onClick={() => handleToggleAutonomy(st.subcategory, st.enabledByHuman)}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                            st.enabledByHuman
                              ? "bg-red-50 text-red-700 hover:bg-red-100"
                              : "bg-emerald text-white hover:bg-emerald-deep"
                          }`}
                        >
                          {st.enabledByHuman ? "Disable Auto-Send" : "Enable Auto-Send"}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {autonomyStates.length === 0 && (
                    <tr>
                      <td colSpan={6} className="p-6 text-center text-[#4B5A57]">
                        No subcategories have processed reviews yet. Start reviewing drafts in the inbox!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Prompts Learning Lab */}
      {activeTab === "prompts" && (
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="glass-card p-5 bg-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-[#0B1F1B]">Nightly Prompt Optimizer & Style Rules</h2>
                <p className="text-xs text-[#4B5A57]">
                  Clusters human edit reasons per subcategory to propose versioned prompt upgrades (e.g. drafting@v2).
                </p>
              </div>
              <button
                onClick={handleRunOptimizer}
                className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" /> Run Clustering Optimizer Now
              </button>
            </div>

            <div className="space-y-4">
              {proposals.map((prop, idx) => (
                <div key={idx} className="p-4 rounded-xl border border-[#E3E9E7] bg-slate-50 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-deep">{prop.version} — {prop.subcategory}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-amber-100 text-amber-800">
                      {prop.status}
                    </span>
                  </div>
                  <div className="text-xs text-[#0B1F1B]">
                    <strong>Proposed Prompt Adjustment:</strong> {prop.proposedRule}
                  </div>
                  <div className="text-[11px] text-[#4B5A57]">
                    Clustered human edit reasons: {prop.clusteredReasons?.join(" • ") || "None"}
                  </div>
                </div>
              ))}
              {proposals.length === 0 && (
                <div className="p-6 text-center text-xs text-[#4B5A57]">
                  No prompt proposals generated yet. Edit a couple of drafts and click "Run Clustering Optimizer Now"!
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
