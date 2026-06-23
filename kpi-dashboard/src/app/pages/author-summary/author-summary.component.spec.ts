import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AuthorSummaryComponent } from './author-summary.component';
import { ApiService } from '../../api.service';

describe('AuthorSummaryComponent', () => {
  let component: AuthorSummaryComponent;
  let fixture: ComponentFixture<AuthorSummaryComponent>;

  const apiServiceMock = {
    getMonthlyUploads: vi.fn().mockReturnValue(of([{upload_id: 'test_id', original_filename: 'test.xlsx'}])),
    getMonthlyPivotByUpload: vi.fn().mockReturnValue(
      of({
        by_author: [
          {
            Author: 'Aziz',
            Time_Hours: 20.5,
            Total_MD: 2.56
          },
          {
            Author: 'Sami',
            Time_Hours: 24,
            Total_MD: 3
          }
        ],
        author_work_summary: [
          {
            Author: 'Aziz',
            Role: 'FE',
            Total_Hours: 20.5,
            Total_MD: 2.56,
            Tickets_Count: 5,
            Worked_On: [
              'Build customer information form',
              'Integrate customer validation API'
            ]
          },
          {
            Author: 'Sami',
            Role: 'BE',
            Total_Hours: 24,
            Total_MD: 3,
            Tickets_Count: 4,
            Worked_On: [
              'Create customer validation endpoint',
              'Add validation rules'
            ]
          }
        ]
      })
    )
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        AuthorSummaryComponent
      ],
      providers: [
        {
          provide: ApiService,
          useValue: apiServiceMock
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AuthorSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create author summary component', () => {
    expect(component).toBeTruthy();
  });

  it('should calculate totals from author data', () => {
    component.byAuthor = [
      {
        Author: 'Aziz',
        Time_Hours: 20
      },
      {
        Author: 'Sami',
        Time_Hours: 24
      }
    ];

    component.authorWorkSummary = [
      {
        Author: 'Aziz',
        Tickets_Count: 5
      },
      {
        Author: 'Sami',
        Tickets_Count: 4
      }
    ];

    component.calculateTotals();

    expect(component.totalHours).toBe(44);
    expect(component.totalMd).toBe(5.5);
    expect(component.totalAuthors).toBe(2);
    expect(component.totalTickets).toBe(9);
  });
});
