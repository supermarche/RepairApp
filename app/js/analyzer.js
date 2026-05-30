import { actionGroups, categoryTips, failureRules, riskRules } from "./rules.js";

const levelRank = {
  low: 0,
  caution: 1,
  high: 2,
};

export function analyzeProblem({ category, description }) {
  const text = normalize(description);
  const risks = detectRisks(text);
  const riskLevel = risks.reduce(
    (highest, risk) => (levelRank[risk.level] > levelRank[highest] ? risk.level : highest),
    "low",
  );
  const failureType = detectFailureType(text);

  return {
    category,
    failureType,
    riskLevel,
    riskReasons: risks.map((risk) => risk.label),
    actions: getActions(riskLevel),
    recommendedNextStep: recommendNextStep({ category, failureType, riskLevel }),
    preventionTip: categoryTips[category] || categoryTips.unknown,
  };
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function detectRisks(text) {
  return riskRules.filter((rule) =>
    rule.keywords.some((keyword) => text.includes(keyword)),
  );
}

function detectFailureType(text) {
  const match = failureRules.find((rule) =>
    rule.keywords.some((keyword) => text.includes(keyword)),
  );

  return match ? match.type : "Unknown or needs verification";
}

function getActions(riskLevel) {
  if (riskLevel === "high") {
    return actionGroups.map((group) => {
      if (group.title === "Repair") {
        return {
          ...group,
          actions: ["Do not attempt DIY repair while the risk is present"],
        };
      }

      if (group.title === "Basic diagnostics") {
        return {
          ...group,
          actions: ["Stop using the item and move it to a safe place only if that can be done safely"],
        };
      }

      return group;
    });
  }

  return actionGroups;
}

function recommendNextStep({ category, failureType, riskLevel }) {
  if (riskLevel === "high") {
    return "Stop using the item now. Keep it away from people and flammable material if safe, then contact a qualified professional or choose replacement/recycling.";
  }

  if (riskLevel === "caution") {
    return "Pause use and inspect the issue carefully. Choose a low-risk fix only if the item is stable, unplugged when relevant, and the damage is minor.";
  }

  if (failureType === "Misconfigured or resettable") {
    return "Try a reset or restart first, then re-check whether the original problem is reproducible.";
  }

  if (failureType === "Maintenance or consumable") {
    return "Start with maintenance: clean, descale, calibrate, or replace the simple consumable before considering repair.";
  }

  if (failureType === "Physical damage") {
    return category === "electrical"
      ? "Unplug the device and inspect for visible damage. Use professional repair for anything involving casing, cable, battery, or internal parts."
      : "Check whether the damaged part carries load. Repair only if the item can be made stable; otherwise replace or recycle it.";
  }

  return "Verify the symptom, compare the likely effort and value, then choose the safest option from maintenance, repair, professional help, replacement, or recycling.";
}
