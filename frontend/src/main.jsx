import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider } from "./context/AuthContext";
import { DemoDataProvider } from "./context/DemoDataContext";
import { SkinProfileProvider } from "./context/SkinProfileContext";
import { UploadProvider } from "./context/UploadContext";
import { ImageQualityProvider } from "./context/ImageQualityContext";
import { FaceDetectionProvider } from "./context/FaceDetectionContext";
import { ImagePreprocessingProvider } from "./context/ImagePreprocessingContext";
import { SkinTypeProvider } from "./context/SkinTypeContext";
import { SkinConcernProvider } from "./context/SkinConcernContext";
import { ProductEligibilityProvider } from "./context/ProductEligibilityContext";
import { ProductRecommendationProvider } from "./context/ProductRecommendationContext";
import { SkincareRoutineProvider } from "./context/SkincareRoutineContext";
import { FinalReportProvider } from "./context/FinalReportContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <ErrorBoundary>
      <AuthProvider>
        <SkinProfileProvider>
          <UploadProvider>
            <ImageQualityProvider>
              <FaceDetectionProvider>
                <ImagePreprocessingProvider>
                  <SkinTypeProvider>
                    <SkinConcernProvider>
                      <ProductEligibilityProvider>
                        <ProductRecommendationProvider>
                          <SkincareRoutineProvider>
                            <FinalReportProvider>
                              <DemoDataProvider>
                                <App />
                              </DemoDataProvider>
                            </FinalReportProvider>
                          </SkincareRoutineProvider>
                        </ProductRecommendationProvider>
                      </ProductEligibilityProvider>
                    </SkinConcernProvider>
                  </SkinTypeProvider>
                </ImagePreprocessingProvider>
              </FaceDetectionProvider>
            </ImageQualityProvider>
          </UploadProvider>
        </SkinProfileProvider>
      </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>,
);
