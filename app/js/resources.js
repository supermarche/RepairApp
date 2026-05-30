export const resourceTypes = [
  { value: "all", label: "All resource types" },
  { value: "community", label: "Repair Cafe / community" },
  { value: "tools", label: "Tool access" },
  { value: "workshop", label: "Workshop / makerspace" },
  { value: "guidance", label: "Knowledge / guidance" },
  { value: "commercial", label: "Commercial repair" },
  { value: "disposal", label: "Recycling / safe disposal" },
];

export const localResources = [
  {
    name: "Repair Cafe Demo Hub",
    type: "community",
    categories: ["electrical", "furniture", "tool", "household", "unknown"],
    services: ["diagnosis", "minor repair", "guidance"],
    location: "Community Center, Main Square 4",
    description: "Volunteer repair support for everyday objects and first diagnosis.",
    source: "demo-data",
  },
  {
    name: "Tool Library Corner",
    type: "tools",
    categories: ["furniture", "tool", "household"],
    services: ["borrow tools", "basic guidance"],
    location: "Library Annex, Workshop Street 8",
    description: "Borrow hand tools and measuring tools for low-risk repairs.",
    source: "demo-data",
  },
  {
    name: "Maker Space Prototype Lab",
    type: "workshop",
    categories: ["tool", "household", "furniture"],
    services: ["3D printing", "small fabrication", "workbench access"],
    location: "Innovation Yard, Hall B",
    description: "Workshop access for brackets, sleeves, clamps, and small custom parts.",
    source: "future-osm-import",
  },
  {
    name: "Open Repair Knowledge Desk",
    type: "guidance",
    categories: ["electrical", "furniture", "tool", "household", "unknown"],
    services: ["repair manuals", "triage", "maintenance tips"],
    location: "Online and at the community desk",
    description: "Helps identify repair manuals, common fixes, and safe first checks.",
    source: "demo-data",
  },
  {
    name: "Certified Electronics Service",
    type: "commercial",
    categories: ["electrical"],
    services: ["electrical safety check", "battery service", "device repair"],
    location: "Service Lane 12",
    description: "Professional repair for electrical devices, batteries, cables, and internal faults.",
    source: "future-osm-import",
  },
  {
    name: "Safe Battery Drop-Off",
    type: "disposal",
    categories: ["electrical"],
    services: ["battery disposal", "e-waste collection", "safe handling advice"],
    location: "Recycling Point North, Gate 2",
    description: "Safe disposal point for swollen batteries, damaged electronics, and e-waste.",
    source: "future-osm-import",
  },
  {
    name: "Furniture Fix Workshop",
    type: "community",
    categories: ["furniture", "household"],
    services: ["wood repair", "stability check", "fastener replacement"],
    location: "Craft Hall, Timber Road 5",
    description: "Community support for chairs, shelves, tables, and small household furniture.",
    source: "demo-data",
  },
  {
    name: "Appliance Maintenance Shop",
    type: "commercial",
    categories: ["electrical", "household"],
    services: ["maintenance", "descaling", "spare parts", "professional repair"],
    location: "Market Street 18",
    description: "Commercial service for small appliances and routine maintenance.",
    source: "demo-data",
  },
  {
    name: "Circular Goods Reuse Point",
    type: "disposal",
    categories: ["furniture", "tool", "household", "unknown"],
    services: ["reuse assessment", "recycling", "donation intake"],
    location: "Reuse Center, Depot Road 3",
    description: "Checks whether items can be reused, donated, recycled, or safely disposed.",
    source: "future-osm-import",
  },
  {
    name: "Neighborhood Skill Share",
    type: "guidance",
    categories: ["furniture", "tool", "household"],
    services: ["repair coaching", "material advice", "workaround ideas"],
    location: "Weekly pop-up at Community Center",
    description: "Local volunteers share practical repair knowledge for ordinary low-risk cases.",
    source: "demo-data",
  },
];

const priorityByRisk = {
  high: ["commercial", "disposal", "guidance", "community", "workshop", "tools"],
  caution: ["guidance", "community", "commercial", "tools", "workshop", "disposal"],
  low: ["community", "tools", "guidance", "workshop", "commercial", "disposal"],
};

export function matchResources({ category, riskLevel, typeFilter = "all", categoryFilter = "all" }) {
  const selectedCategory = categoryFilter === "all" ? category : categoryFilter;
  const priorities = priorityByRisk[riskLevel] || priorityByRisk.low;

  return localResources
    .filter((resource) => typeFilter === "all" || resource.type === typeFilter)
    .filter((resource) =>
      selectedCategory === "all" ||
      selectedCategory === "unknown" ||
      resource.categories.includes(selectedCategory) ||
      resource.categories.includes("unknown"),
    )
    .map((resource) => ({
      ...resource,
      matchReason: getMatchReason(resource, riskLevel),
      score: getScore(resource, priorities, selectedCategory),
    }))
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
}

export function typeLabel(type) {
  return resourceTypes.find((item) => item.value === type)?.label || type;
}

function getScore(resource, priorities, selectedCategory) {
  const priorityIndex = priorities.indexOf(resource.type);
  const typeScore = priorityIndex === -1 ? 0 : (priorities.length - priorityIndex) * 10;
  const categoryScore = resource.categories.includes(selectedCategory) ? 8 : 0;

  return typeScore + categoryScore;
}

function getMatchReason(resource, riskLevel) {
  if (riskLevel === "high" && resource.type === "commercial") {
    return "Prioritized because high-risk cases need qualified professional help.";
  }

  if (riskLevel === "high" && resource.type === "disposal") {
    return "Prioritized because safe disposal or recycling may be the safest outcome.";
  }

  if (riskLevel === "low" && ["community", "tools", "guidance", "workshop"].includes(resource.type)) {
    return "Prioritized for ordinary low-risk cases where local support can help before replacement.";
  }

  return "Matches the selected category and can support this repair decision.";
}
