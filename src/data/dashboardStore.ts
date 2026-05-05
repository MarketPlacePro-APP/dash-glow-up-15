import type { DashboardDataset } from '../types';
import { generatedDashboardData } from './generatedData';

export async function loadDashboardData(): Promise<DashboardDataset> {
  return generatedDashboardData;
}
