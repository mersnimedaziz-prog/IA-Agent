import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { RouterTestingModule } from '@angular/router/testing';
import { PLATFORM_ID } from '@angular/core';
import { vi } from 'vitest';
import { of } from 'rxjs';

import { AuthService } from './auth.service';
import { DashboardApiService } from './services/dashboard-api.service';

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;
  let component: AppComponent;

  const authServiceMock = {
    init: vi.fn().mockReturnValue(Promise.resolve(false)),
    login: vi.fn(),
    logout: vi.fn(),
    getUsername: vi.fn().mockReturnValue('test-user'),
    getFullName: vi.fn().mockReturnValue('Test User'),
    getRoles: vi.fn().mockReturnValue([])
  };

  const DashboardApiServiceMock = {
    getOllamaStatus: vi.fn().mockReturnValue(
      of({
        ollama_available: false
      })
    )
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        AppComponent,
        RouterTestingModule
      ],
      providers: [
        { provide: AuthService, useValue: authServiceMock },
        { provide: DashboardApiService, useValue: DashboardApiServiceMock },
        { provide: PLATFORM_ID, useValue: 'browser' }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app', () => {
    expect(component).toBeTruthy();
  });
});


