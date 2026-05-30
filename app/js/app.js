import { analyzeProblem } from "./analyzer.js";

const form = document.querySelector("#repair-form");
const category = document.querySelector("#category");
const problem = document.querySelector("#problem");
const riskTitle = document.querySelector("#risk-title");
const riskBadge = document.querySelector("#risk-badge");
const safetyWarning = document.querySelector("#safety-warning");
const failureType = document.querySelector("#failure-type");
const signals = document.querySelector("#signals");
const actions = document.querySelector("#actions");
const recommendation = document.querySelector("#recommendation");
const prevention = document.querySelector("#prevention");

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const result = analyzeProblem({
    category: category.value,
    description: problem.value,
  });

  renderResult(result);
});

function renderResult(result) {
  riskTitle.textContent = riskTitleText(result.riskLevel);
  riskBadge.textContent = result.riskLevel;
  riskBadge.className = `risk-badge ${result.riskLevel}`;

  failureType.textContent = result.failureType;
  signals.textContent = result.riskReasons.length
    ? result.riskReasons.join(", ")
    : "No specific safety risk keywords detected.";

  if (result.riskLevel === "high") {
    safetyWarning.classList.remove("hidden");
    safetyWarning.textContent =
      "Safety warning: this description contains high-risk signals. Avoid DIY repair and prioritize stopping use, professional help, replacement, or recycling.";
  } else if (result.riskLevel === "caution") {
    safetyWarning.classList.remove("hidden");
    safetyWarning.textContent =
      "Safety note: this description contains caution signals. Pause use, inspect carefully, and avoid repair steps that could make the item unstable or unsafe.";
  } else {
    safetyWarning.classList.add("hidden");
    safetyWarning.textContent = "";
  }

  actions.replaceChildren(
    ...result.actions.map((group) => {
      const card = document.createElement("article");
      card.className = "action-card";

      const heading = document.createElement("h4");
      heading.textContent = group.title;

      const list = document.createElement("ul");
      group.actions.forEach((action) => {
        const item = document.createElement("li");
        item.textContent = action;
        list.append(item);
      });

      card.append(heading, list);
      return card;
    }),
  );

  recommendation.textContent = result.recommendedNextStep;
  prevention.textContent = result.preventionTip;
}

function riskTitleText(level) {
  if (level === "high") {
    return "High safety risk detected";
  }

  if (level === "caution") {
    return "Use caution before acting";
  }

  return "Low immediate safety risk";
}
