import type { DashboardDataset } from '../types';
import { analyticsBrain } from './analyticsBrain';
import { generatedDashboardData } from './generatedData';

export async function loadDashboardData(): Promise<DashboardDataset> {
  return { ...generatedDashboardData, analyticsBrain };
}
