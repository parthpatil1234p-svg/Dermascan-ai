export const APP_NAME = "DermaScan AI";

export const MEDICAL_DISCLAIMER =
  "DermaScan AI provides general skincare guidance based on visible facial characteristics and user-provided information. It is not a medical diagnostic system, does not prescribe treatment, and does not replace advice from a qualified dermatologist.";

export const SAFETY_ESCALATION_GUIDANCE =
  "Users experiencing severe, painful, infected, persistent, rapidly changing, or unusual skin concerns should seek advice from a qualified healthcare professional.";

export const ROUTES = {
  home: "/",
  login: "/login",
  register: "/register",
  skinProfile: "/skin-profile",
  faceScan: "/face-scan",
  imageQualityCheck: "/image-quality-check",
  faceDetection: "/face-detection",
  imagePreprocessing: "/image-preprocessing",
  skinTypeAnalysis: "/skin-type-analysis",
  skinConcernAnalysis: "/skin-concern-analysis",
  productEligibility: "/product-eligibility",
  productRecommendations: "/product-recommendations",
  skincareRoutine: "/skincare-routine",
  finalReport: "/final-report",
  productDiscovery: "/product-discovery",
  products: "/products",
  ingredients: "/ingredients",
  analysisLoading: "/analysis-loading",
  results: "/results",
  reports: "/reports",
  feedback: "/feedback",
  feedbackHistory: "/feedback/history",
};

export const NAV_LINKS = [
  { label: "Home", to: ROUTES.home },
  { label: "How It Works", to: "/#how-it-works", anchor: true },
  { label: "Benefits", to: "/#benefits", anchor: true },
  { label: "Start Analysis", to: ROUTES.skinProfile },
  { label: "Login", to: ROUTES.login },
  { label: "Register", to: ROUTES.register },
];

export const AGE_GROUPS = [
  "Under 18",
  "18-25",
  "26-35",
  "36-45",
  "46-60",
  "Above 60",
  "Prefer not to say",
];

export const FRAGRANCE_OPTIONS = [
  "Fragrance-free only",
  "Prefer fragrance-free",
  "No preference",
];

export const SKIN_BEHAVIOUR_LEVELS = ["Low", "Moderate", "High", "Not sure"];

export const SENSITIVITY_OPTIONS = ["Yes", "No", "Not sure"];

export const EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"];

export const CURRENT_PRODUCT_OPTIONS = [
  "Cleanser",
  "Toner",
  "Serum",
  "Moisturizer",
  "Sunscreen",
  "Exfoliant",
  "Acne-care product",
  "Under-eye product",
  "Other",
];

export const WORKFLOW_STEPS = [
  {
    title: "Complete skin profile",
    description:
      "Share age group, sensitivity, allergies, budget, ingredient preferences, and location.",
  },
  {
    title: "Upload facial image",
    description:
      "Add a clear JPG or PNG facial image using even lighting and a neutral expression.",
  },
  {
    title: "Check image quality",
    description:
      "Measure whole-image sharpness, lighting, contrast, resolution, and aspect ratio.",
  },
  {
    title: "Detect usable facial region",
    description:
      "Confirm exactly one face, check positioning, and prepare a private temporary crop.",
  },
  {
    title: "Prepare consistent model input",
    description:
      "Standardize the private face crop to a deterministic RGB model-input contract.",
  },
  {
    title: "Estimate broad skin type",
    description:
      "Use a validated four-class model, conservative confidence rules, and transparent questionnaire comparison.",
  },
  {
    title: "Review visible characteristics",
    description:
      "Evaluate independent appearance labels with calibrated thresholds, visible uncertainty, and non-diagnostic wording.",
  },
];

export const BENEFITS = [
  {
    title: "Personalized recommendations",
    description:
      "Matches suggested products to skin profile details instead of using one routine for everyone.",
  },
  {
    title: "Faster product discovery",
    description:
      "Helps users narrow down suitable product categories before comparing brands.",
  },
  {
    title: "Allergy-aware filtering",
    description:
      "Keeps known allergies and ingredients to avoid visible during recommendation planning.",
  },
  {
    title: "Budget-based suggestions",
    description:
      "Supports minimum and maximum budget inputs for practical product selection.",
  },
  {
    title: "Ingredient information",
    description:
      "Highlights helpful ingredients and ingredients that may not suit the user's preferences.",
  },
  {
    title: "Simple routines",
    description:
      "Organizes skincare into clear morning and night steps that are easier to follow.",
  },
];

export const IMAGE_GUIDELINES = [
  "Use bright and even lighting",
  "Keep the complete face visible",
  "Face the camera directly",
  "Use a neutral expression",
  "Remove glasses when possible",
  "Avoid heavy makeup",
  "Avoid beauty filters",
  "Avoid strong shadows",
  "Upload only one person",
  "Use a clear, recent image",
];

export const IMAGE_UPLOAD_RULES = {
  allowedMimeTypes: ["image/jpeg", "image/png"],
  allowedExtensions: [".jpg", ".jpeg", ".png"],
  maxSizeMb: 5,
  minWidth: 300,
  minHeight: 300,
};

