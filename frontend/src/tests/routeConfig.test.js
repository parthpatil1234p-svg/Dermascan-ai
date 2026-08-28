import { describe, expect, it } from "vitest";
import { routeConfig } from "../routes/routeConfig";

describe("workflow route contracts", () => {
  it("keeps private analysis routes protected", () => {
    const routes = new Map(routeConfig.map((route) => [route.path, route]));
    for (const path of [
      "/skin-profile",
      "/face-scan",
      "/image-quality-check",
      "/face-detection",
      "/image-preprocessing",
      "/skin-type-analysis",
      "/skin-concern-analysis",
      "/product-eligibility",
      "/product-recommendations",
      "/skincare-routine",
      "/final-report",
      "/reports",
      "/feedback",
    ]) {
      expect(routes.get(path)?.protected, path).toBe(true);
    }
  });

  it("requires every prior stage before final report generation", () => {
    const finalRoute = routeConfig.find((route) => route.path === "/final-report");
    expect(finalRoute).toMatchObject({
      requiresProfile: true,
      requiresUpload: true,
      requiresQuality: true,
      requiresFaceDetection: true,
      requiresPreprocessing: true,
      requiresSkinType: true,
      requiresConcerns: true,
      requiresEligibility: true,
      requiresRecommendation: true,
      requiresRoutine: true,
    });
  });
});

