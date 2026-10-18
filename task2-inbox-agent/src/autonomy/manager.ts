import fs from "fs";
import path from "path";
import os from "os";
import { DraftResult, EmailRecord } from "../email/types";

export interface SubcategoryAutonomyState {
  subcategory: string;
  consecutiveUnchanged: number;
  eligible: boolean;
  enabledByHuman: boolean;
  totalApproved: number;
  totalEdited: number;
  totalRejected: number;
  lastDisabledReason?: string;
  updatedAt: string;
}

const isServerless = !!(process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME);
const AUTONOMY_DIR = isServerless ? path.join(os.tmpdir(), "data") : path.resolve(process.cwd(), "data");
const AUTONOMY_PATH = path.join(AUTONOMY_DIR, "autonomy_state.json");

let memoryStates: Record<string, SubcategoryAutonomyState> = {};

function loadStates(): Record<string, SubcategoryAutonomyState> {
  try {
    if (!fs.existsSync(AUTONOMY_DIR)) fs.mkdirSync(AUTONOMY_DIR, { recursive: true });
    if (!fs.existsSync(AUTONOMY_PATH)) {
      fs.writeFileSync(AUTONOMY_PATH, JSON.stringify({}, null, 2), "utf-8");
      return memoryStates;
    }
    const diskStates = JSON.parse(fs.readFileSync(AUTONOMY_PATH, "utf-8"));
    return { ...memoryStates, ...diskStates };
  } catch {
    return memoryStates;
  }
}

function saveStates(states: Record<string, SubcategoryAutonomyState>): void {
  memoryStates = { ...states };
  try {
    if (!fs.existsSync(AUTONOMY_DIR)) fs.mkdirSync(AUTONOMY_DIR, { recursive: true });
    fs.writeFileSync(AUTONOMY_PATH, JSON.stringify(states, null, 2), "utf-8");
  } catch {
    // In-memory fallback
  }
}

export class AutonomyManager {
  private threshold = 20;

  getState(subcategory: string): SubcategoryAutonomyState {
    const states = loadStates();
    if (!states[subcategory]) {
      states[subcategory] = {
        subcategory,
        consecutiveUnchanged: 0,
        eligible: false,
        enabledByHuman: false,
        totalApproved: 0,
        totalEdited: 0,
        totalRejected: 0,
        updatedAt: new Date().toISOString(),
      };
      saveStates(states);
    }
    return states[subcategory];
  }

  getAllStates(): SubcategoryAutonomyState[] {
    const states = loadStates();
    return Object.values(states);
  }

  recordOutcome(
    subcategory: string,
    action: "approve_send" | "edit_send" | "reject_write_own" | "escalate_expert",
    isUnchanged: boolean
  ): SubcategoryAutonomyState {
    const states = loadStates();
    const current = this.getState(subcategory);

    if (action === "approve_send" && isUnchanged) {
      current.consecutiveUnchanged += 1;
      current.totalApproved += 1;
      if (current.consecutiveUnchanged >= this.threshold) {
        current.eligible = true;
      }
    } else {
      current.consecutiveUnchanged = 0;
      if (action === "edit_send") current.totalEdited += 1;
      if (action === "reject_write_own") current.totalRejected += 1;

      const recentTotal = current.totalApproved + current.totalEdited + current.totalRejected;
      const editRate = recentTotal > 0 ? (current.totalEdited + current.totalRejected) / recentTotal : 0;

      if (editRate > 0.25 && current.enabledByHuman) {
        current.enabledByHuman = false;
        current.lastDisabledReason = `Rolling edit/rejection rate exceeded 25% (${Math.round(editRate * 100)}%). Autonomy disabled for safety.`;
        console.warn(`[Autonomy] Breached threshold for ${subcategory}. Auto-disabled.`);
      }
    }

    current.updatedAt = new Date().toISOString();
    states[subcategory] = current;
    saveStates(states);
    return current;
  }

  toggleHumanAutonomy(subcategory: string, enable: boolean): { success: boolean; message: string } {
    const states = loadStates();
    const current = this.getState(subcategory);

    if (enable && !current.eligible) {
      return {
        success: false,
        message: `Cannot enable autonomy: Subcategory '${subcategory}' has not reached 20 consecutive unchanged drafts. Current: ${current.consecutiveUnchanged}/20.`,
      };
    }

    current.enabledByHuman = enable;
    if (enable) current.lastDisabledReason = undefined;
    current.updatedAt = new Date().toISOString();
    states[subcategory] = current;
    saveStates(states);

    return {
      success: true,
      message: `Autonomy ${enable ? "ENABLED" : "DISABLED"} for ${subcategory}.`,
    };
  }

  canAutoSend(
    email: EmailRecord,
    draft: DraftResult,
    validatorPassed: boolean
  ): { canSend: boolean; reason: string } {
    const state = this.getState(email.subcategory);

    if (!state.enabledByHuman) {
      return { canSend: false, reason: "Autonomy is not enabled by human operator for this subcategory." };
    }

    if (draft.risk !== "low") {
      return { canSend: false, reason: `Risk level is '${draft.risk}' (must be 'low').` };
    }

    const forbiddenCategories = ["refund_cancellation", "complaint", "quote", "project_request"];
    if (forbiddenCategories.includes(draft.category)) {
      return { canSend: false, reason: `Category '${draft.category}' is forbidden from autonomous sending.` };
    }

    if (!validatorPassed) {
      return { canSend: false, reason: "Safety validator reported rule violations." };
    }

    if (!draft.sources || draft.sources.length === 0) {
      return { canSend: false, reason: "No verified knowledge sources present in draft." };
    }

    return { canSend: true, reason: "All safety and autonomy gates verified." };
  }
}

export const autonomyManager = new AutonomyManager();
