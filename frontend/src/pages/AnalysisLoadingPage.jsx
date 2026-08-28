import { ArrowLeft, FileCheck2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingIndicator from "../components/LoadingIndicator";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import { LOADING_STAGES, ROUTES } from "../constants/appContent";

export default function AnalysisLoadingPage() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setProgress((current) => Math.min(current + 4, 100));
    }, 220);

    return () => window.clearInterval(intervalId);
  }, []);

  const currentStageIndex = useMemo(
    () => Math.min(Math.floor(progress / 20), LOADING_STAGES.length - 1),
    [progress],
  );

  const isComplete = progress >= 100;

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Demonstration only"
        title="Preparing demonstration analysis"
        description="This loading sequence is a temporary user-interface simulation. It does not perform real face detection or AI analysis."
      />

      <div className="mx-auto max-w-3xl">
        <LoadingIndicator
          stages={LOADING_STAGES}
          currentStageIndex={currentStageIndex}
          progress={progress}
        />

        <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
          <SecondaryButton
            type="button"
            icon={ArrowLeft}
            onClick={() => navigate(ROUTES.faceScan)}
          >
            Back to Upload
          </SecondaryButton>
          <PrimaryButton
            type="button"
            icon={FileCheck2}
            disabled={!isComplete}
            onClick={() => navigate(ROUTES.results)}
          >
            View Demonstration Results
          </PrimaryButton>
        </div>
      </div>
    </section>
  );
}
