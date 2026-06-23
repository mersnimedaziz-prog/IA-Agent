import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PLATFORM_ID } from '@angular/core';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { HeaderComponent } from './header.component';
import { AuthService } from '../../auth.service';
import { DashboardApiService } from '../../services/dashboard-api.service';

describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;

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
        HeaderComponent,
        RouterTestingModule,
        NgbDropdownModule
      ],
      providers: [
        {
          provide: AuthService,
          useValue: authServiceMock
        },
        {
          provide: DashboardApiService,
          useValue: DashboardApiServiceMock
        },
        {
          provide: PLATFORM_ID,
          useValue: 'browser'
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create header component', () => {
    expect(component).toBeTruthy();
  });
});

