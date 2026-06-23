import { TestBed } from '@angular/core/testing';
import { PLATFORM_ID } from '@angular/core';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        {
          provide: PLATFORM_ID,
          useValue: 'browser'
        }
      ]
    });

    service = TestBed.inject(AuthService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});