import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { MonthlyTrackingComponent } from './monthly-tracking.component';
import { ApiService } from '../../api.service';

describe('MonthlyTrackingComponent', () => {
  let component: MonthlyTrackingComponent;
  let fixture: ComponentFixture<MonthlyTrackingComponent>;

  const apiServiceMock = {
    uploadMonthlyFile: vi.fn().mockReturnValue(
      of({
        message: 'Fichier mensuel importé avec succès.'
      })
    ),

    saveMonthlyTarget: vi.fn().mockReturnValue(
      of({
        message: 'Target sauvegardé.'
      })
    ),

    calculateMonthlyKpi: vi.fn().mockReturnValue(
      of({
        result: {
          month: '2026-05',
          value: 62,
          unit: 'hours',
          total_md: 7.75
        },
        target: {
          target_value: 60,
          unit: 'hours'
        },
        comparison: {
          gap: 2,
          achieved: true
        }
      })
    )
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        MonthlyTrackingComponent
      ],
      providers: [
        {
          provide: ApiService,
          useValue: apiServiceMock
        }
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