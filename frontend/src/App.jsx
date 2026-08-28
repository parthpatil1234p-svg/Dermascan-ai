import { Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import ProfileRequiredRoute from "./components/ProfileRequiredRoute";
import FaceDetectionRequiredRoute from "./components/FaceDetectionRequiredRoute";
import PreprocessingRequiredRoute from "./components/PreprocessingRequiredRoute";
import QualityRequiredRoute from "./components/QualityRequiredRoute";
import UploadRequiredRoute from "./components/UploadRequiredRoute";
import SkinTypeRequiredRoute from "./components/SkinTypeRequiredRoute";
import ConcernRequiredRoute from "./components/ConcernRequiredRoute";
import EligibilityRequiredRoute from "./components/EligibilityRequiredRoute";
import RecommendationRequiredRoute from "./components/RecommendationRequiredRoute";
import RoutineRequiredRoute from "./components/RoutineRequiredRoute";
import PublicOnlyRoute from "./components/PublicOnlyRoute";
import NotFoundPage from "./pages/NotFoundPage";
import RouteLoadingScreen from "./components/RouteLoadingScreen";
import { routeConfig } from "./routes/routeConfig";

export default function App() {
  return (
    <Suspense fallback={<RouteLoadingScreen />}>
    <Routes>
      <Route element={<AppLayout />}>
        {routeConfig.map((route) => {
          const PageComponent = route.component;
          let element = <PageComponent />;

          if (route.requiresRoutine) {
            element = <RoutineRequiredRoute>{element}</RoutineRequiredRoute>;
          }

          if (route.requiresRecommendation) {
            element = <RecommendationRequiredRoute>{element}</RecommendationRequiredRoute>;
          }

          if (route.requiresEligibility) {
            element = <EligibilityRequiredRoute>{element}</EligibilityRequiredRoute>;
          }

          if (route.requiresConcerns) {
            element = <ConcernRequiredRoute>{element}</ConcernRequiredRoute>;
          }

          if (route.requiresSkinType) {
            element = <SkinTypeRequiredRoute>{element}</SkinTypeRequiredRoute>;
          }

          if (route.requiresPreprocessing) {
            element = (
              <PreprocessingRequiredRoute>{element}</PreprocessingRequiredRoute>
            );
          }

          if (route.requiresFaceDetection) {
            element = <FaceDetectionRequiredRoute>{element}</FaceDetectionRequiredRoute>;
          }

          if (route.requiresQuality) {
            element = <QualityRequiredRoute>{element}</QualityRequiredRoute>;
          }

          if (route.requiresUpload) {
            element = <UploadRequiredRoute>{element}</UploadRequiredRoute>;
          }

          if (route.requiresProfile) {
            element = <ProfileRequiredRoute>{element}</ProfileRequiredRoute>;
          }

          if (route.protected) {
            element = <ProtectedRoute>{element}</ProtectedRoute>;
          }

          if (route.publicOnly) {
            element = <PublicOnlyRoute>{element}</PublicOnlyRoute>;
          }

          return (
            <Route
              key={route.path}
              path={route.path}
              element={element}
            />
          );
        })}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
    </Suspense>
  );
}
