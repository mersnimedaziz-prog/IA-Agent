import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { DailySummaryComponent } from './daily-summary.component';
import { ApiService } from '../../api.service';

describe('DailySummaryComponent', () => {
  let component: DailySummaryComponent;
  let fixture: ComponentFixture<DailySummaryComponent>;

  const apiServiceMock = {
    getMonthlyUploads: vi.fn().mockReturnValue(of([{upload_id: 'test_id', original_filename: 'test.xlsx'}])),
    getMonthlyPivotByUpload: vi.fn().mockReturnValue(
      of({
        daily_summary: [
          {
            Date: '2026-05-04',
            Total_Hours: 12,
            Total_MD: 1.5,
            Activities: [
              'Build customer information form',
              'Create customer validation endpoint'
            ],
            Activities_Text: 'Build customer information form | Create customer validation endpoint'
          }
        ]
      })
    )
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        DailySummaryComponent
      ],
      providers: [
        {
          provide: ApiService,
          useValue: apiServiceMock
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DailySummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create daily summary component', () => {
    expect(component).toBeTruthy();
  });

  it('should calculate totals from daily summary', () => {
    component.dailySummary = [
      {
        Total_Hours: 8,
        Total_MD: 1
      },
      {
        Total_Hours: 4,
        Total_MD: 0.5
      }
    ];

    component.calculateTotals();

    expect(component.totalHours).toBe(12);
    expect(component.totalMd).toBe(1.5);
    expect(component.totalDays).toBe(2);
  });
});