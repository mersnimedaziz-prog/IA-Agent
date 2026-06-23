import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { MonthlyTrackingComponent } from './monthly-tracking.component';
import { MonthlyApiService } from '../../services/monthly-api.service';
import { DashboardApiService } from '../../services/dashboard-api.service';

describe('MonthlyTrackingComponent', () => {
  let component: MonthlyTrackingComponent;
  let fixture: ComponentFixture<MonthlyTrackingComponent>;

  const monthlyApiServiceMock = {
    uploadMonthlyFile: vi.fn().mockReturnValue(of({})),
    saveMonthlyTarget: vi.fn().mockReturnValue(of({})),
    calculateMonthlyKpi: vi.fn().mockReturnValue(of({})),
    getMonthlyComparison: vi.fn().mockReturnValue(of([])),
    getMonthlyResults: vi.fn().mockReturnValue(of([])),
    getMonthlyTargets: vi.fn().mockReturnValue(of([]))
  };

  const dashboardApiServiceMock = {
    getMonthlyResults: vi.fn().mockReturnValue(of([]))
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MonthlyTrackingComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: MonthlyApiService, useValue: monthlyApiServiceMock },
        { provide: DashboardApiService, useValue: dashboardApiServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MonthlyTrackingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create monthly tracking component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize date range from selected month', () => {
    component.monthlyMonth = '2026-05';
    component.updateMonthlyDateRangeFromMonth();
    expect(component.monthlyStartDate).toBe('2026-05-01');
    expect(component.monthlyEndDate).toBe('2026-05-31');
  });
});
