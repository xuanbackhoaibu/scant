import { create } from "zustand";
import { api } from "@/lib/api";

export interface Project {
  id: string;
  user_id: string;
  name: string;
  type: string;
  description?: string;
  settings_json: Record<string, any>;
  topic_details_json: Record<string, any>;
  created_at: string;
  updated_at: string;
  files?: any[];
  reports_count?: number;
  sources_count?: number;
}

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  isLoading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  createProject: (data: any) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await api.projects.list();
      set({ projects, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || "Failed to load projects", isLoading: false });
    }
  },

  fetchProject: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const currentProject = await api.projects.get(id);
      set({ currentProject, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || "Failed to load project", isLoading: false });
    }
  },

  createProject: async (data: any) => {
    set({ isLoading: true, error: null });
    try {
      const project = await api.projects.create(data);
      set((state) => ({
        projects: [project, ...state.projects],
        currentProject: project,
        isLoading: false,
      }));
      return project;
    } catch (err: any) {
      set({ error: err.message || "Failed to create project", isLoading: false });
      throw err;
    }
  },

  deleteProject: async (id: string) => {
    try {
      await api.projects.delete(id);
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id),
        currentProject: state.currentProject?.id === id ? null : state.currentProject,
      }));
    } catch (err: any) {
      set({ error: err.message || "Failed to delete project" });
      throw err;
    }
  },
}));
