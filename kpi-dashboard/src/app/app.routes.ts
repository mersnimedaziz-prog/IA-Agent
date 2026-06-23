import { Routes } from '@angular/router';

import { HomeComponent } from './pages/home/home.component';
import { MonthlyTrackingComponent } from './pages/monthly-tracking/monthly-tracking.component';
import { DailySummaryComponent } from './pages/daily-summary/daily-summary.component';
import { RoleSummaryComponent } from './pages/role-summary/role-summary.component';
import { AuthorSummaryComponent } from './pages/author-summary/author-summary.component';
import { SummaryDashboardComponent } from './pages/summary-dashboard/summary-dashboard.component';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    component: HomeComponent
  },
  {
    path: 'monthly-tracking',
    component: MonthlyTrackingComponent
  },
  {
    path: 'daily-summary',
    component: DailySummaryComponent
  },
  {
    path: 'role-summary',
    component: RoleSummaryComponent
  },
  {
    path: 'author-summary',
    component: AuthorSummaryComponent
  },
  {
    path: '**',
    redirectTo: 'home'
  }
];