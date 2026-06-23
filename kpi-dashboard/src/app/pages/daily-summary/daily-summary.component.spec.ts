import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { DailySummaryComponent } from './daily-summary.component';
import { MonthlyApiService } from '../../services/monthly-api.service';

describe('DailySummaryComponent', () => {
  let component: DailySummaryComponent;
  let fixture: ComponentFixture<DailySummaryComponent>;

  const monthlyApiServiceMock = {
    getMonthlyUploads: vi.fn().mockReturnValue(of([{upload_id: 'test_id', original_filename: 'test.xlsx'}])),
    getMonthlyPivotByUpload: vi.fn().mockReturnValue(of({}))
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DailySummaryComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: MonthlyApiService, useValue: monthlyApiServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DailySummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create daily summary component', () => {
    expect(component).toBeTruthy();
  });
});
