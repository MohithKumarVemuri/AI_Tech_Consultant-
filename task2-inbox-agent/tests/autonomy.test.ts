import { describe, it, expect } from "vitest";
import { AutonomyManager } from "../src/autonomy/manager";

describe("Autonomy Manager", () => {
  it("requires 20 consecutive unchanged drafts to reach eligibility", () => {
    const mgr = new AutonomyManager();
    const subcat = `test_subcat_${Date.now()}`;

    // 19 unchanged
    for (let i = 0; i < 19; i++) {
      mgr.recordOutcome(subcat, "approve_send", true);
    }
    let st = mgr.getState(subcat);
    expect(st.consecutiveUnchanged).toBe(19);
    expect(st.eligible).toBe(false);

    // 20th unchanged -> eligible!
    mgr.recordOutcome(subcat, "approve_send", true);
    st = mgr.getState(subcat);
    expect(st.consecutiveUnchanged).toBe(20);
    expect(st.eligible).toBe(true);

    // Human edit resets counter to 0!
    mgr.recordOutcome(subcat, "edit_send", false);
    st = mgr.getState(subcat);
    expect(st.consecutiveUnchanged).toBe(0);
  });
});
