import type { SourceMeta } from '@/types';

export type ExpoStrip = {
  bus: number;
  guests: number;
  utl: number;
  tlwb: number;
  keyspire: number;
  total: number;
  sourceMode: 'static-export';
  sourcePostedAt: string;
  lastFetchedAt: string;
  source: SourceMeta;
};

// Source: Slack #expo post, May Investor Expo as of 3:03pm MST 04/29/2026.
// Fetched via Slack/API-backed local export during review refresh on 2026-05-05T14:09:01Z.
export const expoStrip: ExpoStrip = {
  bus: 131,
  guests: 53,
  utl: 42,
  tlwb: 88,
  keyspire: 1,
  total: 184,
  sourceMode: 'static-export',
  sourcePostedAt: '2026-04-29T15:03:00-06:00',
  lastFetchedAt: '2026-05-05T14:09:01Z',
  source: {
    sourceKey: 'slack_expo_may_investor_expo_2026_04_29',
    sourceName: 'Slack #expo — May Investor Expo count post',
    sourceUrl: 'slack://channel/expo/post/2026-04-29T15:04-06:00',
    fetchedAt: '2026-05-05T14:09:01Z',
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'expo_strip_static_export',
    caveat: 'Static Slack export: latest visible #expo count post was 2026-04-29 15:04 MDT; stale until a newer #expo count is fetched.'
  }
};
