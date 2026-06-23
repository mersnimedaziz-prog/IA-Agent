import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SummaryDashboardComponent } from './summary-dashboard.component';

describe('SummaryDashboardComponent', () => {
  let component: SummaryDashboardComponent;
  let fixture: ComponentFixture<SummaryDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SummaryDashboardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SummaryDashboardComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
