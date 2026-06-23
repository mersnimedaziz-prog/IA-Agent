import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { RoleSummaryComponent } from './role-summary.component';
import { ApiService } from '../../api.service';

describe('RoleSummaryComponent', () => {
  let component: RoleSummaryComponent;
  let fixture: ComponentFixture<RoleSummaryComponent>;

  const apiServiceMock = {
    getMonthlyUploads: vi.fn().mockReturnValue(of([{upload_id: 'test_id', original_filename: 'test.xlsx'}])),
    getMonthlyPivotByUpload: vi.fn().mockReturnValue(
      of({
        by_role: [
          {
            Role: 'FE',
            Time_Hours: 20.5,
            Total_MD: 2.56
          },
          {
            Role: 'BE',
            Time_Hours: 24,
            Total_MD: 3
          }
        ],
        role_work_summary: [
          {
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
        RoleSummaryComponent
      ],
      providers: [
        {
          provide: ApiService,
          useValue: apiServiceMock
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RoleSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create role summary component', () => {
    expect(component).toBeTruthy();
  });

  it('should calculate totals from role data', () => {
    component.byRole = [
      {
        Role: 'FE',
        Time_Hours: 20
      },
      {
        Role: 'BE',
        Time_Hours: 24
      }
    ];

    component.roleWorkSummary = [
      {
        Role: 'FE',
        Tickets_Count: 5
      },
      {
        Role: 'BE',
        Tickets_Count: 4
      }
    ];

    component.calculateTotals();

    expect(component.totalHours).toBe(44);
    expect(component.totalMd).toBe(5.5);
    expect(component.totalRoles).toBe(2);
    expect(component.totalTickets).toBe(9);
  });
});