import type { SourceMeta } from '@/types';

export type ExpoStrip = {
  bus: number | null;
  guests: number | null;
  utl: number | null;
  tlwb: number | null;
  keyspire: number | null;
  total: number | null;
  status: 'next-count-needed' | 'current';
  label: string;
  sourceMode: 'post-event-reset' | 'slack-count';
  sourcePostedAt: string;
  lastFetchedAt: string;
  source: SourceMeta;
};

// Source: Slack #expo current Investor Expo count parsed from the latest checked post.
export const expoStrip: ExpoStrip = {
  bus: 129,
  guests: 72,
  utl: 7,
  tlwb: 95,
  keyspire: 0,
  total: 201,
  status: 'current',
  label: 'August Investor Expo',
  sourceMode: 'slack-count',
  sourcePostedAt: '2026-07-22T14:55:54.888579-06:00',
  lastFetchedAt: '2026-08-29T06:04:55.955799-06:00',
  source: {
    sourceKey: 'slack_expo_current_2026_08_29',
    sourceName: 'Slack #expo — current Investor Expo count',
    sourceUrl: 'slack://channel/expo/posts/2026-07-22T14:55:54.888579-06:00',
    fetchedAt: '2026-08-29T06:04:55.955799-06:00',
    trustLevel: 'operational',
    sampleData: false,
    sourceRole: 'expo_strip_current_count',
    caveat: 'August Investor Expo count parsed from live #expo at 2026-07-22T14:55:54.888579-06:00.'
  }
};
