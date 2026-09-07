import { Outlet } from "react-router-dom";
import Footer from "../components/Footer";
import Navbar from "../components/Navbar";
import WelcomeModal from "../components/WelcomeModal";
import AIChatWidget from "../components/AIChatWidget";
import ThreeDimensionMeshCanvas from "../components/ThreeDimensionMeshCanvas";

export default function AppLayout() {
  return (
    <div className="relative flex min-h-screen flex-col bg-slate-950 text-slate-100 selection:bg-emerald-500 selection:text-slate-950 overflow-x-hidden">
      {/* Subtle global 3D ambient mesh */}
      <ThreeDimensionMeshCanvas mode="ambient" nodeCount={32} className="opacity-25" />
      <div className="cyber-grid pointer-events-none fixed inset-0 opacity-20" aria-hidden="true" />

      <Navbar />
      <main id="main-content" className="relative z-10 flex-1">
        <Outlet />
      </main>
      <Footer />
      <WelcomeModal />
      <AIChatWidget />
    </div>
  );
}



