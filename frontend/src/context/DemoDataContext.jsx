import { createContext, useContext, useEffect, useMemo } from "react";
import { DEMO_RESULTS } from "../constants/appContent";

const DemoDataContext = createContext(null);

export function DemoDataProvider({ children }) {
  useEffect(() => {
    window.localStorage.removeItem("dermascan_skin_profile");
    window.localStorage.removeItem("dermascan_registration_profile");
  }, []);

  const value = useMemo(
    () => ({
      demoResults: DEMO_RESULTS,
    }),
    [],
  );

  return (
    <DemoDataContext.Provider value={value}>
      {children}
    </DemoDataContext.Provider>
  );
}

export function useDemoData() {
  const context = useContext(DemoDataContext);

  if (!context) {
    throw new Error("useDemoData must be used inside DemoDataProvider");
  }

  return context;
}
