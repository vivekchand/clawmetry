import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clawbert } from "../mascot";
import { PermissionCollarDial, type RiskLevel } from "../components/PermissionCollarDial";
import { ProPaywallModal } from "../components/ProPaywallModal";

interface ApprovalItem {
  id: string;
  agent: string;
  tool: string;
  risk: RiskLevel;
  age: string;
  done?: "ok" | "blocked";
}

interface ApprovalReason {
  label: string;
  weight: number;
}

interface ApprovalAction {
  method: string;
  account: string;
  body: string;
  reach: number;
}

interface ApprovalDetail {
  risk_score: number;
  median_score: number;
  risk_level: RiskLevel;
  title: string;
  agent: string;
  session: string;
  age: string;
  action: ApprovalAction;
  reasons: ApprovalReason[];
  rule_suggestion: string;
}

interface ApprovalsData {
  summary: { awaiting: number; median_response: string; auto_approved_pct: number };
  items: ApprovalItem[];
  details: Record<string, ApprovalDetail>;
  pro_gated_upsell: boolean;
  is_pro: boolean;
}

type Decision = "approve" | "deny" | "edit";

/** Normalize Stage A payloads (selected_detail, no ids) and Stage B (details map). */
function normalizeApprovalsData(raw: Record<string, unknown>): ApprovalsData {
  const itemsRaw = (raw.items as Record<string, unknown>[]) ?? [];
  const items: ApprovalItem[] = itemsRaw.map((it, i) => ({
    id: String(it.id ?? `legacy-${i}`),
    agent: String(it.agent ?? ""),
    tool: String(it.tool ?? ""),
    risk: (it.risk as RiskLevel) ?? "med",
    age: String(it.age ?? ""),
    done: it.done as ApprovalItem["done"],
  }));

  let details = (raw.details as Record<string, ApprovalDetail> | undefined) ?? {};
  const legacyDetail = raw.selected_detail as ApprovalDetail | undefined;
  if (!Object.keys(details).length && legacyDetail) {
    details = Object.fromEntries(items.map((it) => [it.id, legacyDetail]));
  }

  const pending = items.filter(isPending);
  const summaryRaw = raw.summary as ApprovalsData["summary"] | undefined;

  return {
    summary: summaryRaw ?? {
      awaiting: pending.length,
      median_response: "22s",
      auto_approved_pct: 84,
    },
    items,
    details,
    pro_gated_upsell: Boolean(raw.pro_gated_upsell ?? pending.length > 0),
    is_pro: Boolean(raw.is_pro),
  };
}

function riskColor(risk: RiskLevel): string {
  if (risk === "high") return "var(--claw-red)";
  if (risk === "med") return "var(--amber)";
  return "var(--ink-3)";
}

function riskLabel(risk: RiskLevel): string {
  if (risk === "high") return "high";
  if (risk === "med") return "medium";
  return "low";
}

function isPending(item: ApprovalItem): boolean {
  return !item.done;
}

function firstPendingIdx(items: ApprovalItem[]): number {
  const idx = items.findIndex(isPending);
  return idx >= 0 ? idx : 0;
}

function indexForId(items: ApprovalItem[], id: string | null): number {
  if (!id) return firstPendingIdx(items);
  const idx = items.findIndex((it) => it.id === id);
  return idx >= 0 ? idx : firstPendingIdx(items);
}

