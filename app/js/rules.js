export const riskRules = [
  {
    level: "high",
    label: "Fire, smoke, or burning smell",
    keywords: ["fire", "flame", "smoke", "burning", "burnt", "sparks", "smell of smoke"],
  },
  {
    level: "high",
    label: "Battery swelling or leakage",
    keywords: ["swollen battery", "battery is swollen", "battery swelling", "bulging battery", "battery leak", "leaking battery"],
  },
  {
    level: "high",
    label: "Electric shock or exposed live parts",
    keywords: ["electric shock", "shock", "exposed wire", "live wire", "short circuit"],
  },
  {
    level: "high",
    label: "Uncontrolled heat",
    keywords: ["overheating", "very hot", "too hot", "hot casing", "hot", "warm battery"],
  },
  {
    level: "caution",
    label: "Leak or liquid exposure",
    keywords: ["leak", "leaking", "water inside", "wet", "liquid"],
  },
  {
    level: "caution",
    label: "Sharp edge or injury risk",
    keywords: ["sharp", "cut", "cracked glass", "splinter", "injury"],
  },
  {
    level: "caution",
    label: "Instability or collapse risk",
    keywords: ["unstable", "wobbly", "loose leg", "collapsing", "falls over"],
  },
];

export const failureRules = [
  {
    type: "Misconfigured or resettable",
    keywords: ["not responding", "frozen", "stuck", "won't connect", "cannot connect", "software", "settings"],
  },
  {
    type: "Maintenance or consumable",
    keywords: ["dirty", "dust", "clogged", "descale", "filter", "empty", "battery dead", "needs cleaning"],
  },
  {
    type: "Physical damage",
    keywords: ["broken", "cracked", "snapped", "bent", "loose", "torn", "damaged"],
  },
  {
    type: "Function impaired",
    keywords: ["does not turn on", "won't turn on", "stopped working", "not working", "weak", "slow"],
  },
  {
    type: "Wear",
    keywords: ["worn", "old", "wear", "rust", "frayed"],
  },
];

export const actionGroups = [
  {
    title: "Basic diagnostics",
    actions: ["Reset or restart", "Check power, settings, and visible symptoms"],
  },
  {
    title: "Repair",
    actions: ["Clean, tighten, adjust, or replace a simple consumable", "Attempt a low-risk DIY repair only when stable and unplugged"],
  },
  {
    title: "Professional help",
    actions: ["Ask a repair cafe, maker space, technician, or manufacturer"],
  },
  {
    title: "Workaround",
    actions: ["Use a temporary safe alternative while deciding on repair"],
  },
  {
    title: "Replacement",
    actions: ["Replace the item if repair is unsafe, unreliable, or uneconomical"],
  },
  {
    title: "Recycling",
    actions: ["Recycle or dispose through the correct local channel"],
  },
];

export const categoryTips = {
  electrical: "Keep vents clean, stop using devices that heat unusually, and inspect cables before use.",
  furniture: "Tighten fasteners early and stop using furniture when it becomes unstable.",
  tool: "Store tools dry, check moving parts, and avoid using cracked load-bearing parts.",
  household: "Clean and inspect items regularly so small wear does not become a safety issue.",
  unknown: "Check items regularly and stop using anything that shows new safety warning signs.",
};
