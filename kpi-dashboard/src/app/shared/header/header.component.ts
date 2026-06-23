import {
  Component,
  OnInit,
  Inject,
  PLATFORM_ID
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import {
  NgbDropdown,
  NgbDropdownItem,
  NgbDropdownMenu,
  NgbDropdownToggle
} from '@ng-bootstrap/ng-bootstrap';

import { AuthService } from '../../auth.service';
import { TimesheetsApiService } from '../../services/timesheets-api.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive,
    NgbDropdown,
    NgbDropdownToggle,
    NgbDropdownMenu,
    NgbDropdownItem
  ],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent implements OnInit {
  isBrowser = false;
  isAuthenticated = false;
  isAdmin = false;
  userName = 'User';
  userRoles: string[] = [];

  ollamaAvailable = false;
  ollamaStatusLoading = false;

  constructor(
    private authService: AuthService,
    private timesheetsApiService: TimesheetsApiService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
  }

  async ngOnInit(): Promise<void> {
    if (this.isBrowser) {
      await this.initAuth();
      this.checkOllamaStatus();
    }
  }

  async initAuth(): Promise<void> {
    this.isAuthenticated = await this.authService.init();

    if (this.isAuthenticated) {
      this.userName =
        this.authService.getFullName() || this.authService.getUsername();
      this.userRoles = this.authService.getRoles();
      this.isAdmin = this.userRoles.some((role) =>
        ['admin', 'administrator', 'realm-admin'].includes(role.toLowerCase())
      );
    } else {
      this.userName = 'Guest';
      this.userRoles = [];
      this.isAdmin = false;
    }
  }

  login(): void {
    this.authService.login();
  }

  logout(): void {
    this.authService.logout();
  }

  getUserInitials(): string {
    if (!this.userName?.trim() || this.userName === 'User' || this.userName === 'Guest') {
      return 'GU';
    }

    const names = this.userName.trim().split(/\s+/).filter((name) => name.length > 0);

    if (names.length >= 2) {
      return (names[0].charAt(0) + names[1].charAt(0)).toUpperCase();
    }

    if (names[0].length >= 2) {
      return names[0].substring(0, 2).toUpperCase();
    }

    return names[0].charAt(0).toUpperCase();
  }

  getRoleDisplayText(): string {
    if (this.isAdmin) {
      return 'Administrator';
    }

    const role = this.userRoles.find((item) =>
      !['offline_access', 'uma_authorization', 'default-roles-ia-agent'].includes(item)
    );

    return role || 'User';
  }

  checkOllamaStatus(): void {
    this.ollamaStatusLoading = true;

    this.timesheetsApiService.getOllamaStatus().subscribe({
      next: (res: any) => {
        this.ollamaAvailable = !!res?.ollama_available;
        this.ollamaStatusLoading = false;
      },
      error: () => {
        this.ollamaAvailable = false;
        this.ollamaStatusLoading = false;
      },
      complete: () => {
        this.ollamaStatusLoading = false;
      }
    });
  }
}
