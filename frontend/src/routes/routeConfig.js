import { lazy } from "react";

const FaceScanPage = lazy(() => import("../pages/FaceScanPage"));
const FaceDetectionPage = lazy(() => import("../pages/FaceDetectionPage"));
const HomePage = lazy(() => import("../pages/HomePage"));
const ImagePreprocessingPage = lazy(() => import("../pages/ImagePreprocessingPage"));
const ImageQualityCheckPage = lazy(() => import("../pages/ImageQualityCheckPage"));
const LoginPage = lazy(() => import("../pages/LoginPage"));
const RegisterPage = lazy(() => import("../pages/RegisterPage"));
const ReportsPage = lazy(() => import("../pages/ReportsPage"));
const SkinProfilePage = lazy(() => import("../pages/SkinProfilePage"));
const SkinTypeAnalysisPage = lazy(() => import("../pages/SkinTypeAnalysisPage"));
const SkinConcernAnalysisPage = lazy(() => import("../pages/SkinConcernAnalysisPage"));
const ProductDiscoveryPage = lazy(() => import("../pages/ProductDiscoveryPage"));
const ProductsPage = lazy(() => import("../pages/ProductsPage"));
const ProductDetailPage = lazy(() => import("../pages/ProductDetailPage"));
const IngredientsPage = lazy(() => import("../pages/IngredientsPage"));
const IngredientDetailPage = lazy(() => import("../pages/IngredientDetailPage"));
const ProductEligibilityPage = lazy(() => import("../pages/ProductEligibilityPage"));
const ProductRecommendationsPage = lazy(() => import("../pages/ProductRecommendationsPage"));
const SkincareRoutinePage = lazy(() => import("../pages/SkincareRoutinePage"));
const FinalReportGenerationPage = lazy(() => import("../pages/FinalReportGenerationPage"));
const FinalReportDashboardPage = lazy(() => import("../pages/FinalReportDashboardPage"));
const FinalReportPrintPage = lazy(() => import("../pages/FinalReportPrintPage"));
const FeedbackPage = lazy(() => import("../pages/FeedbackPage"));
const FeedbackHistoryPage = lazy(() => import("../pages/FeedbackHistoryPage"));
const FeedbackDetailPage = lazy(() => import("../pages/FeedbackDetailPage"));

export const routeConfig = [
  {
    path: "/",
    component: HomePage,
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