export function ApprovalsPage() {
  const [data, setData] = useState<ApprovalsData | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [bounce, setBounce] = useState(false);
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [autoApplyRule, setAutoApplyRule] = useState(false);
  const [ruleMsg, setRuleMsg] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const load = useCallback((selectId?: string | null) => {
    return fetch("/api/v2/approvals")
      .then((r) => {
        if (!r.ok) throw new Error(`GET /api/v2/approvals → ${r.status}`);
        return r.json();
      })
      .then((raw) => {
        const d = normalizeApprovalsData(raw);
        if (!Object.keys(d.details).length) {
          setApiError(
            "Approvals API returned no detail payload. Restart Flask so it picks up the Stage B routes: CLAWMETRY_V2=1 python3 dashboard.py --host 127.0.0.1 --port 8900 --no-debug",
          );
        } else {
          setApiError(null);
        }
        setData(d);
        setSelectedIdx(indexForId(d.items, selectId ?? null));
        return d;
      });
  }, []);

  useEffect(() => {
    load()
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [load]);

  const pendingItems = data?.items.filter(isPending) ?? [];
  const selectedItem = data && selectedIdx !== null ? data.items[selectedIdx] : null;
  const detail = selectedItem ? data?.details[selectedItem.id] : null;
  const selectedPending = selectedItem ? isPending(selectedItem) : false;

  const postDecision = useCallback(
    async (decision: Decision) => {
      if (!data || !selectedItem || !selectedPending || acting) return;
      setActing(true);
      try {
        const res = await fetch(`/api/v2/approvals/${selectedItem.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision, auto_apply_rule: autoApplyRule }),
        });
        if (!res.ok) throw new Error(await res.text());
        const next = normalizeApprovalsData(await res.json());
        setData(next);
        if (decision === "approve" || decision === "edit") {
          setBounce(true);
        }
        const nextPending = next.items.find(isPending);
        setSelectedIdx(nextPending ? next.items.indexOf(nextPending) : 0);
      } catch (err) {
        console.error(err);
      } finally {
        setActing(false);
      }
    },
    [data, selectedItem, selectedPending, acting, autoApplyRule],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!selectedPending || acting) return;
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      const key = e.key.toLowerCase();
      if (key === "a") {
        e.preventDefault();
        postDecision("approve");
      } else if (key === "d") {
        e.preventDefault();
        postDecision("deny");
      } else if (key === "e") {
        e.preventDefault();
        postDecision("edit");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedPending, acting, postDecision]);

  const handleCreateRule = () => {
    if (data?.pro_gated_upsell || !data?.is_pro) {
      setPaywallOpen(true);
      return;
    }
    setRuleMsg("Rule created (mock).");
    window.setTimeout(() => setRuleMsg(null), 3000);
  };

  if (loading) {
    return (
      <div style={{ padding: 40, color: "var(--ink-4)" }} className="mono">
        Loading approvals…
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: 40, color: "var(--claw-red)" }} className="mono">
        Failed to load approvals.
      </div>
    );
  }

  if (pendingItems.length === 0) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 40 }}>
        <div style={{ textAlign: "center", maxWidth: 420 }}>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
            <Clawbert size={140} mood="calm" tool={null} />
          </div>
          <div style={{ fontSize: 22, fontWeight: 500, color: "var(--ink)", marginBottom: 8 }}>
            Hold the claw is empty. All approved.
          </div>
          <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)" }}>
            {data.summary.auto_approved_pct}% auto-approved · median response {data.summary.median_response}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* summary strip */}
        {apiError && (
          <div
            className="mono"
            style={{
              padding: "10px 22px",
              borderBottom: "1px solid var(--claw-red)",
              background: "var(--claw-red-wash)",
              fontSize: 11,
              color: "var(--claw-red-deep)",
            }}
          >
            {apiError}
          </div>
        )}
        <div
          className="mono"
          style={{
            padding: "10px 22px",
            borderBottom: "1px dashed var(--line)",
            background: "var(--paper)",
            fontSize: 10,
            color: "var(--ink-3)",
            display: "flex",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <span>
            <b style={{ color: "var(--ink-2)" }}>{data.summary.awaiting}</b> awaiting
          </span>
          <span>median response · {data.summary.median_response}</span>
          <span>{data.summary.auto_approved_pct}% auto-approved</span>
          {selectedPending && (
            <span style={{ marginLeft: "auto", color: "var(--ink-4)" }}>
              A approve · D deny · E edit
            </span>
          )}
        </div>

        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "320px 1fr", minHeight: 0 }}>
          {/* inbox list */}
          <div style={{ borderRight: "1px solid var(--line)", overflow: "auto", background: "var(--paper)" }}>
            {data.items.map((a, i) => {
              const color = riskColor(a.risk);
              const isSelected = i === selectedIdx;
              return (
                <div
                  key={a.id}
                  onClick={() => setSelectedIdx(i)}
                  style={{
                    padding: "14px 16px",
                    borderBottom: "1px dashed var(--line)",
                    background: isSelected ? "var(--paper-deep)" : "transparent",
                    cursor: "pointer",
                    borderLeft: isSelected ? "2px solid var(--claw-red)" : "2px solid transparent",
                    opacity: a.done ? 0.65 : 1,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <span className="cm-tag" style={{ color, borderColor: color, fontSize: 9 }}>
                      {a.risk}
                    </span>
                    <span className="mono" style={{ fontSize: 10, color: "var(--ink-2)" }}>
                      {a.tool}
                    </span>
                    {a.done === "ok" && (
                      <span style={{ color: "var(--moss)", fontSize: 11, marginLeft: "auto" }}>✓</span>
                    )}
                    {a.done === "blocked" && (
                      <span style={{ color: "var(--claw-red)", fontSize: 11, marginLeft: "auto" }}>✕</span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--ink-3)" }}>
                    <span className="mono">{a.agent}</span> · {a.age}
                  </div>
                </div>
              );
            })}
          </div>

          {/* detail panel */}
          <div ref={panelRef} style={{ padding: 24, overflow: "auto", background: "var(--paper-deep)" }}>
            {detail && selectedItem ? (
              <AnimatePresence mode="wait">
                <motion.div
                  key={selectedItem.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.18 }}
                >
                  <motion.div
                    animate={
                      bounce
                        ? { y: [0, -14, 5, -3, 0], scale: [1, 1.02, 0.99, 1] }
                        : { y: 0, scale: 1 }
                    }
                    transition={{ duration: 0.55, ease: [0.34, 1.56, 0.64, 1] }}
                    onAnimationComplete={() => setBounce(false)}
                  >
                    <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 14 }}>
                      <div>
                        <div className="caps" style={{ color: riskColor(detail.risk_level) }}>
                          Permission collar · {riskLabel(detail.risk_level)} risk
                        </div>
                        <div style={{ fontSize: 22, fontWeight: 500 }}>{detail.title}</div>
                        <div className="mono" style={{ fontSize: 11, color: "var(--ink-4)", marginTop: 2 }}>
                          {detail.agent} · session {detail.session} · {detail.age}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 24, marginTop: 8 }}>
                      <div
                        className="cm-card"
                        style={{
                          padding: 14,
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: 8,
                        }}
                      >
                        <PermissionCollarDial
                          score={detail.risk_score}
                          median={detail.median_score}
                          riskLevel={detail.risk_level}
                        />
                        <div className="mono" style={{ fontSize: 10, color: "var(--ink-3)", textAlign: "center" }}>
                          scored by: novelty · audience size · sentiment
                        </div>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        <div className="cm-card" style={{ padding: 14 }}>
                          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 6 }}>
                            What it wants to do
                          </div>
                          <div
                            className="mono"
                            style={{
                              fontSize: 12,
                              padding: 12,
                              background: "var(--panel-2)",
                              borderRadius: 6,
                              color: "var(--ink-2)",
                              lineHeight: 1.5,
                            }}
                          >
                            {detail.action.method}
                            <br />
                            <span style={{ color: "var(--ink-4)" }}>account:</span> {detail.action.account}
                            <br />
                            <span style={{ color: "var(--ink-4)" }}>body:</span> &quot;{detail.action.body}&quot;
                            <br />
                            {detail.action.reach > 0 && (
                              <>
                                <span style={{ color: "var(--ink-4)" }}>reach:</span>{" "}
                                {detail.action.reach.toLocaleString()}
                                {detail.action.reach > 100 ? " followers" : " recipient"}
                              </>
                            )}
                          </div>
                        </div>

                        <div className="cm-card" style={{ padding: 14 }}>
                          <div className="caps" style={{ color: "var(--ink-4)", marginBottom: 8 }}>
                            Why ClawMetry flagged it
                          </div>
                          {detail.reasons.map((r, i) => (
                            <div
                              key={i}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 10,
                                padding: "4px 0",
                                fontSize: 12,
                              }}
                            >
                              <div
                                style={{
                                  width: 100,
                                  height: 6,
                                  background: "var(--panel-2)",
                                  borderRadius: 3,
                                  overflow: "hidden",
                                }}
                              >
                                <div
                                  style={{
                                    width: `${r.weight * 100}%`,
                                    height: "100%",
                                    background: riskColor(detail.risk_level),
                                  }}
                                />
                              </div>
                              <span style={{ flex: 1, color: "var(--ink-2)" }}>{r.label}</span>
                              <span className="mono" style={{ fontSize: 10, color: "var(--ink-4)" }}>
                                +{r.weight.toFixed(2)}
                              </span>
                            </div>
                          ))}
                        </div>

                        {selectedPending ? (
                          <>
                            <div style={{ display: "flex", gap: 8 }}>
                              <button
                                type="button"
                                className="cm-btn primary"
                                style={{ flex: 1, justifyContent: "center" }}
                                disabled={acting}
                                onClick={() => postDecision("approve")}
                              >
                                ✓ Approve once
                              </button>
                              <button
                                type="button"
                                className="cm-btn"
                                style={{ flex: 1, justifyContent: "center" }}
                                disabled={acting}
                                onClick={() => postDecision("edit")}
                              >
                                ↻ Approve &amp; edit
                              </button>
                              <button
                                type="button"
                                className="cm-btn"
                                style={{
                                  background: "var(--paper)",
                                  color: "var(--claw-red)",
                                  borderColor: "var(--claw-red)",
                                }}
                                disabled={acting}
                                onClick={() => postDecision("deny")}
                              >
                                ✕ Deny
                              </button>
                            </div>

                            <label
                              className="cm-card"
                              style={{
                                padding: "10px 12px",
                                fontSize: 11,
                                color: "var(--ink-3)",
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                cursor: "pointer",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={autoApplyRule}
                                onChange={(e) => setAutoApplyRule(e.target.checked)}
                              />
                              <span>Auto-approve next 5 like this</span>
                            </label>

                            {detail.rule_suggestion && (
                              <div
                                className="cm-card"
                                style={{
                                  padding: 12,
                                  fontSize: 11,
                                  color: "var(--ink-3)",
                                  display: "flex",
                                  alignItems: "center",
                                  gap: 8,
                                }}
                              >
                                <span style={{ fontSize: 14 }}>✻</span>
                                <span>
                                  <b>Promote to rule:</b> {detail.rule_suggestion}
                                </span>
                                <button
                                  type="button"
                                  className="cm-btn tiny"
                                  style={{ marginLeft: "auto" }}
                                  onClick={handleCreateRule}
                                >
                                  create rule
                                </button>
                              </div>
                            )}
                            {ruleMsg && (
                              <div className="mono" style={{ fontSize: 10, color: "var(--moss)", textAlign: "right" }}>
                                {ruleMsg}
                              </div>
                            )}
                          </>
                        ) : (
                          <div
                            className="cm-card"
                            style={{ padding: 14, fontSize: 12, color: "var(--ink-3)", textAlign: "center" }}
                          >
                            {selectedItem.done === "ok" ? "✓ Approved" : "✕ Blocked"} · resolved
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                </motion.div>
              </AnimatePresence>
            ) : (
              <div style={{ color: "var(--ink-4)" }} className="mono">
                Select an item from the inbox.
              </div>
            )}
          </div>
        </div>
      </div>

      <ProPaywallModal open={paywallOpen} onClose={() => setPaywallOpen(false)} />
    </>
  );
}
