import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { AppSettings, ProviderProfile } from '../shared/types';
import { createDemoApi } from './demo';

export const IS_DEMO = new URLSearchParams(window.location.search).get('demo') === '1';
export const desk = IS_DEMO ? createDemoApi() : window.desk;
export const useBootstrap = () =>
  useQuery({ queryKey: ['bootstrap'], queryFn: () => desk.bootstrap(), staleTime: 30000 });
export function useSessions(seconds = 30, scanOnStart = true) {
  const query = useQueryClient();
  return useQuery({
    queryKey: ['sessions'],
    queryFn: () => desk.sessions(true),
    enabled: scanOnStart || !!query.getQueryData(['sessions']),
    refetchInterval: seconds > 0 ? seconds * 1000 : false,
  });
}
export const useTranscript = (id: string | undefined, updatedAt?: string) =>
  useQuery({
    queryKey: ['transcript', id, updatedAt],
    queryFn: () => desk.transcript(id!),
    enabled: !!id,
  });
export const useSkills = () => useQuery({ queryKey: ['skills'], queryFn: () => desk.skills() });
export const useSkill = (id: string | undefined) =>
  useQuery({ queryKey: ['skill', id], queryFn: () => desk.readSkill(id!), enabled: !!id });
export const useConfigs = () => useQuery({ queryKey: ['configs'], queryFn: () => desk.configs() });
export const useTerminals = () =>
  useQuery({ queryKey: ['terminals'], queryFn: () => desk.terminals(), refetchInterval: 5000 });
export const useCatalog = (id: string, enabled: boolean) =>
  useQuery({
    queryKey: ['catalog', id],
    queryFn: () => desk.models(id),
    enabled,
    staleTime: 60000,
    retry: false,
  });
export function useSaveSettings() {
  const query = useQueryClient();
  return useMutation({
    mutationFn: (settings: AppSettings) => desk.saveSettings(settings),
    onSuccess: async () => {
      await Promise.all(
        ['bootstrap', 'skills', 'configs', 'sessions'].map((key) =>
          query.invalidateQueries({ queryKey: [key] }),
        ),
      );
    },
  });
}
export function useSaveProfile() {
  const query = useQueryClient();
  return useMutation({
    mutationFn: (profile: ProviderProfile) => desk.saveProfile(profile),
    onSuccess: async (profile) => {
      await Promise.all([
        query.invalidateQueries({ queryKey: ['bootstrap'] }),
        query.invalidateQueries({ queryKey: ['configs'] }),
        query.invalidateQueries({ queryKey: ['catalog', profile.id] }),
      ]);
    },
  });
}
