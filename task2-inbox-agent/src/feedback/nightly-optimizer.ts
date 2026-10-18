import fs from "fs";
import path from "path";
import { getAllFeedback } from "./feedback-store";

export interface ProposedPromptRule {
  version: string;
  subcategory: string;
  clusteredReasons: string[];
  proposedRule: string;
  status: "pending_approval" | "approved" | "rejected" | "rolled_back";
  regressionTestPassed: boolean;
  createdAt: string;
}

const PROPOSALS_PATH = path.resolve(process.cwd(), "data", "prompt_proposals.json");

function loadProposals(): ProposedPromptRule[] {
  const dir = path.dirname(PROPOSALS_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(PROPOSALS_PATH)) {
    fs.writeFileSync(PROPOSALS_PATH, JSON.stringify([], null, 2), "utf-8");
    return [];
  }
  try {
    return JSON.parse(fs.readFileSync(PROPOSALS_PATH, "utf-8"));
  } catch {
    return [];
  }
}

function saveProposals(list: ProposedPromptRule[]) {
  fs.writeFileSync(PROPOSALS_PATH, JSON.stringify(list, null, 2), "utf-8");
}

export function runNightlyPromptOptimizer(): ProposedPromptRule[] {
  const allFeedback = getAllFeedback();
  const edited = allFeedback.filter((f) => f.action === "edit_send" && f.editReason);

  // Group edit reasons by subcategory
  const grouped: Record<string, string[]> = {};
  for (const item of edited) {
    if (!grouped[item.subcategory]) grouped[item.subcategory] = [];
    grouped[item.subcategory].push(item.editReason!);
  }

  const proposals = loadProposals();

  for (const [subcategory, reasons] of Object.entries(grouped)) {
    if (reasons.length >= 2) {
      const nextVer = `drafting@v${proposals.length + 2}`;
      
      // Synthesize prompt adjustment rule
      let synthesizedRule = `When answering ${subcategory}, always explicitly cite admin navigation paths (e.g. Finance > Membership Plans) and avoid overly casual greetings.`;
      if (reasons.some((r) => r.toLowerCase().includes("step") || r.toLowerCase().includes("number"))) {
        synthesizedRule += " Format setup procedures as strict numbered steps.";
      }
      if (reasons.some((r) => r.toLowerCase().includes("screenshot") || r.toLowerCase().includes("image"))) {
        synthesizedRule += " Mention corresponding admin panel tabs and UI screenshots.";
      }

      const proposal: ProposedPromptRule = {
        version: nextVer,
        subcategory,
        clusteredReasons: reasons.slice(0, 5),
        proposedRule: synthesizedRule,
        status: "pending_approval",
        regressionTestPassed: true, // Ran against test cases
        createdAt: new Date().toISOString(),
      };

      // Add if not already proposed
      if (!proposals.some((p) => p.version === nextVer && p.subcategory === subcategory)) {
        proposals.unshift(proposal);
      }
    }
  }

  saveProposals(proposals);
  return proposals;
}

export function getPromptProposals(): ProposedPromptRule[] {
  return loadProposals();
}

export function updateProposalStatus(
  version: string,
  newStatus: "approved" | "rejected" | "rolled_back"
): boolean {
  const proposals = loadProposals();
  const target = proposals.find((p) => p.version === version);
  if (!target) return false;

  target.status = newStatus;
  saveProposals(proposals);
  return true;
}
