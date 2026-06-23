import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { SummaryDashboardComponent } from './summary-dashboard.component';
import { DashboardApiService } from '../../services/dashboard-api.service';

describe('SummaryDashboardComponent', () => {
  let component: SummaryDashboardComponent;
  let fixture: ComponentFixture<SummaryDashboardComponent>;

  const dashboardApiServiceMock = {
    getMonthlyResults: vi.fn().mockReturnValue(of([]))
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SummaryDashboardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: DashboardApiService, useValue: dashboardApiServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SummaryDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create summary dashboard component', () => {
    expect(component).toBeTruthy();
  });
});
