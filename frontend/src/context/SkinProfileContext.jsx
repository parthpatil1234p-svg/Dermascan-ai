import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useAuth } from "./AuthContext";
import {
  createSkinProfile,
  deleteSkinProfile,
  getSkinProfile,
  updateSkinProfile,
} from "../services/skinProfileService";

const SkinProfileContext = createContext(null);

export function SkinProfileProvider({ children }) {
  const { isAuthenticated, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [checkedUserId, setCheckedUserId] = useState("");

  const loadProfile = useCallback(async () => {
    if (!isAuthenticated) {
      setProfile(null);
      setError("");
      setCheckedUserId("");
      setIsLoading(false);
      return null;
    }

    setIsLoading(true);
    setError("");
    try {
      const savedProfile = await getSkinProfile();
      setProfile(savedProfile);
      return savedProfile;
    } catch {
      setError("Unable to load your skin profile.");
      return null;
    } finally {
      setCheckedUserId(user?.id || "");
      setIsLoading(false);
    }
  }, [isAuthenticated, user?.id]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile, user?.id]);

  const saveProfile = useCallback(async (values) => {
    if (isSaving) {
      return profile;
    }

    setIsSaving(true);
    setError("");
    try {
      const savedProfile = profile
        ? await updateSkinProfile(values)
        : await createSkinProfile(values);
      setProfile(savedProfile);
      return savedProfile;
    } finally {
      setIsSaving(false);
    }
  }, [isSaving, profile]);

  const removeProfile = useCallback(async () => {
    setIsSaving(true);
    try {
      const response = await deleteSkinProfile();
      setProfile(null);
      return response;
    } finally {
      setIsSaving(false);
    }
  }, []);

  const value = useMemo(
    () => ({
      profile,
      isLoading,
      isSaving,
      error,
      hasProfile: Boolean(profile),
      isComplete: Boolean(profile?.is_complete),
      isInitialized: !isAuthenticated || checkedUserId === user?.id,
      loadProfile,
      saveProfile,
      deleteProfile: removeProfile,
    }),
    [
      profile,
      isLoading,
      isSaving,
      error,
      isAuthenticated,
      checkedUserId,
      user?.id,
      loadProfile,
      saveProfile,
      removeProfile,
    ],
  );

  return (
    <SkinProfileContext.Provider value={value}>
      {children}
    </SkinProfileContext.Provider>
  );
}

export function useSkinProfile() {
  const context = useContext(SkinProfileContext);
  if (!context) {
    throw new Error("useSkinProfile must be used inside SkinProfileProvider");
  }
  return context;
}
