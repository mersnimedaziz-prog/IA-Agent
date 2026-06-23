import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { RoleSummaryComponent } from './role-summary.component';
import { MonthlyApiService } from '../../services/monthly-api.service';

describe('RoleSummaryComponent', () => {
  let component: RoleSummaryComponent;
  let fixture: ComponentFixture<RoleSummaryComponent>;

  const monthlyApiServiceMock = {
    getMonthlyUploads: vi.fn().mockReturnValue(of([{upload_id: 'test_id', original_filename: 'test.xlsx'}])),
    getMonthlyPivotByUpload: vi.fn().mockReturnValue(of({}))
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RoleSummaryComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: MonthlyApiService, useValue: monthlyApiServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RoleSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create role summary component', () => {
    expect(component).toBeTruthy();
  });
});
