import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { HomeComponent } from './home.component';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { AuthService } from '../../auth.service';

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;

  const dashboardApiServiceMock = {
    getMonthlyResults: vi.fn().mockReturnValue(of([]))
  };

  const authServiceMock = {
    init: vi.fn().mockReturnValue(Promise.resolve(false)),
    login: vi.fn(),
    logout: vi.fn(),
    getUsername: vi.fn().mockReturnValue('test-user'),
    getFullName: vi.fn().mockReturnValue('Test User'),
    getRoles: vi.fn().mockReturnValue([])
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomeComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: DashboardApiService, useValue: dashboardApiServiceMock },
        { provide: AuthService, useValue: authServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create home component', () => {
    expect(component).toBeTruthy();
  });
});
