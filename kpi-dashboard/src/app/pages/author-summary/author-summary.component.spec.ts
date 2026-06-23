import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AuthorSummaryComponent } from './author-summary.component';
import { MonthlyApiService } from '../../services/monthly-api.service';

describe('AuthorSummaryComponent', () => {
  let component: AuthorSummaryComponent;
  let fixture: ComponentFixture<AuthorSummaryComponent>;

  const monthlyApiServiceMock = {
    getMonthlyUploads: vi.fn().mockReturnValue(of([{upload_id: 'test_id', original_filename: 'test.xlsx'}])),
    getMonthlyPivotByUpload: vi.fn().mockReturnValue(
      of({
        by_author: [
          { Author: 'Aziz', Time_Hours: 20.5, Total_MD: 2.56 },
          { Author: 'Sami', Time_Hours: 24, Total_MD: 3 }
        ],
        author_work_summary: []
      })
    )
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuthorSummaryComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: MonthlyApiService, useValue: monthlyApiServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AuthorSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create author summary component', () => {
    expect(component).toBeTruthy();
  });
});
