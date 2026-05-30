import { analyzeProblem } from "./analyzer.js";
import { matchResources, resourceTypes, typeLabel } from "./resources.js";

const form = document.querySelector("#repair-form");
const category = document.querySelector("#category");
const problem = document.querySelector("#problem");
const exampleButtons = document.querySelectorAll("[data-example]");
const riskTitle = document.querySelector("#risk-title");
const riskBadge = document.querySelector("#risk-badge");
const safetyWarning = document.querySelector("#safety-warning");
const failureType = document.querySelector("#failure-type");
const signals = document.querySelector("#signals");
const actions = document.querySelector("#actions");
const recommendation = document.querySelector("#recommendation");
const prevention = document.querySelector("#prevention");
const resourceType = document.querySelector("#resource-type");
const resourceCategory = document.querySelector("#resource-category");
const helpSummary = document.querySelector("#help-summary");
const resources = document.querySelector("#resources");

let latestResult = null;

resourceType.replaceChildren(
  ...resourceTypes.map((type) => {
    const option = document.createElement("option");
    option.value = type.value;
    option.textContent = type.label;
    return option;
  }),
);

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const result = analyzeProblem({
    category: category.value,
    description: problem.value,
  });

  latestResult = result;
  renderResult(result);
  renderResources();
});

resourceType.addEventListener("change", renderResources);
resourceCategory.addEventListener("change", renderResources);

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const example = button.dataset.example;

    if (example === "battery") {
      category.value = "electrical";
      problem.value = "My laptop battery is swollen and the case feels warm.";
    } else {
      category.value = "tool";
      problem.value = "My selfie stick is stuck and the clamp will not move.";
    }

    form.requestSubmit();
  });
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

function renderResources() {
  if (!latestResult) {
    return;
  }

  const matches = matchResources({
    category: latestResult.category,
    riskLevel: latestResult.riskLevel,
    typeFilter: resourceType.value,
    categoryFilter: resourceCategory.value,
  });

  helpSummary.textContent = `${latestResult.helpNeeded}. Showing ${matches.length} matching local demo resources, prioritized for ${latestResult.riskLevel} risk.`;

  resources.replaceChildren(
    ...matches.map((resource) => {
      const card = document.createElement("article");
      card.className = "resource-card";

      const heading = document.createElement("h4");
      heading.textContent = resource.name;

      const meta = document.createElement("p");
      meta.className = "resource-meta";
      meta.textContent = `${typeLabel(resource.type)} | ${resource.location}`;

      const description = document.createElement("p");
      description.textContent = resource.description;

      const services = document.createElement("p");
      services.className = "resource-services";
      services.textContent = `Services: ${resource.services.join(", ")}`;

      const reason = document.createElement("p");
      reason.className = "match-reason";
      reason.textContent = resource.matchReason;

      const source = document.createElement("span");
      source.className = "source-badge";
      source.textContent = resource.source;

      card.append(heading, meta, description, services, reason, source);
      return card;
    }),
  );
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