export const IMAGE_QUALITY_STAGES = [
  "Loading image",
  "Checking sharpness",
  "Checking brightness",
  "Checking exposure",
  "Checking contrast",
  "Calculating overall quality",
];

export const FACE_DETECTION_STAGES = [
  "Loading validated image",
  "Locating face",
  "Checking face count",
  "Checking face position",
  "Checking face size",
  "Preparing facial region",
];

export const IMAGE_PREPROCESSING_STAGES = [
  "Loading facial region",
  "Verifying image format",
  "Preparing colour channels",
  "Standardizing image dimensions",
  "Validating model input",
  "Securing processed image",
];

export const SKIN_TYPE_ANALYSIS_STAGES = [
  "Loading prepared facial image",
  "Running skin-type model",
  "Reviewing confidence",
  "Comparing questionnaire responses",
  "Preparing explanation",
];

export const SKIN_CONCERN_ANALYSIS_STAGES = [
  "Loading prepared facial image",
  "Running independent visible-label checks",
  "Applying calibrated thresholds",
  "Comparing relevant questionnaire responses",
  "Reviewing uncertainty and visible prominence",
  "Preparing cautious observations",
];

export const PRODUCT_ELIGIBILITY_STAGES = [
  "Loading trusted profile and analysis context",
  "Checking allergy and ingredient exclusions",
  "Checking budget and location availability",
  "Reviewing age, sensitivity, and fragrance cautions",
  "Checking catalogue data quality",
  "Preparing the eligibility report",
];

export const PRODUCT_RECOMMENDATION_STAGES = [
  "Loading eligible products",
  "Comparing skin-type compatibility",
  "Matching visible skincare concerns",
  "Reviewing ingredient relevance",
  "Checking budget and availability",
  "Ranking category options",
  "Preparing explanations",
];

export const ROUTINE_GENERATION_STAGES = [
  "Loading selected recommendations",
  "Ordering morning categories",
  "Ordering night categories",
  "Separating optional alternatives",
  "Reviewing cautions and limitations",
];

export const FINAL_REPORT_STAGES = [
  "Validating analysis results",
  "Preparing skin-profile summary",
  "Preparing visible observations",
  "Preparing product recommendations",
  "Preparing skincare routine",
  "Adding safety guidance",
  "Generating final report",
];

export const LOADING_STAGES = [
  "Validating image",
  "Detecting facial region",
  "Preparing facial image",
  "Analyzing visible skin features",
  "Generating recommendations",
];

export const DEMO_RESULTS = {
  skinType: "Combination",
  confidence: 87,
  observations: [
    "Moderate visible oiliness in the T-zone",
    "Mild visible pores around the nose",
    "Slightly dry-looking cheek regions",
  ],
  recommendedIngredients: [
    "Niacinamide",
    "Hyaluronic acid",
    "Ceramides",
    "Lightweight non-comedogenic moisturizers",
  ],
  ingredientsToAvoid: [
    "High-fragrance products",
    "Harsh physical scrubs",
    "Very drying alcohol-based toners",
  ],
  products: [
    {
      name: "Gentle Gel Cleanser",
      brand: "DemoDerm",
      category: "Cleanser",
      budget: "Budget friendly",
      availability: "Sample availability only",
      highlights: ["Low fragrance", "Suitable for combination skin"],
    },
    {
      name: "Hydrating Barrier Moisturizer",
      brand: "CareLab",
      category: "Moisturizer",
      budget: "Mid range",
      availability: "Sample availability only",
      highlights: ["Ceramides", "Lightweight texture"],
    },
    {
      name: "Daily Mineral Sunscreen SPF 30",
      brand: "SunKind",
      category: "Sunscreen",
      budget: "Mid range",
      availability: "Sample availability only",
      highlights: ["Broad spectrum", "No heavy finish"],
    },
  ],
  morningRoutine: [
    "Cleanse with a gentle gel cleanser",
    "Apply a lightweight hydrating serum",
    "Use a barrier-supporting moisturizer",
    "Finish with broad-spectrum sunscreen",
  ],
  nightRoutine: [
    "Cleanse to remove sunscreen and impurities",
    "Apply a calming hydrating product",
    "Use moisturizer on dry-looking areas",
    "Avoid strong exfoliation without professional guidance",
  ],
};

export const SAMPLE_REPORTS = [
  {
    id: "RPT-001",
    date: "2026-08-01",
    skinType: "Combination",
    confidence: 87,
    observation: "Moderate visible oiliness in the T-zone",
  },
  {
    id: "RPT-002",
    date: "2026-07-24",
    skinType: "Dry",
    confidence: 81,
    observation: "Slightly dry-looking cheek regions",
  },
  {
    id: "RPT-003",
    date: "2026-07-12",
    skinType: "Oily",
    confidence: 84,
    observation: "Visible shine around forehead and nose",
  },
];
