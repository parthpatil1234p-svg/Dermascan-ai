import { lazy } from "react";

/**
 * lazyWithRetry - Resilient chunk loader for SPA deployments
 * If a new build is deployed to Vercel and an old browser tab requests a replaced chunk hash,
 * this automatically refreshes the page once to load the newest manifest without throwing an uncaught error.
 */
function lazyWithRetry(componentImport) {
  return lazy(async () => {
    const key = `chunk_retry_${window.location.pathname}`;
    const isRetrying = window.sessionStorage.getItem(key);
    try {
      const component = await componentImport();
      if (isRetrying) {
        window.sessionStorage.removeItem(key);
      }
      return component;
    } catch (error) {
      if (!isRetrying) {
        window.sessionStorage.setItem(key, "true");
        window.location.reload();
        return new Promise(() => {}); // Pause until reload
      }
      throw error;
    }
  });
}

const FaceScanPage = lazyWithRetry(() => import("../pages/FaceScanPage"));
const FaceDetectionPage = lazyWithRetry(() => import("../pages/FaceDetectionPage"));
const HomePage = lazyWithRetry(() => import("../pages/HomePage"));
const ImagePreprocessingPage = lazyWithRetry(() => import("../pages/ImagePreprocessingPage"));
const ImageQualityCheckPage = lazyWithRetry(() => import("../pages/ImageQualityCheckPage"));
const LoginPage = lazyWithRetry(() => import("../pages/LoginPage"));
const RegisterPage = lazyWithRetry(() => import("../pages/RegisterPage"));
const ReportsPage = lazyWithRetry(() => import("../pages/ReportsPage"));
const SkinProfilePage = lazyWithRetry(() => import("../pages/SkinProfilePage"));
const SkinTypeAnalysisPage = lazyWithRetry(() => import("../pages/SkinTypeAnalysisPage"));
const SkinConcernAnalysisPage = lazyWithRetry(() => import("../pages/SkinConcernAnalysisPage"));
const ProductDiscoveryPage = lazyWithRetry(() => import("../pages/ProductDiscoveryPage"));
const ProductsPage = lazyWithRetry(() => import("../pages/ProductsPage"));
const ProductDetailPage = lazyWithRetry(() => import("../pages/ProductDetailPage"));
const IngredientsPage = lazyWithRetry(() => import("../pages/IngredientsPage"));
const IngredientDetailPage = lazyWithRetry(() => import("../pages/IngredientDetailPage"));
const IngredientCheckerPage = lazyWithRetry(() => import("../pages/IngredientCheckerPage"));
const ProductEligibilityPage = lazyWithRetry(() => import("../pages/ProductEligibilityPage"));
const ProductRecommendationsPage = lazyWithRetry(() => import("../pages/ProductRecommendationsPage"));
const SkincareRoutinePage = lazyWithRetry(() => import("../pages/SkincareRoutinePage"));
const FinalReportGenerationPage = lazyWithRetry(() => import("../pages/FinalReportGenerationPage"));
const FinalReportDashboardPage = lazyWithRetry(() => import("../pages/FinalReportDashboardPage"));
const FinalReportPrintPage = lazyWithRetry(() => import("../pages/FinalReportPrintPage"));
const FeedbackPage = lazyWithRetry(() => import("../pages/FeedbackPage"));
const FeedbackHistoryPage = lazyWithRetry(() => import("../pages/FeedbackHistoryPage"));
const FeedbackDetailPage = lazyWithRetry(() => import("../pages/FeedbackDetailPage"));


export const routeConfig = [
  {
    path: "/",
    component: HomePage,
  },
  {
    path: "/ingredient-checker",
    component: IngredientCheckerPage,
  },
  {
    path: "/login",
    component: LoginPage,
    publicOnly: true,
  },
  {
    path: "/register",
    component: RegisterPage,
    publicOnly: true,
  },
  {
    path: "/products",
    component: ProductsPage,
  },
  {
    path: "/products/:productId",
    component: ProductDetailPage,
  },
  {
    path: "/ingredients",
    component: IngredientsPage,
  },
  {
    path: "/ingredients/:ingredientId",
    component: IngredientDetailPage,
  },
  {
    path: "/skin-profile",
    component: SkinProfilePage,
    protected: true,
  },
  {
    path: "/face-scan",
    component: FaceScanPage,
    protected: true,
    requiresProfile: true,
  },
  {
    path: "/image-quality-check",
    component: ImageQualityCheckPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
  },
  {
    path: "/face-detection",
    component: FaceDetectionPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
  },
  {
    path: "/image-preprocessing",
    component: ImagePreprocessingPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
  },
  {
    path: "/skin-type-analysis",
    component: SkinTypeAnalysisPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
  },
  {
    path: "/skin-concern-analysis",
    component: SkinConcernAnalysisPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
    requiresSkinType: true,
  },
  {
    path: "/product-eligibility",
    component: ProductEligibilityPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
    requiresSkinType: true,
    requiresConcerns: true,
  },
  {
    path: "/product-recommendations",
    component: ProductRecommendationsPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
    requiresSkinType: true,
    requiresConcerns: true,
    requiresEligibility: true,
  },
  {
    path: "/skincare-routine",
    component: SkincareRoutinePage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
    requiresSkinType: true,
    requiresConcerns: true,
    requiresEligibility: true,
    requiresRecommendation: true,
  },
  {
    path: "/final-report",
    component: FinalReportGenerationPage,
    protected: true,
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
  },
  {
    path: "/reports/:finalReportId/print",
    component: FinalReportPrintPage,
    protected: true,
  },
  {
    path: "/reports/:finalReportId",
    component: FinalReportDashboardPage,
    protected: true,
  },
  {
    path: "/product-discovery",
    component: ProductDiscoveryPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
    requiresSkinType: true,
    requiresConcerns: true,
  },
  {
    path: "/analysis-loading",
    component: SkinTypeAnalysisPage,
    protected: true,
    requiresProfile: true,
    requiresUpload: true,
    requiresQuality: true,
    requiresFaceDetection: true,
    requiresPreprocessing: true,
  },
  {
    path: "/results",
    component: FinalReportGenerationPage,
    protected: true,
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
  },
  {
    path: "/reports",
    component: ReportsPage,
    protected: true,
  },
  {
    path: "/feedback",
    component: FeedbackPage,
    protected: true,
  },
  {
    path: "/feedback/history",
    component: FeedbackHistoryPage,
    protected: true,
  },
  {
    path: "/feedback/:feedbackId",
    component: FeedbackDetailPage,
    protected: true,
  },
];
