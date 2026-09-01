import { Outlet } from "react-router-dom";
import Footer from "../components/Footer";
import Navbar from "../components/Navbar";
import WelcomeModal from "../components/WelcomeModal";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-clinic-50">
      <Navbar />
      <main id="main-content" className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <WelcomeModal />
    </div>
  );
}


