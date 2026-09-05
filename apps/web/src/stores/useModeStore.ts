import { create } from "zustand";

export type ProjectWizardMode = "auto" | "advanced" | "bulk";

interface ModeStoreState {
  mode: ProjectWizardMode;
  setMode: (mode: ProjectWizardMode) => void;
  modeChangeHandler: ((mode: ProjectWizardMode) => boolean | void) | null;
  registerModeChangeHandler: (handler: ((mode: ProjectWizardMode) => boolean | void) | null) => void;
}

export const useModeStore = create<ModeStoreState>((set, get) => ({
  mode: "auto",
  setMode: (mode) => {
    const handler = get().modeChangeHandler;
    if (handler) {
      const allowed = handler(mode);
      if (allowed === false) return;
    }
    set({ mode });
  },
  modeChangeHandler: null,
  registerModeChangeHandler: (handler) => set({ modeChangeHandler: handler }),
}));
